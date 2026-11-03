"""Ingest every replay and rebuild the learned-pattern knowledge.

Usage:  python tools/ingest.py [extra_replay_dir ...]
Reads  .ydr files from the game's Common folder (+ any extra dirs),
writes  data/replays/<name>.txt        readable story
        data/dataset/replays.jsonl     one structured summary per replay
        knowledge/07_learned_patterns.md  aggregate statistics (regenerated each run)
Drop new replays into the Common folder (or an extra dir) and run it again.
"""
import collections, glob, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_decode import analyse, load_cards, parse
from patterns import write_patterns

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMMON = os.path.expandvars(r"%APPDATA%\Yu-Gi-Oh! Power of Chaos Common")


def read_deck(path):
    d = open(path, "rb").read(); p = 8; out = []
    while p + 2 <= len(d):
        n = struct.unpack_from("<H", d, p)[0]; p += 2
        out.append(list(struct.unpack_from("<%dH" % n, d, p))); p += 2 * n
    return out


def name_deck(main, known):
    """Return the saved deck name whose main list overlaps most with `main`."""
    best, score = None, 0.0
    ms = collections.Counter(main)
    for nm, cnt in known.items():
        inter = sum((ms & cnt).values()); uni = sum((ms | cnt).values())
        j = inter / uni if uni else 0
        if j > score:
            best, score = nm, j
    return (best, round(score, 2)) if score >= 0.5 else (None, round(score, 2))


def readable_story(lines, user_side):
    """Text of a story. When the user's side is known, relabel so that 'YOU' is always the user."""
    text = "\n".join(lines) + "\n"
    if user_side == "OPP":
        text = text.replace("YOU", "\0").replace("OPP", "YOU").replace("\0", "OPP")
        return "[labels swapped: YOU = the user (the first deck list in this file)]\n" + text
    if user_side == "YOU":
        return "[YOU = the user (the second deck list in this file)]\n" + text
    return text


def main():
    cards = load_cards()
    nm = lambda c: cards[c]["name"] if c in cards else f"#{c}"
    known = {}
    for f in glob.glob(os.path.join(COMMON, "*.ydc")):
        known[os.path.basename(f)] = collections.Counter(read_deck(f)[0])
    # sources: the game's Common folder, the project's replay folders, plus any folders given on the command line
    sides_file = os.path.join(ROOT, 'data', 'user_sides.json')
    user_sides = json.load(open(sides_file)) if os.path.exists(sides_file) else {}
    dirs = [COMMON] + [os.path.join(ROOT, d) for d in ("My Hand", "My opp's Hand", "learned_replays")] + sys.argv[1:]
    dirs = [d for d in dirs if os.path.isdir(d)]
    os.makedirs(os.path.join(ROOT, "data", "dataset"), exist_ok=True)
    rows, seen, dups, skipped = [], {}, 0, []
    for d in dirs:
        tag = "common" if d == COMMON else os.path.basename(d.rstrip("\\/")).replace(" ", "_").replace("'", "")
        outdir = os.path.join(ROOT, "data", "replays", tag)
        os.makedirs(outdir, exist_ok=True)
        for f in sorted(glob.glob(os.path.join(d, "*.ydr"))):
            base = os.path.splitext(os.path.basename(f))[0]
            try:
                a = analyse(f, cards)
            except Exception as e:
                skipped.append(base); continue
            key = (a["seed"], a["turns"], len(a["events"]), a["lp"]["YOU"], a["lp"]["OPP"])
            if key in seen:                       # same game saved under another name / folder
                dups += 1; continue
            seen[key] = base
            safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in base)
            open(os.path.join(outdir, safe + ".txt"), "w", encoding="utf8").write(readable_story(a["story"], user_sides.get(base)))
            you_main, opp_main = a["decks"][1][0], a["decks"][0][0]
            you_deck = name_deck(you_main, known)
            ws = a["winner"]
            wd = a["decks"][1] if ws == "YOU" else a["decks"][0]
            ld = a["decks"][0] if ws == "YOU" else a["decks"][1]
            rows.append(dict(
                name=base, source=tag, user_side=user_sides.get(base), version=a["version"], how=a["how"], win_side=ws, winner=ws, first=a["first"],
                turns=a["turns"], lp=a["lp"], you_deck=you_deck[0], you_deck_match=you_deck[1],
                win_main=[nm(c) for c in wd[0]], win_fusion=[nm(c) for c in wd[1]], win_sidedeck=[nm(c) for c in wd[2]],
                lose_main=[nm(c) for c in ld[0]], lose_fusion=[nm(c) for c in ld[1]],
                you_main=[nm(c) for c in you_main], opp_main=[nm(c) for c in opp_main],
                events=[{k: (nm(v) if k in ("card", "attacker", "target") and isinstance(v, int) else v) for k, v in e.items()}
                        for e in a["events"]]))
    with open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), "w", encoding="utf8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_patterns(rows, ROOT)
    print(f"ingested {len(rows)} unique replays ({dups} duplicates skipped, {len(skipped)} unreadable: {skipped})")


if __name__ == "__main__":
    main()

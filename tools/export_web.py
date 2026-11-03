"""Export card data and replays as JSON for the web game project (C:\\Users\\ahmed\\OneDrive\\Desktop\\joey_web_game).

  python tools/export_web.py REPLAY.ydr [REPLAY2.ydr ...]     writes data/replays/<name>.json (one frame per replay event)
  python tools/export_web.py --cards                          writes data/cards.json (the 771 playable cards)
"""
import csv, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import replay_decode as rd
from hands import initial_libraries

WEB = os.path.abspath(os.path.join(HERE, "..", "..", "joey_web_game"))
OPNAME = {0x01: "turn", 0x04: "end", 0x05: "surrender", 0x61: "draw", 0xCE: "summon", 0xCF: "spelltrap", 0x72: "effect",
          0x33: "attack", 0x34: "direct", 0x3C: "destroyed", 0x7C: "to_graveyard", 0x43: "lp_loss", 0x42: "lp_gain", 0x70: "special_summon"}


def fusion_names():
    """Monsters that the replays keep in a Fusion Deck (the card table itself has no flag for it)."""
    names = set()
    for line in open(os.path.join(HERE, "..", "data", "dataset", "replays.jsonl"), encoding="utf8"):
        d = json.loads(line)
        for k in ("win_fusion", "lose_fusion"):
            names.update(d.get(k) or [])
    return names


def cards():
    fus = fusion_names()
    out = []
    for r in csv.DictReader(open(os.path.join(HERE, "..", "data", "cards_game.csv"), encoding="utf8")):
        out.append(dict(id=int(r["deck_id"]), name=r["name"], level=r["level"], attribute=r["attribute"], type=r["type"],
                        atk=r["atk"], def_=r["def"], text=r["description"], fusion=r["name"] in fus))
    os.makedirs(os.path.join(WEB, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(WEB, "data", "cards.json"), "w"), ensure_ascii=False)
    print(len(out), "cards written")


def export(path):
    allc = rd.load_cards()
    seed, decks, rec = rd.parse(path)
    raw = open(path, "rb").read()
    first_side = next((rd.SIDE[bool(a & 0x8000)] for a, b in rec if (a & 0x7FFF) == 0x01), None)
    libs = initial_libraries([decks[0], decks[1]], seed, 1 if first_side == "YOU" else 0) if first_side else None
    d = rd.Duel(allc, decks, libs, "YOU" if struct.unpack_from("<I", raw, 16)[0] == 1 else "OPP")
    frames = []
    for a, b in rec:
        n0 = len(d.out)
        d.step(a, b)
        op = a & 0x7FFF
        frames.append(dict(
            op=OPNAME.get(op, hex(op)), side=rd.SIDE[bool(a & 0x8000)], text=[s.strip() for s in d.out[n0:] if s.strip()],
            lp=[d.lp["YOU"], d.lp["OPP"]], turn=d.turn, hand=[d.hand["YOU"], d.hand["OPP"]],
            field={s: [None if c is None else [c, d.facedown[s][i]] for i, c in enumerate(d.field[s])] for s in ("YOU", "OPP")},
            hand_cards={s: d.hand_list(s) if d.libs and d.lib_exact[s] else None for s in ("YOU", "OPP")}))
    name = os.path.splitext(os.path.basename(path))[0]
    doc = dict(name=name, seed=seed, first=first_side, decks=dict(OPP=decks[0], YOU=decks[1]), frames=frames)
    os.makedirs(os.path.join(WEB, "data", "replays"), exist_ok=True)
    json.dump(doc, open(os.path.join(WEB, "data", "replays", name + ".json"), "w"), ensure_ascii=False)
    print(name, len(frames), "frames")


def export_compact(path, outdir):
    """Raw operations plus a board snapshot after each one, for the effect-verification harness (tests/verify_effects.mjs)."""
    allc = rd.load_cards()
    seed, decks, rec = rd.parse(path)
    raw = open(path, "rb").read()
    first_side = next((rd.SIDE[bool(a & 0x8000)] for a, b in rec if (a & 0x7FFF) == 0x01), None)
    libs = initial_libraries([decks[0], decks[1]], seed, 1 if first_side == "YOU" else 0) if first_side else None
    d = rd.Duel(allc, decks, libs, "YOU" if struct.unpack_from("<I", raw, 16)[0] == 1 else "OPP")
    frames = []
    for a, b in rec:
        d.step(a, b)
        fld = lambda s: [None if c is None else (c if not d.facedown[s][i] else -c) for i, c in enumerate(d.field[s])]
        frames.append([a & 0x7FFF, 1 if a & 0x8000 else 0, a >> 16, b, d.lp["YOU"], d.lp["OPP"], d.turn, fld("YOU"), fld("OPP")])
    name = os.path.basename(os.path.dirname(path)).replace(" ", "_") + "__" + os.path.splitext(os.path.basename(path))[0]
    os.makedirs(outdir, exist_ok=True)
    json.dump(dict(name=name, first=first_side, frames=frames), open(os.path.join(outdir, name + ".json"), "w"))
    return len(frames)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--verify-dir" in args:
        import glob
        root = os.path.join(HERE, "..")
        files = glob.glob(os.path.join(root, "My Hand", "*.ydr")) + glob.glob(os.path.join(root, "My opp's Hand", "*.ydr")) + glob.glob(os.path.expandvars(r"%APPDATA%\Yu-Gi-Oh! Power of Chaos Common\*.ydr"))
        n = 0
        for f in files:
            try:
                export_compact(f, os.path.join(WEB, "data", "verify")); n += 1
            except Exception as e:
                print("skip", f, e)
        print(n, "replays written to data/verify")
        sys.exit()
    if "--cards" in args:
        cards()
    for p in [a for a in args if not a.startswith("--")]:
        export(p)

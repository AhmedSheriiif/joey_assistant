"""Export the champion decks (>=5 games, >=85% wins) as .ydc files you can copy into the game's Common folder,
plus a readable markdown gallery (knowledge/10_champion_decks.md)."""
import collections, glob, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_decode import parse, load_cards

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HEADER = bytes.fromhex("01f312005754cb3f")          # same header as the .ydc files in your Common folder
cards = load_cards(); nm = lambda c: cards[c]["name"] if c in cards else f"#{c}"
fp = lambda ids: tuple(sorted(collections.Counter(ids).items()))

files = []
for d in ("My Hand", "My opp's Hand"):
    files += sorted(glob.glob(os.path.join(ROOT, d, "*.ydr")))
files += sorted(glob.glob(os.path.expandvars(r"%APPDATA%\Yu-Gi-Oh! Power of Chaos Common\*.ydr")))
rec = collections.defaultdict(lambda: [0, 0]); full = {}; seen = set(); n_games = 0
for f in files:
    try:
        seed, decks, ev = parse(f)
    except Exception:
        continue
    # winner from the analysed dataset is not available here, so re-derive using the dataset by (seed, #events)
    key = (seed, len(ev))
    if key in seen:
        continue
    seen.add(key); n_games += 1
    rows_key = key
    full.setdefault(rows_key, decks)

ds = {}
for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8"):
    r = json.loads(l)
    ds[(r["name"])] = r
# map dataset games back to full deck triples by name
by_name = {}
for f in files:
    base = os.path.splitext(os.path.basename(f))[0]
    try:
        seed, decks, ev = parse(f)
    except Exception:
        continue
    by_name[base] = decks
fpn = lambda names: tuple(sorted(collections.Counter(names).items()))
rec = collections.defaultdict(lambda: [0, 0]); example = {}
for name, r in ds.items():
    w, l = fpn(r["win_main"]), fpn(r["lose_main"])
    rec[w][0] += 1; rec[w][1] += 1; rec[l][1] += 1
    if name in by_name:
        decks = by_name[name]
        d = decks[1] if r["winner"] == "YOU" else decks[0]
        example.setdefault(w, d)
champ = sorted([k for k, v in rec.items() if v[1] >= 5 and v[0] / v[1] >= 0.85], key=lambda k: -rec[k][1])
os.makedirs(os.path.join(ROOT, "champion_decks"), exist_ok=True)
md = ["# Champion decks (tournament replays)\n",
      "Decks that won at least 85% of 5+ games. Deck strength and pilot skill cannot be separated in this data, so treat these as proven shells, not guaranteed results.",
      "The `.ydc` files are in `champion_decks/`: copy them into `%APPDATA%\\Yu-Gi-Oh! Power of Chaos Common` to use them in the game.\n"]
for i, k in enumerate(champ, 1):
    w, g = rec[k]
    lists = example.get(k)
    label = f"Champ{i:02d}_{w}-{g}"
    if lists:
        data = HEADER
        for l_ in lists:
            data += struct.pack("<H", len(l_)) + struct.pack("<%dH" % len(l_), *l_)
        open(os.path.join(ROOT, "champion_decks", label + ".ydc"), "wb").write(data)
    md.append(f"\n## {label}  ({w} wins in {g} games, {sum(n for _, n in k)} cards)")
    md.append(", ".join(f"{n}x {c}" if n > 1 else c for c, n in sorted(k, key=lambda x: (-x[1], x[0]))))
    if lists:
        md.append("Fusion: " + ", ".join(f"{n}x {nm(c)}" if n > 1 else nm(c) for c, n in sorted(collections.Counter(lists[1]).items(), key=lambda x: -x[1])))
        md.append("Side: " + ", ".join(f"{n}x {nm(c)}" if n > 1 else nm(c) for c, n in sorted(collections.Counter(lists[2]).items(), key=lambda x: -x[1])))
open(os.path.join(ROOT, "knowledge", "10_champion_decks.md"), "w", encoding="utf8").write("\n".join(md) + "\n")
print(len(champ), "champion decks exported")

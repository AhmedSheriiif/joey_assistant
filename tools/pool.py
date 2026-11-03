"""Mark which cards are really playable in Joey the Passion and write data/cards_game.csv.

card_pack.bin (u16 per card index) low byte is a bit mask: 1 = Yugi the Destiny, 2 = Kaiba the Revenge, 4 = Joey the Passion.
Entries with low byte 0 are not in any game (card back, unused/unreleased entries). Result: exactly 771 playable cards.
Run from the tools folder:  python pool.py
"""
import csv, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
import lz
b, u = lz.raw("bin#" + chr(92) + "card_pack.bin")
pk = lz.lzss(b, u, 4078, 32, 0) if len(b) != u else b
vals = [struct.unpack_from("<H", pk, i * 2)[0] & 0xFF for i in range(1115)]
list_txt = open(os.path.join(HERE, "..", "data", "list_card.txt"), "rb").read().decode("latin1") if os.path.exists(os.path.join(HERE, "..", "data", "list_card.txt")) else None
# card index -> deck id (from the game's list_card.txt; decode it again so the script is self-contained)
lb, lu = lz.raw("card" + chr(92) + "list_card.txt")
txt = lz.lzss(lb, lu, 4078, 32, 0).decode("latin1")
idx2deck = {int(i): int(c) for _, i, c in re.findall(r"//\t(.*?)\r?\n//\t(\d+):\[(\d+)\]", txt)}
mask = {idx2deck[i]: vals[i] for i in range(1115) if i in idx2deck}
src = os.path.join(HERE, "..", "data", "cards_all.csv")
rows = list(csv.DictReader(open(src, encoding="utf8")))
cols = list(rows[0].keys())
for r in rows:
    m = mask.get(int(r["deck_id"]), 0)
    r["yugi"], r["kaiba"], r["joey"] = int(bool(m & 1)), int(bool(m & 2)), int(bool(m & 4))
    r["playable"] = int(m & 7 != 0)
extra = ["yugi", "kaiba", "joey", "playable"]
for path, sel in ((src, rows), (os.path.join(HERE, "..", "data", "cards_game.csv"), [r for r in rows if r["playable"]])):
    with open(path, "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=[c for c in cols if c not in extra] + extra); w.writeheader(); w.writerows(sel)
play = [r for r in rows if r["playable"]]
print(len(rows), "entries,", len(play), "playable;", sum(int(r["yugi"]) for r in rows), "Yugi,", sum(int(r["kaiba"]) for r in rows), "Kaiba,", sum(int(r["joey"]) for r in rows), "Joey")

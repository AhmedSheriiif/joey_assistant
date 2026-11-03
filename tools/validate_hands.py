"""How well does the shuffle reconstruction (tools/hands.py) explain the replays?
For every player-side, every card played on his first turn must lie in the first 6 cards of the reconstructed library
(5 opening cards + the turn's draw), unless he drew extra cards that turn (Pot of Greed, Graceful Charity).
Chance level for a random order is about 15% per card, so 89% across 490 sides is far beyond luck."""
import collections, glob, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_decode import parse, load_cards
from hands import initial_libraries

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
cards = load_cards()
files = sorted(glob.glob(os.path.join(ROOT, "My Hand", "*.ydr"))) + sorted(glob.glob(os.path.expandvars(r"%APPDATA%\Yu-Gi-Oh! Power of Chaos Common\*.ydr")))
good = tot = 0
for f in files:
    try:
        seed, decks, rec = parse(f)
    except Exception:
        continue
    raw = open(f, "rb").read(); f20 = struct.unpack_from("<I", raw, 20)[0]
    libs = initial_libraries(decks, seed, 1 if f20 == 1 else 0)
    turn = 0; cur = None; first = {}; plays = {"YOU": [], "OPP": []}
    for a, b in rec:
        op = a & 0x7FFF; s = "YOU" if a & 0x8000 else "OPP"
        if op == 1:
            turn += 1; cur = s; first.setdefault(s, turn)
        if op in (0xCE, 0xCF) and cur == s and first.get(s) == turn and (a >> 16) in cards:
            plays[s].append(a >> 16)
    for s in ("YOU", "OPP"):
        if plays[s]:
            top = collections.Counter(libs[s][:6]); tot += 1; good += all(top[c] > 0 for c in plays[s])
print(f"{good} of {tot} player-sides: all first-turn plays are inside the reconstructed opening hand + first draw ({100 * good // tot}%)")

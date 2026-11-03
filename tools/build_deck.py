"""Build, check and export the recommended deck.

Rules checked: banned cards (Delinquent Duo, The Forceful Sentry, Confiscation), copy limits seen in the tournament replays,
deck size 40-44. Outputs champion_decks/Best_Deck.ydc (load it in the game) and prints opening-hand statistics from 20,000 simulated shuffles.
"""
import collections, csv, glob, json, os, random, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_decode import parse, load_cards

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BANNED = {"Delinquent Duo", "The Forceful Sentry", "Confiscation"}

MAIN = {
    # monsters (19)
    "Mystic Tomato": 3, "Nimble Momonga": 3, "Penguin Soldier": 2, "Man-Eater Bug": 2, "Cannon Soldier": 1, "Crass Clown": 1,
    "Sangan": 1, "Witch of the Black Forest": 1, "Jinzo": 1, "Amazon Archer": 1, "Kuriboh": 1, "Morphing Jar": 1, "Magician of Faith": 1,
    # spells and traps (21)
    "Scapegoat": 3, "Mystical Space Typhoon": 2, "Giant Trunade": 1, "Graceful Charity": 1, "Pot of Greed": 1, "Monster Reborn": 1,
    "Premature Burial": 1, "Call Of The Haunted": 1, "United We Stand": 1, "Snatch Steal": 1, "Change of Heart": 1, "Dark Hole": 1,
    "Raigeki": 1, "Heavy Storm": 1, "Torrential Tribute": 1, "Mirror Force": 1, "Magic Cylinder": 1, "Swords of Revealing Light": 1,
}
FUSION = ["Blue-Eyes Ultimate Dragon", "St. Joan", "The Last Warrior from Another Planet", "Alligator's Sword Dragon", "Thousand-Eyes Restrict"]
SIDE = {"Waboku": 1, "Imperial Order": 1, "Mirror Wall": 1, "Nobleman of Crossout": 2, "Dust Tornado": 2, "Ceasefire": 1, "Ring of Destruction": 1,
        "Rush Recklessly": 2, "Crush Card": 1, "Kunai with Chain": 1, "Wall of Illusion": 1, "Fissure": 1}

cards = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cards_game.csv"), encoding="utf8"))}

# observed maximum copies per card in the tournament decks
rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
maxc = collections.Counter()
for r in rows:
    for d in (r["you_main"], r["opp_main"]):
        for c, n in collections.Counter(d).items():
            maxc[c] = max(maxc[c], n)

problems = []
n_main = sum(MAIN.values())
for c, n in {**MAIN, **SIDE}.items():
    if c not in cards: problems.append(f"unknown card {c}")
    if c in BANNED: problems.append(f"banned card {c}")
    if n > 3: problems.append(f"{c} x{n} exceeds 3")
    if maxc[c] and n > maxc[c]: problems.append(f"{c} x{n} is more than ever seen in the replays (max {maxc[c]})")
if not 40 <= n_main <= 44: problems.append(f"main deck has {n_main} cards")
if sum(SIDE.values()) > 15: problems.append("side deck larger than 15")
mons = sum(n for c, n in MAIN.items() if cards[c]["level"])
print(f"main {n_main} cards ({mons} monsters, {n_main - mons} spells/traps), side {sum(SIDE.values())}, fusion {len(FUSION)}")
print("rule check:", "OK" if not problems else problems)

# ---- score with the deck model (sum of logistic coefficients) against the champion decks and the user's deck
dm = json.load(open(os.path.join(ROOT, "data", "models", "deck_model.json")))["cards"]
score = lambda deck: sum(dm.get(c, {}).get("coef", 0) for c in set(deck))
fp = lambda d: tuple(sorted(collections.Counter(d).items()))
rec = collections.defaultdict(lambda: [0, 0])
for r in rows:
    rec[fp(r["win_main"])][0] += 1; rec[fp(r["win_main"])][1] += 1; rec[fp(r["lose_main"])][1] += 1
champs = sorted([(v[0], v[1], k) for k, v in rec.items() if v[1] >= 5 and v[0] / v[1] >= 0.85], reverse=True)
print("deck-model score (sum of card coefficients; higher = more like winning decks):")
print(f"   this deck: {score(MAIN):+.2f}")
for w, g, k in champs[:5]:
    print(f"   champion {w}-{g}: {score([c for c, _ in k]):+.2f}")

# ---- opening-hand statistics
random.seed(1)
deck = [c for c, n in MAIN.items() for _ in range(n)]
REM = {"Mystical Space Typhoon", "Giant Trunade", "Dark Hole", "Raigeki", "Heavy Storm", "Change of Heart", "Snatch Steal", "Man-Eater Bug", "Penguin Soldier", "Crass Clown"}
BURN = {"Cannon Soldier", "Amazon Archer"}
ENGINE = {"Pot of Greed", "Graceful Charity", "Morphing Jar"}
REVIVE = {"Monster Reborn", "Premature Burial", "Call Of The Haunted"}
cnt = collections.Counter(); N = 20000
for _ in range(N):
    h = random.sample(deck, 6)
    lowm = sum(1 for c in h if cards[c]["level"] and int(cards[c]["level"]) <= 4)
    cnt["no low monster"] += lowm == 0
    cnt["2+ low monsters"] += lowm >= 2
    cnt["a removal/steal card"] += any(c in REM for c in h)
    cnt["a draw engine card"] += any(c in ENGINE for c in h)
    cnt["a burn finisher"] += any(c in BURN for c in h)
    cnt["a revive card"] += any(c in REVIVE for c in h)
    cnt["a defensive trap or Scapegoat"] += any(c in {"Mirror Force", "Magic Cylinder", "Torrential Tribute", "Scapegoat", "Swords of Revealing Light"} for c in h)
    cnt["unplayable-looking (no low monster and no spell)"] += lowm == 0 and all(cards[c]["level"] for c in h)
print(f"opening 6 cards ({N} simulated hands):")
for k, v in cnt.items():
    print(f"   {k:48} {100 * v / N:5.1f}%")

# ---- export .ydc using the ids the replays use
idmap = collections.defaultdict(collections.Counter)
for f in glob.glob(os.path.join(ROOT, "My Hand", "*.ydr"))[:200] + glob.glob(os.path.expandvars(r"%APPDATA%\Yu-Gi-Oh! Power of Chaos Common\*.ydr")):
    try:
        seed, decks, rec_ = parse(f)
    except Exception:
        continue
    nm = load_cards()
    for p in decks:
        for l in p:
            for i in l:
                if i in nm: idmap[nm[i]["name"]][i] += 1
def cid(name):
    if idmap[name]: return idmap[name].most_common(1)[0][0]
    return int(cards[name]["deck_id"])
def to_ids(spec): return [cid(c) for c, n in spec.items() for _ in range(n)]
def to_ids_list(lst): return [cid(c) for c in lst]
lists = [to_ids(MAIN), to_ids_list(FUSION), to_ids(SIDE)]
data = bytes.fromhex("01f312005754cb3f")
for l in lists: data += struct.pack("<H", len(l)) + struct.pack("<%dH" % len(l), *l)
out = os.path.join(ROOT, "champion_decks", "Best_Deck.ydc"); open(out, "wb").write(data)
print("written", out)

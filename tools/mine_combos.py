"""Mine real combos: which cards are played together in the same turn, and which turns deal huge damage.

Prints a report. A 'turn' is one player's turn. Damage = LP the opponent loses during that turn (self-inflicted costs excluded).
"""
import collections, itertools, json, os, statistics

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
rows = [r for r in rows if r["winner"] in ("YOU", "OPP")]

turns = []
for gi, r in enumerate(rows):
    ev = r["events"]
    idx = [i for i, e in enumerate(ev) if e["kind"] == "turn"]
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else len(ev)
        me = ev[i]["side"]; op = "OPP" if me == "YOU" else "YOU"
        seg = ev[i + 1:j]
        cards = collections.Counter()
        order = []
        for e in seg:
            if e["side"] == me and e.get("card") and e["kind"] in ("summon", "set_monster", "set_st", "activate", "effect"):
                cards[e["card"]] += 1
                if e["kind"] in ("summon", "set_monster", "activate", "effect"):
                    order.append(e["card"])
        dmg = sum(e["amount"] for e in seg if e["kind"] == "lp_loss" and e["side"] == op and not e.get("cost"))
        lp_op = ev[i]["lp_opp"] if me == "YOU" else ev[i]["lp_you"]
        turns.append(dict(game=gi, name=r["name"], turn=ev[i]["turn"], me=me, won=r["winner"] == me, dmg=dmg, cards=cards, order=order,
                          direct=sum(e["kind"] == "direct" for e in seg if e["side"] == me), lp_op=lp_op,
                          last=(k >= len(idx) - 2 and r["winner"] == me)))
print(f"{len(turns)} turns from {len(rows)} games")
ds = sorted(t["dmg"] for t in turns)
print("damage per turn: median %d, 90th pct %d, 99th pct %d, max %d" % (ds[len(ds)//2], ds[int(len(ds)*0.9)], ds[int(len(ds)*0.99)], ds[-1]))
big = [t for t in turns if t["dmg"] >= 3000]
otk = [t for t in turns if t["dmg"] >= 5000]
print(f"turns dealing >=3000: {len(big)}; >=5000: {len(otk)}; one-turn kills from >=7000 LP: {sum(1 for t in turns if t['last'] and t['lp_op'] >= 7000)}")
fin = [t for t in turns if t["last"]]
print("final-turn damage: median %d, share of wins with a final turn >=3000: %.0f%%" % (statistics.median(t["dmg"] for t in fin), 100 * sum(t["dmg"] >= 3000 for t in fin) / len(fin)))

# single cards and pairs: how often do they appear in big-damage turns vs all turns
allc = collections.Counter(); bigc = collections.Counter()
allp = collections.Counter(); bigp = collections.Counter()
for t in turns:
    s = set(t["cards"])
    for c in s: allc[c] += 1
    for p in itertools.combinations(sorted(s), 2): allp[p] += 1
for t in big:
    s = set(t["cards"])
    for c in s: bigc[c] += 1
    for p in itertools.combinations(sorted(s), 2): bigp[p] += 1
base = len(big) / len(turns)
print("\nCards over-represented in turns that deal >=3000 (lift = share of big turns / share of all turns):")
rows_ = [(bigc[c] / allc[c] / base, c, bigc[c], allc[c]) for c in allc if allc[c] >= 25 and bigc[c] >= 8]
for lift, c, b, a in sorted(rows_, reverse=True)[:22]:
    print(f"  {c:28} lift {lift:4.1f}  ({b} of {a} turns using it dealt >=3000)")
print("\nPairs used together in the same turn (>=6 big turns, ranked by lift):")
rows_ = [(bigp[p] / allp[p] / base, p, bigp[p], allp[p]) for p in allp if allp[p] >= 12 and bigp[p] >= 6]
for lift, p, b, a in sorted(rows_, reverse=True)[:25]:
    print(f"  {p[0]} + {p[1]:26} lift {lift:4.1f}  ({b} of {a} turns)")

# what precedes a huge turn: removal / control cards in the same turn
REMOVE = {"Mystical Space Typhoon", "Dust Tornado", "Heavy Storm", "Dark Hole", "Raigeki", "Harpie's Feather Duster", "Giant Trunade", "Change of Heart", "Snatch Steal", "Nobleman of Crossout", "Man-Eater Bug", "Penguin Soldier", "Crass Clown"}
BOOST = {"United We Stand", "Mage Power", "Rush Recklessly", "Graceful Dice", "Kunai with Chain", "Metalmorph", "Sword of Dragon's Soul", "Black Pendant"}
BURN = {"Cannon Soldier", "Amazon Archer", "Ceasefire", "Magic Cylinder", "Ring of Destruction", "Giant Germ"}
def tags(t):
    s = set(t["cards"])
    return (bool(s & REMOVE), bool(s & BOOST), bool(s & BURN), t["direct"] >= 1)
sh = collections.Counter(tags(t) for t in big); sa = collections.Counter(tags(t) for t in turns)
print("\nShape of a >=3000 turn (removal, boost, burn, direct hit): count (share of big turns)")
for k, v in sh.most_common(8):
    print(f"  removal={k[0]!s:5} boost={k[1]!s:5} burn={k[2]!s:5} direct={k[3]!s:5}: {v} ({100*v//len(big)}%) vs {100*sa[k]//len(turns)}% of all turns")

print("\nBiggest turns (cards used in order):")
for t in sorted(turns, key=lambda t: -t["dmg"])[:14]:
    seq = []
    for c in t["order"]:
        if not seq or seq[-1] != c: seq.append(c)
    print(f"  {t['dmg']:5} dmg  {t['name'][:22]:22} T{t['turn']:<3} {t['me']}: " + ", ".join(seq[:12]))

# multi-step sequence: removal then direct swing in the same turn, winners vs losers
print("\nWinner turns: removal/steal + direct attack in the same turn: %d of %d winner turns with a direct attack" % (
    sum(1 for t in turns if t["won"] and t["direct"] and (set(t["cards"]) & REMOVE)), sum(1 for t in turns if t["won"] and t["direct"])))

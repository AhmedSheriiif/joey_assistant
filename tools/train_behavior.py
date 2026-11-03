"""Behaviour analysis: what do the best pilots do differently, and what decision rules explain their turns?

Champion pilot = the side playing a deck (fingerprint) that won >=85% of >=5 games in the dataset.
(Deck and player skill are inseparable in this data; "champion" means "deck+pilot that reliably won".)
Prints a report; saves rules to data/models/behavior_rules.txt.
"""
import collections, json, os
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
rows = [r for r in rows if r["winner"] in ("YOU", "OPP")]
fp = lambda d: tuple(sorted(collections.Counter(d).items()))
rec = collections.defaultdict(lambda: [0, 0])
for r in rows:
    w, l = fp(r["win_main"]), fp(r["lose_main"])
    rec[w][0] += 1; rec[w][1] += 1; rec[l][1] += 1
champ = {k for k, v in rec.items() if v[1] >= 5 and v[0] / v[1] >= 0.85}
print(f"{len(champ)} champion decks, covering {sum(rec[k][1] for k in champ)} deck-games")

REMOVAL = {"Mystical Space Typhoon", "Dust Tornado", "Heavy Storm", "Dark Hole", "Raigeki", "Harpie's Feather Duster", "Giant Trunade",
            "Nobleman of Crossout", "Nobleman of Extermination", "Tribute to The Doomed", "Offerings to the Doomed", "Change of Heart", "Snatch Steal"}
BURN = {"Cannon Soldier", "Amazon Archer", "Ceasefire", "Magic Cylinder", "Ring of Destruction"}

turns = []          # one dict per (game, mover turn)
for gi, r in enumerate(rows):
    ev = r["events"]
    deck_of = {"YOU": fp(r["you_main"]), "OPP": fp(r["opp_main"])}
    lp_prev = {}
    tl = [(i, e) for i, e in enumerate(ev) if e["kind"] == "turn"]
    for k, (i, t) in enumerate(tl):
        j = tl[k + 1][0] if k + 1 < len(tl) else len(ev)
        mine = [e for e in ev[i + 1:j] if e["side"] == t["side"]]
        me = t["side"]; op = "OPP" if me == "YOU" else "YOU"
        lp_me, lp_op = (t["lp_you"], t["lp_opp"]) if me == "YOU" else (t["lp_opp"], t["lp_you"])
        mon_me, mon_op = (t["mon_you"], t["mon_opp"]) if me == "YOU" else (t["mon_opp"], t["mon_you"])
        cards = [e.get("card") for e in mine if e.get("card")]
        turns.append(dict(
            game=gi, turn=t["turn"], champ=deck_of[me] in champ, won=r["winner"] == me, first=r["first"] == me,
            lp_me=lp_me, lp_op=lp_op, mon_me=mon_me, mon_op=mon_op, first_turn=(k < 2),
            attacks=sum(e["kind"] == "attack" for e in mine), direct=sum(e["kind"] == "direct" for e in mine),
            sets=sum(e["kind"] == "set_monster" for e in mine), summons=sum(e["kind"] == "summon" for e in mine),
            st=sum(e["kind"] in ("set_st", "activate") for e in mine), eff=sum(e["kind"] == "effect" for e in mine),
            removal=sum(1 for e in mine if e["kind"] in ("activate", "effect") and e.get("card") in REMOVAL),
            burn=sum(1 for e in mine if e["kind"] == "effect" and e.get("card") in BURN),
            lp_lost=sum(e["amount"] for e in mine if e["kind"] == "lp_loss"),
            lp_dealt=sum(e["amount"] for e in ev[i + 1:j] if e["kind"] == "lp_loss" and e["side"] == op and not e.get("cost"))))

def avg(rs, k): return float(np.mean([t[k] for t in rs])) if rs else float("nan")
C = [t for t in turns if t["champ"]]; O = [t for t in turns if not t["champ"]]
print(f"\nPer-turn behaviour (champion pilots n={len(C)} turns vs everyone else n={len(O)}):")
print(f"{'':28}{'champion':>10}{'others':>10}")
for k, lab in (("attacks", "monster attacks"), ("direct", "direct attacks"), ("sets", "monsters set face-down"), ("summons", "monsters summoned face-up"),
               ("st", "spell/trap plays"), ("eff", "effects fired"), ("removal", "removal/steal plays"), ("burn", "burn effects"),
               ("lp_dealt", "LP dealt to opp"), ("lp_lost", "LP lost by self")):
    print(f"{lab:28}{avg(C, k):10.2f}{avg(O, k):10.2f}")
for lab, f in (("when opp has 0 monsters", lambda t: t["mon_op"] == 0), ("when opp has 1+ monsters", lambda t: t["mon_op"] >= 1)):
    c = [t for t in C if f(t) and not t["first_turn"]]; o = [t for t in O if f(t) and not t["first_turn"]]
    print(f"\n{lab}: P(any attack)  champion {np.mean([t['attacks']+t['direct']>0 for t in c]):.0%}  others {np.mean([t['attacks']+t['direct']>0 for t in o]):.0%}   (n={len(c)}/{len(o)})")
    print(f"{'':28}P(direct)      champion {np.mean([t['direct']>0 for t in c]):.0%}  others {np.mean([t['direct']>0 for t in o]):.0%}")
# own LP buckets
print("\nChampions: probability of an attack this turn by own LP / opp LP (turn>=3):")
for lo, hi, lab in ((0, 2000, "opp<=2000"), (2001, 4000, "opp 2001-4000"), (4001, 6500, "opp 4001-6500"), (6501, 99999, "opp>6500")):
    s = [t for t in C if lo <= t["lp_op"] <= hi and t["turn"] >= 3]
    print(f"  {lab:16} attack {np.mean([t['attacks']+t['direct']>0 for t in s]):.0%} direct {np.mean([t['direct']>0 for t in s]):.0%}  burn {np.mean([t['burn']>0 for t in s]):.0%}  (n={len(s)})")
print("\nChampions: first monster face-down rate (first own turn): %.0f%%  others %.0f%%" % (
    100 * np.mean([t["sets"] > 0 for t in C if t["first_turn"] and t["sets"] + t["summons"] > 0]),
    100 * np.mean([t["sets"] > 0 for t in O if t["first_turn"] and t["sets"] + t["summons"] > 0])))

# decision trees on champion turns
FEAT = ["turn", "lp_me", "lp_op", "mon_me", "mon_op"]
out = []
def tree(target, name, depth=3):
    s = [t for t in C if t["turn"] > 2]
    Xs = np.array([[t[f] for f in FEAT] for t in s], float); ys = np.array([target(t) for t in s])
    if ys.min() == ys.max():
        return
    m = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=25, random_state=0).fit(Xs, ys)
    txt = export_text(m, feature_names=FEAT, show_weights=True)
    base = max(ys.mean(), 1 - ys.mean())
    out.append(f"\n### {name}  (champion turns n={len(s)}, base rate {ys.mean():.0%}, tree accuracy {m.score(Xs, ys):.0%}, majority-class {base:.0%})\n{txt}")
tree(lambda t: int(t["attacks"] + t["direct"] > 0), "Will the champion attack this turn?")
tree(lambda t: int(t["direct"] > 0), "Will the champion attack directly this turn?")
tree(lambda t: int(t["removal"] > 0), "Will the champion use removal/steal this turn?")
tree(lambda t: int(t["sets"] > 0), "Will the champion set a monster face-down this turn?")
tree(lambda t: int(t["burn"] > 0), "Will the champion fire a burn effect this turn?")
txt = "\n".join(out)
open(os.path.join(ROOT, "data", "models", "behavior_rules.txt"), "w", encoding="utf8").write(txt)
print(txt)

"""Learn from hands: opening hands, hold-or-play behaviour, and a play-choice model (hand + board -> next action).

Needs the dataset built by ingest.py (events carry the exact hand before each decision when it is known).
Prints a report and saves data/models/policy_model.json (+ policy_meta.json).
"""
import collections, csv, json, os, statistics
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
rows = [r for r in rows if r["winner"] in ("YOU", "OPP")]
cards = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cards_game.csv"), encoding="utf8"))}
fp = lambda d: tuple(sorted(collections.Counter(d).items()))

# groups for leak-free cross-validation (connected components of shared decks)
parent = {}
def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for r in rows:
    parent[find(fp(r["win_main"]))] = find(fp(r["lose_main"]))
comp = {}
group = [comp.setdefault(find(fp(r["win_main"])), len(comp)) for r in rows]

def is_monster(n): return bool(cards.get(n, {}).get("level"))
def lvl(n):
    try: return int(cards[n]["level"])
    except Exception: return 0
def atk(n):
    try: return int(cards[n]["atk"])
    except Exception: return 0

# ------------------------------------------------------------------ A. opening hands
print("=== A. OPENING HANDS ===")
KEY = ["Pot of Greed", "Graceful Charity", "Raigeki", "Heavy Storm", "Dark Hole", "Jinzo", "Cannon Soldier", "Amazon Archer", "Monster Reborn",
       "Premature Burial", "Snatch Steal", "Change of Heart", "Mystical Space Typhoon", "Scapegoat", "United We Stand", "Morphing Jar", "Sangan",
       "Man-Eater Bug", "Giant Trunade", "Swords of Revealing Light", "Torrential Tribute", "Mirror Force", "Magic Cylinder", "Kuriboh", "Waboku"]
op_rows = []
for gi, r in enumerate(rows):
    seen = set()
    for e in r["events"]:
        if e["kind"] == "turn" and e["side"] not in seen:
            seen.add(e["side"])
            pass
    first_turn = {}
    for e in r["events"]:
        if e["kind"] == "turn" and e["side"] not in first_turn:
            first_turn[e["side"]] = e
    for side, e in first_turn.items():
        h = e["hand_cards_you"] if side == "YOU" else e["hand_cards_opp"]
        ex = e["exact_you"] if side == "YOU" else e["exact_opp"]
        if h and ex and len(h) == 5 + (0 if True else 0):
            op_rows.append(dict(game=gi, side=side, won=int(r["winner"] == side), hand=h, first=int(r["first"] == side)))
print(f"{len(op_rows)} exact opening hands")
mon = [sum(is_monster(c) for c in o["hand"]) for o in op_rows]
won = np.array([o["won"] for o in op_rows])
for k in sorted(set(mon)):
    s = np.array(mon) == k
    if s.sum() >= 15:
        print(f"  {k} monsters in the opening 5: win {won[s].mean():.0%} (n={s.sum()})")
low = [sum(is_monster(c) and lvl(c) <= 4 for c in o["hand"]) for o in op_rows]
for k in sorted(set(low)):
    s = np.array(low) == k
    if s.sum() >= 15:
        print(f"  {k} Level<=4 monsters in the opening 5: win {won[s].mean():.0%} (n={s.sum()})")
print("  Opening hand contains the card -> win rate of those players (all 5-card openings, deck-dependent):")
res = []
for c in KEY:
    s = np.array([c in o["hand"] for o in op_rows])
    if s.sum() >= 25:
        res.append((won[s].mean(), c, int(s.sum())))
for w, c, n in sorted(res, reverse=True):
    print(f"    {c:28} {w:4.0%}  (n={n})")
print("  Base win rate of these players: %.0f%%" % (100 * won.mean()))

# ------------------------------------------------------------------ B. hold or play
print("\n=== B. HOLD OR PLAY (exact hands) ===")
hold = collections.defaultdict(lambda: [0, 0, 0, 0])          # card -> [winner present, winner held, loser present, loser held]
for gi, r in enumerate(rows):
    ev = r["events"]
    for i, e in enumerate(ev):
        if e["kind"] != "end_turn" or not e.get("hand_exact"): continue
        side = e["side"]; won_ = side == r["winner"]
        # cards that were in hand at the first play of this turn / start of main: use the turn event for this side's turn
        j = i
        while j >= 0 and not (ev[j]["kind"] == "turn" and ev[j]["side"] == side): j -= 1
        if j < 0: continue
        t = ev[j]
        start = t["hand_cards_you"] if side == "YOU" else t["hand_cards_opp"]
        if not start: continue
        left = collections.Counter(e["hand_before"]); st = collections.Counter(start)
        for c, n in st.items():
            k = 0 if won_ else 2
            hold[c][k] += n
            hold[c][k + 1] += min(n, left.get(c, 0))
tab = []
for c, (wp, wh, lp, lh) in hold.items():
    if wp + lp >= 80:
        tab.append((c, (wh + lh) / (wp + lp), wh / wp if wp else float('nan'), lh / lp if lp else float('nan'), wp + lp))
print("Share of times a card in hand at turn start is still in hand at the end of the turn (held), winners vs losers:")
print("  most held:", ", ".join(f"{c} {h:.0%} (W {w:.0%}/L {l:.0%})" for c, h, w, l, n in sorted(tab, key=lambda x: -x[1])[:14]))
print("  least held (played at once):", ", ".join(f"{c} {h:.0%}" for c, h, w, l, n in sorted(tab, key=lambda x: x[1])[:14]))
diff = [(w - l, c, w, l, n) for c, h, w, l, n in tab if not np.isnan(w) and not np.isnan(l) and n >= 150]
print("  winners hold more than losers:", ", ".join(f"{c} W {w:.0%} vs L {l:.0%}" for d, c, w, l, n in sorted(diff, reverse=True)[:8]))
print("  winners hold less than losers:", ", ".join(f"{c} W {w:.0%} vs L {l:.0%}" for d, c, w, l, n in sorted(diff)[:8]))

# ------------------------------------------------------------------ C. play-choice model
print("\n=== C. PLAY-CHOICE MODEL ===")
dec = []                      # one dict per decision
for gi, r in enumerate(rows):
    plays_turn = collections.Counter(); normal_used = collections.Counter(); cur = {}
    for e in r["events"]:
        if e["kind"] == "turn":
            plays_turn[e["side"]] = 0; normal_used[e["side"]] = 0; cur[e["side"]] = e["turn"]
            continue
        if e["kind"] not in ("summon", "set_monster", "set_st", "activate", "end_turn"): continue
        if not e.get("hand_exact") or not e.get("hand_before"):
            if e["kind"] in ("summon", "set_monster"): normal_used[e["side"]] += 1
            plays_turn[e["side"]] += 1 if e["kind"] != "end_turn" else 0
            continue
        h = e["hand_before"]; ch = e.get("card") if e["kind"] != "end_turn" else "END"
        if ch != "END" and ch not in h:
            continue
        dec.append(dict(game=gi, won=int(e["side"] == r["winner"]), side=e["side"], hand=h, chosen=ch, turn=e["turn"],
                        lp_me=e["lp_me"], lp_opp=e["lp_opp"], mon_me=e["mon_me"], mon_opp=e["mon_opp"],
                        gy_me=e.get("gy_me", 0), gy_opp=e.get("gy_opp", 0), st_me=e.get("st_me", 0), st_opp=e.get("st_opp", 0),
                        plays=plays_turn[e["side"]], normal=int(normal_used[e["side"]] > 0)))
        if e["kind"] in ("summon", "set_monster"): normal_used[e["side"]] += 1
        if e["kind"] != "end_turn": plays_turn[e["side"]] += 1
print(f"{len(dec)} decisions with an exact hand ({sum(d['won'] for d in dec)} by winners)")

vocab = sorted({c for d in dec for c in d["hand"]})
cid = {c: i for i, c in enumerate(vocab)}
def cand_rows(d):
    cnt = collections.Counter(d["hand"])
    nm = sum(is_monster(c) for c in d["hand"])
    base = dict(turn=d["turn"], lp_me=d["lp_me"], lp_opp=d["lp_opp"], lp_diff=d["lp_me"] - d["lp_opp"], mon_me=d["mon_me"], mon_opp=d["mon_opp"],
                hand_size=len(d["hand"]), hand_monsters=nm, hand_other=len(d["hand"]) - nm, plays=d["plays"], normal=d["normal"],
                gy_me=d["gy_me"], gy_opp=d["gy_opp"], st_me=d["st_me"], st_opp=d["st_opp"])
    out = []
    for c in list(cnt) + ["END"]:
        x = dict(base)
        if c == "END":
            x.update(card=-1, is_end=1, is_mon=0, level=0, atk=0, dup=0, mon_blocked=0)
        else:
            m = is_monster(c)
            x.update(card=cid[c], is_end=0, is_mon=int(m), level=lvl(c), atk=atk(c), dup=cnt[c], mon_blocked=int(m and d["normal"] == 1))
        out.append((c, x))
    return out

def build(ds):
    X, y, g, did = [], [], [], []
    for k, d in enumerate(ds):
        for c, x in cand_rows(d):
            X.append(x); y.append(int(c == d["chosen"])); g.append(d["game"]); did.append(k)
    return pd.DataFrame(X), np.array(y), np.array(g), np.array(did)

def evaluate(model, ds, X, y, did):
    p = model.predict(xgb.DMatrix(X)); top1 = top3 = n = 0; end_first = 0
    for k in range(len(ds)):
        idx = np.where(did == k)[0]
        order = idx[np.argsort(-p[idx])]
        n += 1; top1 += y[order[0]] == 1; top3 += y[order[:3]].sum() > 0
    return top1 / n, top3 / n

params = dict(objective="binary:logistic", max_depth=4, eta=0.08, subsample=0.8, colsample_bytree=0.8, min_child_weight=3, reg_lambda=2.0)
def run(ds, label):
    X, y, g, did = build(ds)
    gg = np.array([group[x] for x in g]); ug = np.unique(gg); rs = np.random.RandomState(1); rs.shuffle(ug); folds = np.array_split(ug, 5)
    t1 = t3 = nt = b1 = b3 = e1 = 0
    for f in folds:
        te = np.isin(gg, f); tr = ~te
        m = xgb.train(params, xgb.DMatrix(X[tr], y[tr]), 200)
        te_dec = sorted(set(did[te])); sub = [ds[k] for k in te_dec]
        Xt = X[te].reset_index(drop=True); yt = y[te]; dt = np.array([te_dec.index(k) for k in did[te]])
        a1, a3 = evaluate(m, sub, Xt, yt, dt)
        t1 += a1 * len(sub); t3 += a3 * len(sub); nt += len(sub)
        # baseline: always pick the card most often played in the training decisions that is in hand, else END (prior)
        prior = collections.Counter(); seen = collections.Counter()
        for k in sorted(set(did[tr])):
            d = ds[k]
            for c in set(d["hand"]) | {"END"}: seen[c] += 1
            prior[d["chosen"]] += 1
        score = lambda c: prior[c] / max(1, seen[c])
        for d in sub:
            cs = list(set(d["hand"])) + ["END"]
            r_ = sorted(cs, key=lambda c: -score(c))
            b1 += r_[0] == d["chosen"]; b3 += d["chosen"] in r_[:3]
    print(f"{label}: {nt} decisions | model top-1 {t1/nt:.0%} top-3 {t3/nt:.0%} | card-popularity baseline top-1 {b1/nt:.0%} top-3 {b3/nt:.0%}")
    return X, y

winners = [d for d in dec if d["won"]]
run(dec, "all players   ")
Xw, yw = run(winners, "winners only  ")

# final model on winners' decisions
X, y, g, did = build(winners)
final = xgb.train(params, xgb.DMatrix(X, y), 200)
os.makedirs(os.path.join(ROOT, "data", "models"), exist_ok=True)
final.save_model(os.path.join(ROOT, "data", "models", "policy_model.json"))
json.dump(dict(vocab=vocab, features=list(X.columns)), open(os.path.join(ROOT, "data", "models", "policy_meta.json"), "w"))
imp = final.get_score(importance_type="gain")
print("policy feature importance:", ", ".join(f"{k} {v:.0f}" for k, v in sorted(imp.items(), key=lambda x: -x[1])[:10]))

# how often do winners end the turn without playing anything vs. with cards left
end_n = sum(1 for d in winners if d["chosen"] == "END")
print(f"winners' decisions that were 'end turn': {end_n} of {len(winners)}")
# example: what winners do with each card when they have it (play rate in the same turn)

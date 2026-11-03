"""Position model + play-impact analysis.

1. Build one row per turn start: state from the point of view of the side to move.
2. Train a gradient-boosted win-probability model (grouped cross-validation, no deck/series leakage).
3. Use it to measure how much each card play changes the win probability (play impact).
Outputs data/models/position_model.json (xgboost) and data/models/play_impact.json; prints a report.
"""
import collections, json, os
import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import Ridge

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
rows = [r for r in rows if r["winner"] in ("YOU", "OPP")]
fp = lambda d: tuple(sorted(collections.Counter(d).items()))

# groups = connected components of shared decks (same as train_deck)
parent = {}
def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for r in rows:
    parent[find(fp(r["win_main"]))] = find(fp(r["lose_main"]))
comp = {}
gid = [comp.setdefault(find(fp(r["win_main"])), len(comp)) for r in rows]

BURN = {"Cannon Soldier", "Amazon Archer", "Ceasefire", "Magic Cylinder", "Ring of Destruction", "Fire Princess",
        "Lady Assailant of Flames", "Fire Sorcerer", "Raimei", "Giant Germ"}
FEATS = ["turn", "lp_me", "lp_opp", "lp_diff", "lp_ratio", "mon_me", "mon_opp", "mon_diff",
         "me_mon_played", "me_st_played", "me_effects", "me_direct", "me_attacks", "me_lp_lost", "me_lp_gained", "me_burn",
         "op_mon_played", "op_st_played", "op_effects", "op_direct", "op_attacks", "op_lp_lost", "op_lp_gained", "op_burn", "i_move_first"]

X, y, G, meta = [], [], [], []
for gi, r in enumerate(rows):
    ev = r["events"]; first = r["first"]
    cum = {s: collections.Counter() for s in ("YOU", "OPP")}
    idx = 0
    for e in ev:
        if e["kind"] == "turn":
            me = e["side"]; op = "OPP" if me == "YOU" else "YOU"
            lp_me, lp_op = e["lp_you"], e["lp_opp"]
            mon_me, mon_op = e["mon_you"], e["mon_opp"]
            if me == "OPP":
                lp_me, lp_op, mon_me, mon_op = lp_op, lp_me, mon_op, mon_me
            c, o = cum[me], cum[op]
            f = [e["turn"], lp_me, lp_op, lp_me - lp_op, lp_me / max(1, lp_op), mon_me, mon_op, mon_me - mon_op,
                 c["mon"], c["st"], c["eff"], c["direct"], c["att"], c["lost"], c["gain"], c["burn"],
                 o["mon"], o["st"], o["eff"], o["direct"], o["att"], o["lost"], o["gain"], o["burn"], int(first == me)]
            X.append(f); y.append(int(r["winner"] == me)); G.append(gi)
            meta.append((gi, e["turn"], me))
        else:
            c = cum[e["side"]]
            k = e["kind"]
            if k in ("summon", "set_monster"): c["mon"] += 1
            elif k in ("set_st", "activate"): c["st"] += 1
            elif k == "effect":
                c["eff"] += 1
                if e.get("card") in BURN: c["burn"] += 1
            elif k == "direct": c["direct"] += 1; c["att"] += 1
            elif k == "attack": c["att"] += 1
            elif k == "lp_loss": c["lost"] += e["amount"]
            elif k == "lp_gain": c["gain"] += e["amount"]
X = np.array(X, float); y = np.array(y); G = np.array(G); gid = np.array(gid)
print(f"{len(rows)} games -> {len(X)} turn snapshots; base rate {y.mean():.2f}")

params = dict(objective="binary:logistic", max_depth=3, eta=0.05, subsample=0.8, colsample_bytree=0.8,
              min_child_weight=5, eval_metric="auc", reg_lambda=2.0)
ug = np.unique(gid); rs = np.random.RandomState(0); rs.shuffle(ug); folds = np.array_split(ug, 5)
pred = np.zeros(len(X))
for f in folds:
    te = np.isin(gid[G], f); tr = ~te
    m = xgb.train(params, xgb.DMatrix(X[tr], y[tr], feature_names=FEATS), 250)
    pred[te] = m.predict(xgb.DMatrix(X[te], feature_names=FEATS))
print(f"grouped CV AUC (all turns): {roc_auc_score(y, pred):.3f}")
T = X[:, 0]
for lo, hi in ((1, 3), (4, 6), (7, 10), (11, 15), (16, 25), (26, 200)):
    s = (T >= lo) & (T <= hi)
    if s.sum() > 50 and 0 < y[s].mean() < 1:
        print(f"  turns {lo:3}-{hi:3}: AUC {roc_auc_score(y[s], pred[s]):.3f}  (n={s.sum()})")

model = xgb.train(params, xgb.DMatrix(X, y, feature_names=FEATS), 250)
os.makedirs(os.path.join(ROOT, "data", "models"), exist_ok=True)
model.save_model(os.path.join(ROOT, "data", "models", "position_model.json"))
imp = model.get_score(importance_type="gain")
print("\nFeature importance (gain):")
for k, v in sorted(imp.items(), key=lambda x: -x[1])[:12]:
    print(f"  {k:16} {v:8.1f}")

# calibration vs LP difference
print("\nWin chance for the side to move vs LP difference (observed, turn>=4):")
d = X[:, 3]; s0 = T >= 4
for lo, hi in ((-9e9, -4000), (-4000, -2000), (-2000, -500), (-500, 500), (500, 2000), (2000, 4000), (4000, 9e9)):
    s = s0 & (d > lo) & (d <= hi)
    if s.sum() > 20:
        print(f"  LP diff ({lo:>8.0f},{hi:>8.0f}]: win {y[s].mean():.0%} (n={s.sum()})")
print("\nWin chance vs monsters on board difference (turn>=4):")
md = X[:, 7]
for v in (-3, -2, -1, 0, 1, 2, 3):
    s = s0 & (md == v)
    if s.sum() > 20:
        print(f"  monsters me-opp = {v:+d}: win {y[s].mean():.0%} (n={s.sum()})")
print("\nWin chance vs direct attacks made so far (turn>=6):")
for v in (0, 1, 2, 3, 5):
    s = (T >= 6) & (X[:, 11] == v) if v < 5 else (T >= 6) & (X[:, 11] >= 5)
    if s.sum() > 20:
        print(f"  my direct attacks so far {'>=' if v==5 else '='}{v}: win {y[s].mean():.0%} (n={s.sum()})")

# ---- play impact: change in win probability across the mover's turn vs cards used
p_all = model.predict(xgb.DMatrix(X, feature_names=FEATS))
pos = {(g, t): i for i, (g, t, s) in enumerate(meta)}
delta, cards_used, turnno = [], [], []
for gi, r in enumerate(rows):
    ev = r["events"]
    turns = [(e["turn"], e["side"]) for e in ev if e["kind"] == "turn"]
    for k, (t, side) in enumerate(turns):
        if k + 2 >= len(turns): break                       # need the mover's next turn start
        i0 = pos[(gi, t)]; i1 = pos[(gi, turns[k + 2][0])]
        if turns[k + 2][1] != side: continue
        d_ = p_all[i1] - p_all[i0]
        used = collections.Counter(e["card"] for e in ev if e["turn"] == t and e["side"] == side and e["kind"] in ("summon", "set_monster", "set_st", "activate", "effect") and e.get("card"))
        delta.append(d_); cards_used.append(used); turnno.append(t)
vocab = [c for c, v in collections.Counter(c for u in cards_used for c in u).items() if v >= 25]
ix = {c: i for i, c in enumerate(vocab)}
A = np.zeros((len(delta), len(vocab) + 1))
for i, u in enumerate(cards_used):
    for c in u:
        if c in ix: A[i, ix[c]] = 1
    A[i, -1] = min(turnno[i], 40) / 40.0
rg = Ridge(alpha=3.0).fit(A, np.array(delta))
imp_ = {c: float(rg.coef_[ix[c]]) for c in vocab}
cnt = collections.Counter(c for u in cards_used for c in u)
json.dump(imp_, open(os.path.join(ROOT, "data", "models", "play_impact.json"), "w"), indent=1)
print(f"\nPLAY IMPACT: change in the mover's win probability over a turn in which the card was played (ridge, n={len(delta)} turns)")
order = sorted(vocab, key=lambda c: -imp_[c])
print(" best:  " + ", ".join(f"{c} {imp_[c]*100:+.1f}pt (x{cnt[c]})" for c in order[:20]))
print(" worst: " + ", ".join(f"{c} {imp_[c]*100:+.1f}pt (x{cnt[c]})" for c in order[-14:]))

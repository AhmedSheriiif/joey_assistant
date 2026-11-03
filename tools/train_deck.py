"""Deck-level analysis that is robust to repeated decks.

The replay set contains *series*: the same deck plays many games (one deck won 16 of 16). Counting each game would
let the model memorize decks, so we:
  * deduplicate to distinct (winner deck, loser deck) pairs,
  * cross-validate with groups = connected components of shared decks (no deck seen in both train and test),
  * report per-deck records (the real champion decks).
Outputs data/models/deck_model.json and prints a report.
"""
import collections, csv, json, os, sys
import numpy as np
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
rows = [r for r in rows if r["winner"] in ("YOU", "OPP")]
fp = lambda d: tuple(sorted(collections.Counter(d).items()))

# ---- distinct decks and their records
rec = collections.defaultdict(lambda: [0, 0])          # fp -> [wins, games]
for r in rows:
    w, l = fp(r["win_main"]), fp(r["lose_main"])
    rec[w][0] += 1; rec[w][1] += 1; rec[l][1] += 1
decks = {k: dict(wins=v[0], games=v[1]) for k, v in rec.items()}

# ---- distinct pairs (a series of identical matchups counts once)
pairs = {}
for r in rows:
    key = (fp(r["win_main"]), fp(r["lose_main"]))
    pairs.setdefault(key, dict(win=r["win_main"], lose=r["lose_main"], n=0))["n"] += 1
pl = list(pairs.values())
N = len(pl)
# connected components over shared decks => groups for CV
parent = {}
def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b):
    parent[find(a)] = find(b)
for (w, l) in pairs:
    union(w, l)
comp = {}
groups = np.array([comp.setdefault(find(w), len(comp)) for (w, l) in pairs])
print(f"{len(rows)} games -> {N} distinct matchups, {len(decks)} distinct decks, {len(comp)} independent groups")

use = collections.Counter()                  # in how many DISTINCT decks does each card appear
for k in decks:
    for c, _ in k:
        use[c] += 1
vocab = sorted(c for c, v in use.items() if v >= 8)
ix = {c: i for i, c in enumerate(vocab)}
def vec(deck):
    v = np.zeros(len(vocab))
    for c in set(deck):
        if c in ix:
            v[ix[c]] = 1.0
    return v
Dp = np.array([vec(p["win"]) - vec(p["lose"]) for p in pl])
print(f"{len(vocab)} cards seen in >=8 distinct decks")

# ---- grouped cross-validation
ug = np.unique(groups); rs = np.random.RandomState(3); rs.shuffle(ug)
folds = np.array_split(ug, 5)
best = None
for C in (0.01, 0.03, 0.1, 0.3, 1.0):
    preds = np.full(N, np.nan)
    for f in folds:
        te = np.isin(groups, f); tr = ~te
        Xtr = np.vstack([Dp[tr], -Dp[tr]]); ytr = np.r_[np.ones(tr.sum()), np.zeros(tr.sum())]
        m = LogisticRegression(C=C, fit_intercept=False, max_iter=3000).fit(Xtr, ytr)
        preds[te] = m.predict_proba(Dp[te])[:, 1]
    acc = float(np.mean(preds > 0.5)); auc = roc_auc_score(np.r_[np.ones(N), np.zeros(N)], np.r_[preds, 1 - preds])
    print(f"C={C}: grouped held-out accuracy {acc:.3f} AUC {auc:.3f}")
    if best is None or auc > best[0]:
        best = (auc, C, acc)
auc, C, acc = best
X = np.vstack([Dp, -Dp]); y = np.r_[np.ones(N), np.zeros(N)]
model = LogisticRegression(C=C, fit_intercept=False, max_iter=5000).fit(X, y)
coef = dict(zip(vocab, model.coef_[0]))
B = 200; pos = collections.Counter()
for _ in range(B):
    s = rs.randint(0, N, N)
    mb = LogisticRegression(C=C, fit_intercept=False, max_iter=3000).fit(np.vstack([Dp[s], -Dp[s]]), np.r_[np.ones(N), np.zeros(N)])
    for c, w in zip(vocab, mb.coef_[0]):
        pos[c] += w > 0

# ---- per card: distinct-matchup net advantage
res = {}
for c in vocab:
    j = ix[c]
    a = int(sum(1 for p in pl if c in p["win"] and c not in p["lose"]))
    b = int(sum(1 for p in pl if c not in p["win"] and c in p["lose"]))
    p_ = binomtest(a, a + b, 0.5).pvalue if a + b else 1.0
    res[c] = dict(only_win=a, only_lose=b, usage=use[c] / len(decks), net=(a - b) / max(1, a + b), p=p_,
                  coef=float(coef[c]), stab=pos[c] / B, decks=use[c])
json.dump(dict(n_games=len(rows), n_pairs=N, n_decks=len(decks), n_groups=len(comp), cv_auc=auc, cv_acc=acc, C=C, cards=res),
          open(os.path.join(ROOT, "data", "models", "deck_model.json") if os.path.isdir(os.path.join(ROOT, "data", "models")) else os.devnull, "w"), indent=1) if False else None
os.makedirs(os.path.join(ROOT, "data", "models"), exist_ok=True)
json.dump(dict(n_games=len(rows), n_pairs=N, n_decks=len(decks), n_groups=len(comp), cv_auc=auc, cv_acc=acc, C=C, cards=res),
          open(os.path.join(ROOT, "data", "models", "deck_model.json"), "w"), indent=1)

print(f"\nBest: C={C} grouped accuracy {acc:.3f} AUC {auc:.3f}  (0.5 = no signal)")
print("\nTOP cards by coefficient:")
for c in sorted(vocab, key=lambda c: -res[c]["coef"])[:22]:
    r = res[c]; print(f'  {c:28} coef {r["coef"]:+.3f} stab {r["stab"]:.2f} in {r["usage"]:.0%} of decks  only-win {r["only_win"]} only-lose {r["only_lose"]} p={r["p"]:.3f}')
print("\nBOTTOM:")
for c in sorted(vocab, key=lambda c: res[c]["coef"])[:15]:
    r = res[c]; print(f'  {c:28} coef {r["coef"]:+.3f} stab {r["stab"]:.2f} in {r["usage"]:.0%} of decks  only-win {r["only_win"]} only-lose {r["only_lose"]} p={r["p"]:.3f}')

print("\nCHAMPION DECKS (distinct decks, >=5 games):")
for k, v in sorted(decks.items(), key=lambda x: (-x[1]["wins"] / x[1]["games"], -x[1]["games"])):
    if v["games"] >= 5:
        main = ", ".join(f"{n}x {c}" if n > 1 else c for c, n in sorted(k, key=lambda x: (-x[1], x[0])))
        print(f'  {v["wins"]}/{v["games"]} ({sum(n for _, n in k)} cards): {main}')

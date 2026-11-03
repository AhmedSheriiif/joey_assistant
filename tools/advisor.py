"""First version of the play advisor.

Usage example:
  python tools/advisor.py --hand "Change of Heart, Giant Trunade, Jinzo, Monster Reborn, The Rock Spirit, Man-Eater Bug" --lp-me 8000 --lp-opp 8000 --mon-me 0 --mon-opp 0 --turn 1

It ranks the next action (play a card from the hand, or end the turn) by how often strong players did it in a similar state,
using the model trained on the winners' decisions (data/models/policy_model.json). It is an imitation of the replays,
not a solver: it does not look ahead and does not know the opponent's hand. Treat it as 'what the winners usually do here'.
Rules applied on top of the model: after you used your Normal Summon this turn, monsters are not offered.
"""
import argparse, csv, json, os, collections
import numpy as np
import pandas as pd
import xgboost as xgb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CARDS = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cards_game.csv"), encoding="utf8"))}
META = json.load(open(os.path.join(ROOT, "data", "models", "policy_meta.json")))
MODEL = xgb.Booster(); MODEL.load_model(os.path.join(ROOT, "data", "models", "policy_model.json"))
CID = {c: i for i, c in enumerate(META["vocab"])}


def _num(n, k):
    try:
        return int(CARDS[n][k])
    except Exception:
        return 0


NEEDS_OPP_MONSTER = {"Change of Heart", "Snatch Steal", "Mystic Box", "Tribute to The Doomed", "Offerings to the Doomed", "Ring of Destruction",
                     "Raigeki", "Fissure", "Nobleman of Crossout", "Thousand Knives", "Kunai with Chain", "Makiu", "Dark Hole"}
NEEDS_MY_MONSTER = {"United We Stand", "Mage Power", "Rush Recklessly", "Metalmorph", "Megamorph", "Axe of Despair", "Mystic Box",
                    "Salamandra", "Elf's Light", "Gust Fan", "Steel Shell", "Burning Spear", "Dragonic Attack", "Black Pendant", "Sword of Dragon's Soul"}
NEEDS_GRAVEYARD = {"Monster Reborn", "Premature Burial", "Call Of The Haunted", "Backup Soldier", "Return of the Doomed"}
NEEDS_SPELLTRAP_ON_FIELD = {"Mystical Space Typhoon", "Dust Tornado", "Heavy Storm", "Harpie's Feather Duster", "Giant Trunade", "Spiritualism"}


def legal(c, mon_me, mon_opp, my_gy, opp_gy, my_st, opp_st):
    """Cheap sanity filter from the card texts. A value of None means 'unknown' and disables that check."""
    if c in NEEDS_OPP_MONSTER and mon_opp == 0:
        return False
    if c in NEEDS_MY_MONSTER and mon_me == 0:
        return False
    if c in NEEDS_GRAVEYARD and my_gy is not None and opp_gy is not None and (my_gy + opp_gy) == 0:
        return False
    if c in NEEDS_SPELLTRAP_ON_FIELD and my_st is not None and opp_st is not None and (my_st + opp_st) == 0:
        return False
    return True


def advise(hand, lp_me, lp_opp, mon_me, mon_opp, turn, plays=0, normal_used=False, my_gy=None, opp_gy=None, my_st=None, opp_st=None):
    cnt = collections.Counter(hand)
    is_mon = lambda c: bool(CARDS.get(c, {}).get("level"))
    nm = sum(is_mon(c) for c in hand)
    base = dict(turn=turn, lp_me=lp_me, lp_opp=lp_opp, lp_diff=lp_me - lp_opp, mon_me=mon_me, mon_opp=mon_opp, hand_size=len(hand),
                hand_monsters=nm, hand_other=len(hand) - nm, plays=plays, normal=int(normal_used),
                gy_me=my_gy or 0, gy_opp=opp_gy or 0, st_me=my_st or 0, st_opp=opp_st or 0)
    rows, names = [], []
    for c in list(cnt) + ["END"]:
        x = dict(base)
        if c == "END":
            x.update(card=-1, is_end=1, is_mon=0, level=0, atk=0, dup=0, mon_blocked=0)
        else:
            m = is_mon(c)
            x.update(card=CID.get(c, -1), is_end=0, is_mon=int(m), level=_num(c, "level"), atk=_num(c, "atk"), dup=cnt[c],
                     mon_blocked=int(m and normal_used))
        rows.append(x); names.append(c)
    df = pd.DataFrame(rows)[META["features"]]
    p = MODEL.predict(xgb.DMatrix(df))
    out = []
    for c, v in zip(names, p):
        if c != "END" and is_mon(c) and normal_used:
            continue                                   # rule: one Normal Summon / Set per turn
        if c != "END" and not legal(c, mon_me, mon_opp, my_gy, opp_gy, my_st, opp_st):
            continue                                   # no target: not worth offering
        out.append((c, float(v)))
    tot = sum(v for _, v in out) or 1.0
    return sorted(((c, v / tot) for c, v in out), key=lambda x: -x[1])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hand", required=True, help="comma separated card names")
    ap.add_argument("--lp-me", type=int, default=8000); ap.add_argument("--lp-opp", type=int, default=8000)
    ap.add_argument("--mon-me", type=int, default=0); ap.add_argument("--mon-opp", type=int, default=0)
    ap.add_argument("--turn", type=int, default=1); ap.add_argument("--plays", type=int, default=0)
    ap.add_argument("--normal-used", action="store_true", help="you already Normal Summoned/Set a monster this turn")
    ap.add_argument("--my-gy", type=int, help="monsters in your Graveyard"); ap.add_argument("--opp-gy", type=int, help="monsters in his Graveyard")
    ap.add_argument("--my-st", type=int, help="Spell/Trap cards on your side"); ap.add_argument("--opp-st", type=int, help="Spell/Trap cards on his side")
    ap.add_argument("--my-monsters", help='your field, e.g. "Giant Rat, Sangan/s" (/d defense, /s Set, @n current ATK)')
    ap.add_argument("--opp-monsters", help='his field, e.g. "Jinzo, ?" (? = unknown Set monster)')
    ap.add_argument("--my-traps", default="", help="your Set cards that matter for burst, e.g. Ceasefire")
    ap.add_argument("--gy-best", default=None, help="best monster in a Graveyard (for Monster Reborn / Premature Burial)")
    a = ap.parse_args()
    hand = [h.strip() for h in a.hand.split(",") if h.strip()]
    lethal_cards = set()
    if a.my_monsters is not None or a.opp_monsters is not None:
        import lookahead
        me_ = lookahead.parse_monsters(a.my_monsters); opp_ = lookahead.parse_monsters(a.opp_monsters)
        a.mon_me, a.mon_opp = len(me_), len(opp_)
        ns = argparse.Namespace(hand=a.hand, my_monsters=a.my_monsters or "", opp_monsters=a.opp_monsters or "", lp_me=a.lp_me, lp_opp=a.lp_opp,
                                my_st=a.my_st or 0, opp_st=a.opp_st or 0, normal_used=a.normal_used, my_traps=a.my_traps, gy_best=a.gy_best)
        lookahead.report(ns)
        res = lookahead.burst(me_, hand, opp_, a.lp_me, a.lp_opp, a.my_st or 0, a.opp_st or 0, a.normal_used, [t.strip() for t in a.my_traps.split(",") if t.strip()], a.gy_best)
        if res["lethal"]:
            lethal_cards = set(res["lethal"][0]["cards"])
        print("\n=== WHAT WINNERS USUALLY DO IN A STATE LIKE THIS (model) ===")
    bad = [h for h in hand if h not in CARDS]
    if bad:
        print("unknown card names:", bad); raise SystemExit(1)
    for c, p in advise(hand, a.lp_me, a.lp_opp, a.mon_me, a.mon_opp, a.turn, a.plays, a.normal_used, a.my_gy, a.opp_gy, a.my_st, a.opp_st):
        mark = "*" if c in lethal_cards else " "
        print(f"{p:6.0%} {mark} {'END THE TURN' if c == 'END' else c}")
    if lethal_cards:
        print("(* = part of the lethal line above: play those first)")

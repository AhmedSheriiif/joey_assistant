"""Audit one duel turn by turn with the lookahead: did you have a kill, and would the danger check have warned you before he killed you?

Usage:  python tools/audit_replay.py REPLAY.ydr --me YOU|OPP
        (--me = which side is you in the decoder's labels; for your own games see data/user_sides.json)
Caveats: the field is rebuilt from the log (Set/summon/destroy events) and can be off after complex effects; the hand is exact only
until a search/shuffle effect, so 'known hand' is a lower bound. The kill check therefore only reports lines it can see.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_decode import analyse, load_cards
import lookahead as L

ap = argparse.ArgumentParser(); ap.add_argument("replay"); ap.add_argument("--me", choices=["YOU", "OPP"])
a = ap.parse_args()
cards = load_cards()
res = analyse(a.replay, cards)
me = a.me
if me is None:
    sides = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "user_sides.json")))
    me = sides.get(os.path.splitext(os.path.basename(a.replay))[0], "YOU")
mk = lambda fl: [L.Mon(n, "set" if fd else "atk") for n, fd in fl]
print(f"{os.path.basename(a.replay)}: you = {me}, winner = {res['winner']}")
ev = res["events"]
for i, e in enumerate(ev):
    if e["side"] != me:
        continue
    if e["kind"] == "main1":
        hand = [h for h in (e["hand_before"] or []) if h in L.CARDS]
        r = L.burst(mk(e["field_me"]), hand, mk(e["field_opp"]), e["lp_me"], e["lp_opp"], e["st_me"], e["st_opp"], False, [], None)
        print(f"turn {e['turn']:>3} start: LP {e['lp_me']} vs {e['lp_opp']}; known hand {len(hand)} card(s){'' if e['hand_exact'] else ' (partial)'}; best visible line {r['best']['damage']}"
              + ("  <-- LETHAL available" if r["lethal"] else ""))
    if e["kind"] == "end_turn":
        gy = [L.Mon(n) for n in e.get("gy_cards_opp", []) if n in L.CARDS and L.CARDS[n].get("level")]
        t = L.danger(mk(e["field_me"]), mk(e["field_opp"]), e["lp_me"], gy)
        worst = max(t, key=lambda x: x[1])
        nxt = next((x for x in ev[i + 1:] if x["kind"] == "turn"), None)
        actual = 0
        if nxt:
            j = ev.index(nxt) + 1
            while j < len(ev) and ev[j]["kind"] != "turn":
                if ev[j]["kind"] == "lp_loss" and ev[j]["side"] == me and not ev[j].get("cost"):
                    actual += ev[j]["amount"]
                j += 1
        print(f"turn {e['turn']:>3} end  : LP {e['lp_me']}; his worst-case estimate {worst[1]} ({L.level(worst[1], e['lp_me'])}) -> he actually dealt {actual} on his next turn")

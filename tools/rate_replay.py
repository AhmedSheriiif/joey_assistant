"""Rate a Power of Chaos replay: how each player played, what could be better, what the players teach us.

Usage:
  python tools/rate_replay.py REPLAY.ydr                  rate both players (the file name decides which side is you if it is in data/user_sides.json)
  python tools/rate_replay.py REPLAY.ydr --me YOU|OPP     say which side is you (labels: YOU = the second deck list, OPP = the first)
  python tools/rate_replay.py REPLAY.ydr --learn          also add it to the dataset (copies it into learned_replays/, runs tools/ingest.py)
  python tools/rate_replay.py REPLAY.ydr --learn --retrain  ... and retrain the three models
  python tools/rate_replay.py REPLAY.ydr --json

What it measures, per player (every number is counted from the log, benchmarks are recomputed from data/dataset/replays.jsonl):
  * Result, deck rating (tools/rate_deck.py), opening turn, life-point race and the turn where the game turned
  * Tempo: damage per turn, direct attacks, burn, removal against the winners / losers of the recorded games
  * Mistakes the log can show: free attacks not taken, possible lethal not taken (tools/lookahead.py), turns that ended inside his burst range,
    useful cards still in hand / Set cards unused when the game was lost
  * Style and signature cards, how the damage was dealt, the big turns (3000+ damage) with the cards used (new combos to learn)
Limits: the field is rebuilt from the log and can be off after complex effects; the hand is exact only until a search or shuffle effect;
what a player *chose not to do* is only seen where the log shows what was available. Read it as a coach's first look, not a verdict.
"""
import argparse, collections, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from replay_decode import analyse, load_cards
import lookahead as L
import rate_deck as RD

BURN = {"Cannon Soldier", "Ring of Destruction", "Ceasefire", "Fire Princess", "Amazon Archer", "Magic Cylinder", "Raimei", "Hinotama", "Final Flame",
        "Sparks", "Inferno Fire Blast", "Blast Sphere", "Ekibyo Drakmord", "Mirror Force", "Torrential Tribute"}
BURN = BURN - {"Mirror Force", "Torrential Tribute"}
SAFE = {"Kuriboh", "Waboku", "Scapegoat", "Imperial Order", "Mirror Wall", "Swords of Revealing Light", "Magic Cylinder", "Mirror Force", "Torrential Tribute",
        "Messenger of Peace", "Fairy Box", "Solemn Judgment", "Raigeki", "Dark Hole", "Heavy Storm", "Giant Trunade"}


def other(s): return "OPP" if s == "YOU" else "YOU"
def mk(fl): return [L.Mon(n, "set" if fd else "atk") for n, fd in fl]


def side_stats(events, s):
    """Counted per own turn. Used for the replay itself and for the benchmarks (so both come out of the same code)."""
    mine = [e for e in events if e["side"] == s]
    turns = sorted({e["turn"] for e in events if e["kind"] == "turn" and e["side"] == s})
    nt = max(1, len(turns))
    dmg_to_foe = 0; per_turn = collections.Counter(); sources = collections.Counter(); prev = None
    for e in events:
        if e["kind"] == "lp_loss" and e["side"] == other(s) and not e.get("cost"):
            dmg_to_foe += e["amount"]
            key = "battle" if prev and prev["kind"] == "attack" else "direct attack" if prev and prev["kind"] == "direct" else \
                  (f"effect: {prev.get('card')}" if prev and prev.get("card") else "other")
            sources[key] += e["amount"]
            owner = next((t for t in turns if t == e["turn"]), None)
            per_turn[e["turn"]] += e["amount"]
        prev = e
    seen = set(); removal = burn = effects = st_plays = 0
    for e in mine:
        c = e.get("card")
        if e["kind"] in ("activate", "effect") and c:
            if (e["turn"], c) not in seen:
                seen.add((e["turn"], c))
                removal += c in RD.REMOVAL; burn += c in BURN
            effects += e["kind"] == "effect"
        if e["kind"] in ("set_st", "activate") and c:
            st_plays += 1
    second = per_turn.get(turns[1], 0) if len(turns) > 1 else 0
    return dict(turns=nt, dmg=dmg_to_foe, dmg_per_turn=dmg_to_foe / nt, direct=sum(e["kind"] == "direct" for e in mine) / nt,
                attacks=sum(e["kind"] == "attack" for e in mine) / nt, burn=burn / nt, removal=removal / nt, effects=effects / nt,
                st_plays=st_plays / nt, second_turn_dmg=second, sources=dict(sources), per_turn=dict(per_turn))


def benchmarks(rows):
    path = os.path.join(ROOT, "data", "models", "replay_benchmarks.json")
    key = len(rows)
    if os.path.exists(path):
        b = json.load(open(path))
        if b.get("n") == key: return b
    acc = {"win": collections.defaultdict(list), "lose": collections.defaultdict(list)}
    for r in rows:
        if r["winner"] not in ("YOU", "OPP"): continue
        for s, tag in ((r["winner"], "win"), (other(r["winner"]), "lose")):
            st = side_stats(r["events"], s)
            for k in ("dmg_per_turn", "direct", "attacks", "burn", "removal", "effects", "st_plays", "second_turn_dmg"):
                acc[tag][k].append(st[k])
    b = {"n": key}
    for tag in acc: b[tag] = {k: sum(v) / len(v) for k, v in acc[tag].items()}
    json.dump(b, open(path, "w"), indent=1)
    return b


def lp_race(events, s):
    """(turn, lead) at the start of each of the player's turns."""
    out = []
    for e in events:
        if e["kind"] == "turn" and e["side"] == s:
            out.append((e["turn"], e[f"lp_{s.lower()}"] - e[f"lp_{other(s).lower()}"]))
    return out


def mistakes(events, s, winner, cards):
    out = dict(free_attacks=[], missed_lethal=[], open_turns=[], stuck=[], unused_sets=[], big_turns=[])
    last_turn = max((e["turn"] for e in events if e["kind"] == "turn"), default=0)
    my_main = [e for e in events if e["kind"] == "main1" and e["side"] == s]
    acted = collections.defaultdict(list)
    for e in events:
        if e["side"] == s: acted[e["turn"]].append(e)
    for e in my_main:
        t = e["turn"]
        up = [m for m in e["field_me"] if not m[1]]
        if not e["field_opp"] and up and not any(x["kind"] in ("attack", "direct") for x in acted[t]) and t > 1:
            out["free_attacks"].append((t, [m[0] for m in up], e["lp_opp"]))
        try:
            hand = [h for h in (e["hand_before"] or []) if h in L.CARDS]
            r = L.burst(mk(e["field_me"]), hand, mk(e["field_opp"]), e["lp_me"], e["lp_opp"], e["st_me"], e["st_opp"], False, [], None)
            if r["lethal"] and not (t >= last_turn - 1 and winner == s):
                out["missed_lethal"].append((t, r["lethal"][0]["damage"], e["lp_opp"], r["lethal"][0].get("log", [])[:6], e["hand_exact"]))
        except Exception:
            pass
    ends = [e for e in events if e["kind"] == "end_turn" and e["side"] == s]
    for i, e in enumerate(events):
        if e["kind"] != "end_turn" or e["side"] != s: continue
        try:
            gy = [L.Mon(n) for n in e.get("gy_cards_opp", []) if n in L.CARDS and L.CARDS[n].get("level")]
            worst = max(L.danger(mk(e["field_me"]), mk(e["field_opp"]), e["lp_me"], gy), key=lambda x: x[1])
        except Exception:
            continue
        actual = 0
        j = i + 1
        while j < len(events) and events[j]["kind"] != "turn":
            j += 1
        j += 1
        while j < len(events) and events[j]["kind"] != "turn":
            if events[j]["kind"] == "lp_loss" and events[j]["side"] == s and not events[j].get("cost"): actual += events[j]["amount"]
            j += 1
        held = [h for h in (e["hand_before"] or []) if h in SAFE]
        if worst[1] >= e["lp_me"] and (actual >= 0.6 * e["lp_me"] or (winner != s and e["turn"] >= last_turn - 1)):
            out["open_turns"].append((e["turn"], e["lp_me"], worst[1], actual, held))
    if winner != s and ends:
        e = ends[-1]
        out["stuck"] = [h for h in (e["hand_before"] or []) if h in SAFE or h in RD.REMOVAL]
        out["unused_sets"] = list(e["set_me"])
    by_turn = collections.defaultdict(float)
    for e in events:
        if e["kind"] == "lp_loss" and e["side"] == other(s) and not e.get("cost"): by_turn[e["turn"]] += e["amount"]
    for t, d in by_turn.items():
        if d >= 3000:
            cs = []
            for x in acted[t]:
                if x["kind"] in ("summon", "set_monster", "set_st", "activate", "effect") and x.get("card") and x["card"] not in cs: cs.append(x["card"])
            out["big_turns"].append((t, int(d), cs))
    return out


def style_of(st, race, winner_is_me, total_turns):
    src = st["sources"]; tot = max(1, sum(src.values()))
    battle = src.get("battle", 0) / tot; direct = src.get("direct attack", 0) / tot
    eff = sum(v for k, v in src.items() if k.startswith("effect")) / tot
    burn = sum(v for k, v in src.items() if k.startswith("effect:") and k.split(": ", 1)[1] in BURN) / tot
    if total_turns <= 10 and direct + eff >= 0.6 and st["dmg"] >= 6000: lab = "burst / OTK (a few explosive turns)"
    elif burn >= 0.3: lab = "burn finisher"
    elif battle >= 0.5: lab = "beatdown (wins by battle damage)"
    elif st["dmg_per_turn"] < 250 and total_turns >= 20: lab = "stall / control (slow, low damage)"
    elif direct >= 0.4: lab = "direct-attack tempo"
    else: lab = "mixed"
    return lab, dict(battle=battle, direct=direct, effects=eff, burn=burn)


def analyse_side(res, s, bench, cards, you_side, winner, deck_rep):
    ev = res["events"]; st = side_stats(ev, s); race = lp_race(ev, s); mi = mistakes(ev, s, winner, cards)
    won = winner == s
    ref = bench["win"]; lose = bench["lose"]
    lab, shares = style_of(st, race, won, res["turns"])
    played = collections.Counter(e["card"] for e in ev if e["side"] == s and e["kind"] in ("summon", "set_monster", "set_st", "activate", "effect") and e.get("card"))
    sig = [c for c, _ in played.most_common(8)]
    first_t = min((e["turn"] for e in ev if e["kind"] == "turn" and e["side"] == s), default=None)
    opening = [(e["kind"], e["card"]) for e in ev if e["side"] == s and e["turn"] == first_t and e["kind"] in ("summon", "set_monster", "set_st", "activate") and e.get("card")]
    behind_last = max((t for t, lead in race if lead < 0), default=None)
    worst = min(race, key=lambda x: x[1]) if race else None
    best = max(race, key=lambda x: x[1]) if race else None
    adv, tips, learn = [], [], []

    # ---- tempo against the recorded winners
    def rel(name, mine, w, l, unit=""):
        verdict = "close to the winners" if mine >= 0.85 * w else ("between losers and winners" if mine > l else "at the losers' level")
        return f"{name}: {mine:.2f}{unit} per turn (winners {w:.2f}, losers {l:.2f}): {verdict}"
    adv.append(rel("Damage dealt", st["dmg_per_turn"], ref["dmg_per_turn"], lose["dmg_per_turn"]))
    adv.append(rel("Direct attacks", st["direct"], ref["direct"], lose["direct"]))
    adv.append(rel("Removal / steal cards", st["removal"], ref["removal"], lose["removal"]))
    adv.append(f"Damage on your 2nd turn: {st['second_turn_dmg']:.0f} (winners {ref['second_turn_dmg']:.0f}, losers {lose['second_turn_dmg']:.0f})")
    if st["dmg_per_turn"] < 0.75 * ref["dmg_per_turn"] and not won:
        tips.append(f"You dealt {st['dmg_per_turn']:.0f} a turn, winners deal {ref['dmg_per_turn']:.0f}. Clear the blocker (MST, Man-Eater Bug, Penguin Soldier, Change of Heart) and then hit directly instead of attacking into Set monsters.")
    if st["direct"] < 0.6 * ref["direct"] and not won:
        tips.append("Few direct attacks. Winners get a direct hit on about 4 turns in 10; create the empty field first.")
    if st["removal"] < 0.6 * ref["removal"] and not won:
        tips.append("Little removal or steal used. Winners use about 1 removal card every 3 turns; hold MST / Raigeki / Dark Hole for the turn you can follow with a direct attack.")
    if mi["free_attacks"]:
        ts = ", ".join(f"turn {t} ({'/'.join(m)})" for t, m, _ in mi["free_attacks"][:5])
        tips.append(f"Free attack not taken: the opponent had no monster and you had a face-up monster but did not attack in {len(mi['free_attacks'])} turn(s): {ts}. (He may have had a Set Swords / Messenger of Peace; check the replay.)")
    for t, dmg, lpo, line, exact in mi["missed_lethal"][:3]:
        tips.append(f"Possible lethal on turn {t}: the lookahead found {dmg} damage against his {lpo} LP with {'your exact' if exact else 'your known'} hand. Line: {'; '.join(line) or 'see tools/advisor.py'}.")
    for t, lp, wc, actual, held in mi["open_turns"][:3]:
        tips.append(f"Turn {t}: you ended with {lp} LP while his worst case was {wc:.0f}; he then dealt {actual}. " + (f"You were holding {', '.join(held)}: use it before ending the turn." if held else "Keep a blocker, Kuriboh, Waboku or Scapegoat for that turn."))
    if mi["stuck"] and not won: tips.append(f"You lost with these useful cards still in hand: {', '.join(mi['stuck'])}.")
    if mi["unused_sets"] and not won: tips.append(f"Cards Set but not used at the end: {', '.join(mi['unused_sets'])}. Trap cards that never fire are dead cards; activate them in your own turn or bait with a weaker monster.")
    ot = [k for k, _ in opening]
    if first_t and not any(k in ("set_monster", "summon") for k in ot): tips.append("You played no monster on your first turn; winners play about one monster (Set) and one or two Spells/Traps on turn one.")
    if won and behind_last and behind_last >= 8:
        learn.append(f"Comeback: you were behind in life points as late as turn {behind_last} and still won. See what turned it (the big turns below).")
    # ---- deck
    if deck_rep:
        adv.append(f"Deck rating {deck_rep['rating']}/100 (grade {deck_rep['grade']}); dead cards: {', '.join(c for c, _ in deck_rep['dead']) or 'none'}")
        if deck_rep["dead"]: tips.append("Deck: " + "; ".join(f"{c} ({w})" for c, w in deck_rep["dead"][:3]))
        if deck_rep["cuts"] and not won: tips.append("Deck: cut " + ", ".join(c for c, _ in deck_rep["cuts"][:3]) + "; consider " + ", ".join(c for c, _ in deck_rep["adds"][:3]) + ".")
    return dict(side=s, won=won, stats=st, style=lab, shares=shares, signature=sig, opening=opening, race=dict(start=race[0] if race else None, worst=worst, best=best,
                behind_last=behind_last), mistakes=mi, advice=adv, tips=tips, learn=learn)


def final_blow(ev, s):
    la = [e for e in ev if e["side"] == s and e["kind"] in ("attack", "direct", "effect", "activate")]
    return (la[-1]["kind"], la[-1].get("attacker") or la[-1].get("card")) if la else (None, None)


def render(name, res, sides, you):
    L_ = [f"# Replay rating: {name}", ""]
    w = res["winner"]
    L_.append(f"Result: **{w} won** by {res['how']} after {res['turns']} turns; {res['first']} went first; life points at the end YOU {res['lp']['YOU']} / OPP {res['lp']['OPP']}. "
              f"(YOU = the 2nd deck list in the file, OPP = the 1st.) " + (f"You are **{you}**." if you else "Which side is you is not known: pass --me YOU|OPP."))
    for s in ("YOU", "OPP"):
        d = sides[s]; st = d["stats"]
        L_ += ["", f"## {s}{' (you)' if s == you else ''} - {'WON' if d['won'] else 'LOST'} - style: {d['style']}"]
        kind, card = final_blow(res["events"], s)
        sh = d["shares"]
        L_.append(f"Damage dealt {st['dmg']} over {st['turns']} turns: battle {sh['battle']:.0%}, direct attacks {sh['direct']:.0%}, effects {sh['effects']:.0%} (burn {sh['burn']:.0%}). Signature cards: {', '.join(d['signature'][:6])}.")
        r = d["race"]
        if r["best"] and r["worst"]:
            L_.append(f"Life-point lead at the start of your turns: best {r['best'][1]:+d} (turn {r['best'][0]}), worst {r['worst'][1]:+d} (turn {r['worst'][0]})" + (f", last behind on turn {r['behind_last']}" if r["behind_last"] else ", never behind"))
        if d["opening"]: L_.append("Opening turn: " + ", ".join(f"{k.replace('_', ' ')} {c}" for k, c in d["opening"]))
        L_ += ["", "How it compares with the recorded games:"] + [f"- {x}" for x in d["advice"]]
        if d["tips"]:
            L_ += ["", "What could be better:"] + [f"{i}. {x}" for i, x in enumerate(d["tips"], 1)]
        elif d["won"]:
            L_ += ["", "No clear mistake found in the log."]
        big = d["mistakes"]["big_turns"]
        if big:
            L_ += ["", "Big turns (3000+ damage): learn the line"] + [f"- turn {t}: {dmg} damage with {', '.join(cs[:9])}" for t, dmg, cs in big[:4]]
        for x in d["learn"]: L_.append(f"- {x}")
    L_ += ["", "## What to take from the players"]
    ws, ls = sides[w], sides[other(w)]
    if w in sides:
        L_.append(f"- The winner ({w}) played a **{ws['style']}** game: {ws['stats']['dmg_per_turn']:.0f} damage a turn against {ls['stats']['dmg_per_turn']:.0f}, with {ws['stats']['direct']:.2f} direct attacks a turn against {ls['stats']['direct']:.2f}.")
        L_.append(f"- The loser ({other(w)}) played **{ls['style']}**; the decisive difference is in: " + ", ".join(k for k, a, b in (("damage", ws['stats']['dmg_per_turn'], ls['stats']['dmg_per_turn']), ("direct attacks", ws['stats']['direct'], ls['stats']['direct']), ("removal", ws['stats']['removal'], ls['stats']['removal']), ("burn", ws['stats']['burn'], ls['stats']['burn'])) if a > 1.3 * b + 0.01) or "small margins; look at the turning-point turn")
    L_.append("- To fold this into the knowledge base run with `--learn` (adds the replay to the dataset), then retrain (`--retrain`) and read knowledge/11_model_findings.md.")
    L_.append("")
    L_.append("Caveat: the log shows what was played, not what was held back; hands are exact only until a search or shuffle. Treat every item as a place to look in the replay, not a verdict.")
    return "\n".join(L_)


def learn_replay(path, me, retrain):
    dst = os.path.join(ROOT, "learned_replays"); os.makedirs(dst, exist_ok=True)
    target = os.path.join(dst, os.path.basename(path))
    if not os.path.exists(target): shutil.copy2(path, target)
    base = os.path.splitext(os.path.basename(path))[0]
    sf = os.path.join(ROOT, "data", "user_sides.json")
    sides = json.load(open(sf)) if os.path.exists(sf) else {}
    if me and sides.get(base) != me:
        sides[base] = me; json.dump(sides, open(sf, "w"), indent=1)
    out = subprocess.run([sys.executable, os.path.join(HERE, "ingest.py")], capture_output=True, text=True, cwd=ROOT)
    msg = [out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-300:]]
    if retrain:
        for t in ("train_deck.py", "train_position.py", "train_behavior.py"):
            r = subprocess.run([sys.executable, os.path.join(HERE, t)], capture_output=True, text=True, cwd=ROOT)
            msg.append(f"{t}: {'ok' if r.returncode == 0 else 'failed: ' + r.stderr[-200:]}")
        bf = os.path.join(ROOT, "data", "models", "replay_benchmarks.json")
        if os.path.exists(bf): os.remove(bf)
    return msg


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("replay"); ap.add_argument("--me", choices=["YOU", "OPP"]); ap.add_argument("--json", action="store_true")
    ap.add_argument("--learn", action="store_true"); ap.add_argument("--retrain", action="store_true")
    a = ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    cards = load_cards()
    res = analyse(a.replay, cards)
    base = os.path.splitext(os.path.basename(a.replay))[0]
    sf = os.path.join(ROOT, "data", "user_sides.json")
    me = a.me or (json.load(open(sf)).get(base) if os.path.exists(sf) else None)
    rows = RD.load_dataset()
    bench = benchmarks([r for r in rows if r["winner"] in ("YOU", "OPP")])
    byid, byname = RD.load_cards(); model = RD.Model(); limits = RD.load_limits()
    decks = {"YOU": res["decks"][1], "OPP": res["decks"][0]}
    drep = {s: RD.analyse(decks[s], byid, byname, model, limits, 4000) for s in decks}
    sides = {s: analyse_side(res, s, bench, cards, me, res["winner"], drep[s]) for s in ("YOU", "OPP")}
    if a.json:
        print(json.dumps(dict(name=base, winner=res["winner"], turns=res["turns"], me=me, sides=sides), indent=1, ensure_ascii=False, default=str)); return
    print(render(base, res, sides, me))
    if a.learn or a.retrain:
        print("\n## Learning"); print("\n".join(learn_replay(a.replay, me, a.retrain)))


if __name__ == "__main__":
    main()

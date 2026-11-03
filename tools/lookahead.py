"""Lookahead: one-turn-kill (burst) planner and danger calculator.

Burst planner  : given your field, your hand and his field, search the plays that deal the most damage this turn
                 (removal / steals / summon / revive / equips / battle / Cannon Soldier & Amazon Archer burn) and say whether it is lethal.
Danger check   : how much damage he can plausibly deal on his next turn against your field, in three tiers
                 (board only / + one typical boost / + removal of your best blocker and a boost), plus the replay base rate.

Monster notation (comma separated): "Giant Rat" face-up Attack, "Wall of Illusion/d" face-up Defense, "Man-Eater Bug/s" Set face-down,
"?" an unknown Set monster (assumed 1400/1200), "Giant Rat@2200" to override the current ATK (equips already on it).
Cards come from data/cards_game.csv. This is a model of the main OTK patterns seen in the replays, not a full rules engine:
it ignores Chain timing, his Set cards beyond a trap-risk count, and any card it does not know.
"""
import argparse, collections, csv, itertools, json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CARDS = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cards_game.csv"), encoding="utf8"))}

# ----------------------------------------------------------------------------- card knowledge (from card texts)
RAIGEKI = {"Raigeki"}; DARKHOLE = {"Dark Hole"}
STEAL = {"Change of Heart", "Snatch Steal"}
FLAT_BURN = {"Raimei": 300, "Hinotama": 500, "Final Flame": 600, "Sparks": 200}
ST_REMOVAL = {"Mystical Space Typhoon", "Heavy Storm", "Giant Trunade", "Harpie's Feather Duster", "Dust Tornado"}
TYPE_ATK_BONUS = {"Axe of Despair": 1000, "Black Pendant": 500, "Rush Recklessly": 700, "Kunai with Chain": 500}
NO_DIRECT = {"Zombyra the Dark"}                 # cannot attack directly
DOUBLE_ATTACK = {"Hayabusa Knight"}
UNKNOWN_SET = (1400, 1200)


class Mon:
    def __init__(self, name, pos="atk", atk=None, df=None):
        self.name = name; self.pos = pos
        c = CARDS.get(name, {})
        self.level = int(c["level"]) if c.get("level") else 0
        self.type = c.get("type", "")
        self.base_atk = int(c["atk"]) if c.get("atk") else (UNKNOWN_SET[0] if name == "?" else 0)
        self.base_def = int(c["def"]) if c.get("def") else (UNKNOWN_SET[1] if name == "?" else 0)
        self.atk = atk if atk is not None else self.base_atk
        self.df = df if df is not None else self.base_def
        self.can_attack = True

    def copy(self):
        m = Mon.__new__(Mon); m.__dict__ = dict(self.__dict__); return m

    def __repr__(self):
        return f"{self.name}({self.atk}/{self.df},{self.pos})"


def parse_monsters(text):
    out = []
    for tok in [t.strip() for t in (text or "").split(",") if t.strip()]:
        atk = None
        if "@" in tok:
            tok, v = tok.split("@", 1); atk = int(v)
        pos = "atk"
        if "/" in tok:
            tok, p = tok.rsplit("/", 1)
            pos = {"a": "atk", "d": "def", "s": "set"}[p.strip().lower()[0]]
        tok = tok.strip()
        if tok != "?" and tok not in CARDS:
            raise SystemExit(f"unknown card: {tok}")
        out.append(Mon(tok, pos, atk))
    return out


# ----------------------------------------------------------------------------- battle and burn
def battle(attackers, blockers):
    """Greedy battle: kill blockers with the weakest sufficient attackers, then everything left hits directly.
    Returns (damage, destroyed_attackers_count, log)."""
    atks = []
    for m in attackers:
        if m.can_attack and m.pos != "def":
            atks.append(m)
            if m.name in DOUBLE_ATTACK:
                atks.append(m)
    atks = sorted(atks, key=lambda m: m.atk)
    blk = sorted(blockers, key=lambda m: -(m.atk if m.pos == "atk" else m.df))
    dmg = 0; log = []
    for b in list(blk):
        need = (b.atk if b.pos == "atk" else b.df)
        for a in atks:
            beats = a.atk > need or (b.pos == "atk" and a.atk == need)
            if beats:
                if b.pos == "atk":
                    d = max(0, a.atk - b.atk); dmg += d
                    log.append(f"{a.name} ({a.atk}) destroys {b.name} ({b.atk}) +{d}")
                else:
                    log.append(f"{a.name} ({a.atk}) destroys {b.name} (DEF {b.df})")
                atks.remove(a); blk.remove(b); break
    if blk:
        return dmg, log, False
    for a in atks:
        if a.name in NO_DIRECT:
            continue
        dmg += a.atk; log.append(f"{a.name} attacks directly for {a.atk}")
    return dmg, log, True


def burn_phase(my, extra_burn_ok=True):
    """Cannon Soldier / Amazon Archer / Catapult Turtle after battle. Returns (damage, log)."""
    names = [m.name for m in my]
    log = []; dmg = 0
    cannon = names.count("Cannon Soldier"); archer = names.count("Amazon Archer"); turtle = names.count("Catapult Turtle")
    burners = cannon + archer + turtle
    bodies = sorted([m for m in my if m.name not in ("Cannon Soldier", "Amazon Archer", "Catapult Turtle")], key=lambda m: -m.atk)
    n = len(bodies)
    if turtle and bodies:
        best = bodies[0]; d = best.atk // 2
        if d > 500 or not (cannon or archer):
            dmg += d; log.append(f"Catapult Turtle tributes {best.name} for {d}"); bodies = bodies[1:]; n -= 1
    if archer and n >= 2:
        a = n // 2; dmg += 1200 * a; log.append(f"Amazon Archer x{a} for {1200 * a}"); n -= 2 * a
    if cannon and n >= 1:
        dmg += 500 * n; log.append(f"Cannon Soldier x{n} for {500 * n}"); n = 0
    # the burner cards themselves can be tributed at the very end (an extra body each)
    spare = (cannon + archer + turtle) - 1
    if cannon and spare > 0 and burners > 1:
        dmg += 500 * spare; log.append(f"Cannon Soldier tributes the other burners x{spare} for {500 * spare}")
    return dmg, log


# ----------------------------------------------------------------------------- one plan
def best_boost(attackers, blockers, boosts, lp_me, lp_opp, my_st_after):
    """Try every attacker as the target of all boosts; return the damage of the best assignment."""
    base = [m.copy() for m in attackers]
    best = None
    targets = range(len(base)) if boosts else [None]
    for ti in targets:
        mons = [m.copy() for m in base]
        log = []
        if ti is not None and mons:
            t = mons[ti]
            for b in boosts:
                if b == "United We Stand":
                    n = sum(1 for m in mons if m.pos != "set") if True else 0
                    t.atk += 800 * n; log.append(f"United We Stand on {t.name} (+{800 * n})")
                elif b == "Mage Power":
                    t.atk += 500 * my_st_after; log.append(f"Mage Power on {t.name} (+{500 * my_st_after})")
                elif b == "Megamorph":
                    if lp_me < lp_opp:
                        t.atk = t.atk + t.base_atk; log.append(f"Megamorph doubles the original ATK of {t.name}")
                    else:
                        t.atk = t.atk - t.base_atk // 2; log.append(f"Megamorph halves {t.name} (your LP are higher)")
                elif b == "Limiter Removal":
                    for m in mons:
                        if m.type == "Machine":
                            m.atk *= 2
                    log.append("Limiter Removal doubles the Machines")
                elif b in TYPE_ATK_BONUS:
                    t.atk += TYPE_ATK_BONUS[b]; log.append(f"{b} on {t.name} (+{TYPE_ATK_BONUS[b]})")
        d, blog, direct = battle(mons, blockers)
        if best is None or d > best[0]:
            best = (d, log + blog, direct, mons)
    return best


def plan_line(me, hand, opp, lp_me, lp_opp, my_st, opp_st, normal_used, my_traps, gy_best):
    """Enumerate plays from the hand and return the list of (damage, log, flags) sorted best first."""
    spells = [c for c in hand if c in (RAIGEKI | DARKHOLE | STEAL | {"Mystic Box", "Nobleman of Crossout", "United We Stand", "Mage Power", "Rush Recklessly",
                                                                     "Kunai with Chain", "Axe of Despair", "Megamorph", "Limiter Removal", "Black Pendant",
                                                                     "Scapegoat", "Monster Reborn", "Premature Burial", "Call Of The Haunted"}
                                       | set(FLAT_BURN) | ST_REMOVAL)]
    summons = [None] + ([c for c in set(hand) if CARDS.get(c, {}).get("level") and int(CARDS[c]["level"]) <= 6] if not normal_used else [])
    results = []
    n = len(spells)
    for mask in range(1 << n):
        chosen = [spells[i] for i in range(n) if mask >> i & 1]
        if chosen.count("Scapegoat") > 1:
            continue
        for sm in summons:
            if sm and "Scapegoat" in chosen:
                continue                                  # Scapegoat forbids any summon that turn
            mon = [m.copy() for m in me]; foe = [m.copy() for m in opp]; log = []; lp_a = lp_me; lp_b = lp_opp
            flat = 0; st_used = my_st + 0
            # 1 clear the field
            if "Dark Hole" in chosen:
                mon = []; foe = []; log.append("Dark Hole clears the whole field")
            if "Raigeki" in chosen:
                foe = []; log.append("Raigeki destroys his monsters")
            # 2 steal / Mystic Box / Nobleman
            for s in [c for c in chosen if c in STEAL]:
                if foe:
                    best = max(foe, key=lambda m: m.atk if m.pos != "set" else m.base_atk); foe.remove(best)
                    stolen = best.copy(); stolen.pos = "atk"; stolen.can_attack = True; mon.append(stolen)
                    log.append(f"{s} takes {best.name}")
            if "Mystic Box" in chosen and foe and mon:
                best = max(foe, key=lambda m: m.atk); foe.remove(best); log.append(f"Mystic Box destroys {best.name}")
                gone = min(mon, key=lambda m: m.atk); mon.remove(gone)
            if "Nobleman of Crossout" in chosen:
                fd = [m for m in foe if m.pos == "set"]
                if fd:
                    foe.remove(fd[0]); log.append("Nobleman removes a Set monster")
            # 3 flip effects of my Set monsters
            for m in mon:
                if m.pos == "set":
                    m.pos = "atk"
                    if m.name == "Man-Eater Bug" and foe:
                        best = max(foe, key=lambda x: x.atk); foe.remove(best); log.append(f"Man-Eater Bug flips and destroys {best.name}")
                    elif m.name == "Penguin Soldier" and foe:
                        for _ in range(min(2, len(foe))):
                            best = max(foe, key=lambda x: x.atk); foe.remove(best)
                        log.append("Penguin Soldier flips and bounces up to 2 of his monsters")
                    elif m.name == "Slate Warrior":
                        m.atk += 500; m.df += 500; log.append("Slate Warrior flips (+500)")
            # 4 summon
            if sm:
                lv = int(CARDS[sm]["level"]); tributes = 0 if lv <= 4 else (1 if lv <= 6 else 2)
                if len(mon) >= tributes:
                    mon = sorted(mon, key=lambda m: m.atk)[tributes:]
                    mon.append(Mon(sm, "atk")); log.append(f"Summon {sm}" + (f" (Tribute {tributes})" if tributes else ""))
                else:
                    continue
            # 5 revive
            for r in [c for c in chosen if c in ("Monster Reborn", "Premature Burial", "Call Of The Haunted")]:
                if gy_best and len(mon) < 5:
                    mon.append(Mon(gy_best, "atk")); log.append(f"{r} revives {gy_best}")
                    if r == "Premature Burial":
                        lp_a -= 800
            # 6 Scapegoat tokens
            if "Scapegoat" in chosen:
                k = min(4, 5 - len(mon))
                for _ in range(k):
                    t = Mon("Sheep Token", "def"); t.can_attack = False; mon.append(t)
                log.append(f"Scapegoat makes {k} Sheep Tokens")
            # S/T count after plays for Mage Power (equips and traps count)
            st_after = my_st + sum(1 for c in chosen if c in ("United We Stand", "Mage Power", "Axe of Despair", "Megamorph", "Limiter Removal", "Black Pendant"))
            # 7 boosts + battle
            boosts = [c for c in chosen if c in ("United We Stand", "Mage Power", "Rush Recklessly", "Kunai with Chain", "Axe of Despair", "Megamorph", "Limiter Removal", "Black Pendant")]
            if "Kunai with Chain" in boosts:
                for f_ in foe:
                    if f_.pos == "atk":
                        f_.pos = "def"; log.append(f"Kunai shifts {f_.name} to Defense"); break
            bd, blog, direct, mon_after = best_boost(mon, foe, boosts, lp_a, lp_b, st_after)
            log += blog
            survivors = [m for m in mon_after]
            bdmg, burnlog = burn_phase(survivors)
            log += burnlog
            for c in chosen:
                if c in FLAT_BURN:
                    flat += FLAT_BURN[c]; log.append(f"{c} {FLAT_BURN[c]}")
            # my Set traps with burn: Ceasefire
            extra = 0
            if "Ceasefire" in my_traps:
                eff = sum(1 for m in survivors + foe if CARDS.get(m.name, {}).get("description", "") and not re.match(r"^\s*$", CARDS[m.name]["description"]) and m.pos != "set")
                extra += 500 * eff; log.append(f"Ceasefire {500 * eff}")
            # his Set S/T removal in this plan
            removed = sum(1 for c in chosen if c in ST_REMOVAL)
            traps_left = max(0, opp_st - removed)
            for c in chosen:
                if c in ST_REMOVAL:
                    log.insert(0, f"{c} removes his Set card(s) before you attack")
            total = bd + bdmg + flat + extra
            results.append(dict(damage=total, attack_damage=bd + extra * 0, burn=bdmg + flat + extra, log=log, cards=chosen + ([sm] if sm else []),
                                traps_left=traps_left, direct=direct))
    results.sort(key=lambda r: (-r["damage"], len(r["cards"])))
    return results


def burst(me, hand, opp, lp_me, lp_opp, my_st=0, opp_st=0, normal_used=False, my_traps=(), gy_best=None):
    res = plan_line(me, hand, opp, lp_me, lp_opp, my_st, opp_st, normal_used, set(my_traps), gy_best)
    best = res[0] if res else dict(damage=0, log=[], cards=[], traps_left=opp_st, attack_damage=0, burn=0, direct=False)
    lethal = sorted([r for r in res if r["damage"] >= lp_opp], key=lambda r: (r["traps_left"], len(r["cards"]), -r["damage"]))
    # lethal even if his Set cards stop all monster attacks: burn only
    burn_safe = [r for r in res if r["burn"] >= lp_opp]
    return dict(best=best, lethal=lethal[:3], burn_only_lethal=burn_safe[:1], trap_risk=best["traps_left"])


# ----------------------------------------------------------------------------- danger check (his next turn)
def danger(my, opp, lp_me, opp_gy=()):
    """His possible damage next turn against `my` field, in three tiers. `opp` are his monsters (all assumed able to attack)."""
    foe = [m.copy() for m in opp if m.pos != "set"] + [m.copy() for m in opp if m.pos == "set"]
    blockers = [m.copy() for m in my]
    tiers = []
    d0, l0, direct0 = battle(foe, blockers)
    b0, bl0 = burn_phase([m.copy() for m in foe])
    tiers.append(("board only", d0 + b0, l0 + bl0))
    # tier 1: one typical boost (United We Stand on his best attacker, or Rush) with the same blockers
    t1 = best_boost([m.copy() for m in foe], blockers, ["United We Stand"], lp_me, 8000, 1)
    d1 = t1[0] if t1 else d0
    d1b = best_boost([m.copy() for m in foe], blockers, ["Rush Recklessly"], lp_me, 8000, 1)
    d1 = max(d1, d1b[0] if d1b else 0)
    tiers.append(("+ one boost (United We Stand / Rush Recklessly)", d1 + b0, (t1[1] if t1 else [])))
    # tier 2: removal of your best blocker (Change of Heart: he takes it and attacks with it), then a boost
    blk2 = sorted(blockers, key=lambda m: -m.atk)
    stolen = None
    if blk2:
        stolen = blk2[0].copy(); blk2 = blk2[1:]
    foe2 = [m.copy() for m in foe] + ([stolen] if stolen else [])
    t2 = best_boost(foe2, blk2, ["United We Stand"], lp_me, 8000, 1)
    d2 = (t2[0] if t2 else 0)
    b2, bl2 = burn_phase([m.copy() for m in foe2])
    tiers.append(("+ he takes your best monster (Change of Heart) and boosts", d2 + b2, (t2[1] if t2 else []) + bl2))
    # tier 3: the Spell OTK package seen in the replays: he removes up to two of your monsters (steal + destroy), revives up to two monsters
    # from his Graveyard (Premature Burial / Monster Reborn) and equips United We Stand
    if opp_gy:
        blk3 = sorted([m.copy() for m in blockers], key=lambda m: -m.atk)
        stolen3 = blk3[0].copy() if blk3 else None
        blk3 = blk3[2:] if len(blk3) >= 2 else []
        foe3 = [m.copy() for m in foe] + ([stolen3] if stolen3 else [])
        for g in sorted(opp_gy, key=lambda m: -m.atk)[:2]:
            if len(foe3) < 5:
                foe3.append(g.copy())
        t3 = best_boost(foe3, blk3, ["United We Stand"], lp_me, 8000, 1)
        b3, bl3 = burn_phase([m.copy() for m in foe3])
        tiers.append(("+ Spell OTK package: steal one, destroy one, revive two from his Graveyard, United We Stand", (t3[0] if t3 else 0) + b3, (t3[1] if t3 else []) + bl3))
    return tiers


def level(dmg, lp):
    if dmg >= lp: return "LETHAL"
    if dmg >= 0.6 * lp: return "danger"
    if dmg >= 0.3 * lp: return "caution"
    return "ok"


def base_rates(lp_me, my_mon, opp_mon):
    """Share of turns in the replays where the player to move dealt at least `lp_me`, given monsters on each side (+/- 1)."""
    path = os.path.join(ROOT, "data", "models", "burst_stats.json")
    if not os.path.exists(path):
        rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "dataset", "replays.jsonl"), encoding="utf8")]
        out = []
        for r in rows:
            ev = r["events"]; idx = [i for i, e in enumerate(ev) if e["kind"] == "turn"]
            for k, i in enumerate(idx):
                j = idx[k + 1] if k + 1 < len(idx) else len(ev); me = ev[i]["side"]; op = "OPP" if me == "YOU" else "YOU"
                dmg = sum(e["amount"] for e in ev[i + 1:j] if e["kind"] == "lp_loss" and e["side"] == op and not e.get("cost"))
                mm = ev[i]["mon_you"] if me == "YOU" else ev[i]["mon_opp"]; mo = ev[i]["mon_opp"] if me == "YOU" else ev[i]["mon_you"]
                out.append((mm, mo, dmg))
        json.dump(out, open(path, "w"))
    rows = json.load(open(path))
    sel = [d for mm, mo, d in rows if abs(mm - opp_mon) <= 1 and abs(mo - my_mon) <= 1]
    if not sel:
        return None
    return sum(1 for d in sel if d >= lp_me) / len(sel), len(sel)


# ----------------------------------------------------------------------------- CLI
def report(args):
    me = parse_monsters(args.my_monsters); opp = parse_monsters(args.opp_monsters)
    hand = [h.strip() for h in args.hand.split(",") if h.strip()] if args.hand else []
    for h in hand:
        if h not in CARDS:
            raise SystemExit(f"unknown card in hand: {h}")
    traps = [t.strip() for t in (args.my_traps or "").split(",") if t.strip()]
    print(f"=== YOUR TURN: can you kill? (your LP {args.lp_me}, his LP {args.lp_opp}) ===")
    res = burst(me, hand, opp, args.lp_me, args.lp_opp, args.my_st, args.opp_st, args.normal_used, traps, args.gy_best)
    b = res["lethal"][0] if res["lethal"] else res["best"]
    print(f"Best line deals {b['damage']} (attacks/burn: {b['damage']-b['burn']} + {b['burn']}); he has {args.opp_st} Set Spell/Trap card(s)")
    for ln in b["log"]:
        print("   -", ln)
    if res["lethal"]:
        print(f"LETHAL: {b['damage']} >= {args.lp_opp}. Cards used: {', '.join(res['lethal'][0]['cards']) or 'board only'}")
        if b["traps_left"] and not res["burn_only_lethal"]:
            print(f"   Risk: with {b['traps_left']} Set card(s) still on his side he can stop the attacks (Mirror Force / Torrential / Magic Cylinder). Clear them first (MST, Heavy Storm, Trunade) or bait with the weakest attacker.")
        elif res["burn_only_lethal"]:
            print("   Burn alone is lethal, so Set traps cannot stop it.")
    else:
        print(f"Not lethal this turn: short by {args.lp_opp - b['damage']}.")
    print(f"\n=== HIS NEXT TURN: how dangerous is he? (your LP {args.lp_me}) ===")
    opp_gy = parse_monsters(getattr(args, 'opp_gy_monsters', ''))
    for name, dmg, log in danger(me, opp, args.lp_me, opp_gy):
        print(f"  {level(dmg, args.lp_me):8} {dmg:5d}  {name}")
    r = base_rates(args.lp_me, len(me), len(opp))
    if r:
        print(f"  In the replays, a player with {len(opp)}+/-1 monsters against {len(me)}+/-1 reached {args.lp_me}+ damage in {100*r[0]:.1f}% of turns (n={r[1]}).")
    worst = max(d for _, d, _ in danger(me, opp, args.lp_me, opp_gy))
    if worst >= args.lp_me:
        print("  Defensive ideas: keep Scapegoat / extra Set monsters as blockers, hold Waboku / Kuriboh / Swords of Revealing Light, set Imperial Order if his plan is Spell-based,")
        print("  and do not leave a single monster as your only blocker (Change of Heart / Snatch Steal take it).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hand", default="", help="your hand, comma separated")
    ap.add_argument("--my-monsters", default="", help='e.g. "Giant Rat, Sangan/s"')
    ap.add_argument("--opp-monsters", default="", help='e.g. "Jinzo, ?"')
    ap.add_argument("--lp-me", type=int, default=8000); ap.add_argument("--lp-opp", type=int, default=8000)
    ap.add_argument("--my-st", type=int, default=0, help="Spell/Trap cards on your side (for Mage Power)")
    ap.add_argument("--opp-st", type=int, default=0, help="Set Spell/Trap cards on his side")
    ap.add_argument("--normal-used", action="store_true")
    ap.add_argument("--my-traps", default="", help="your Set traps that matter, e.g. 'Ceasefire'")
    ap.add_argument("--gy-best", default=None, help="best monster in either Graveyard (for Monster Reborn etc.)")
    ap.add_argument("--opp-gy-monsters", default="", help="monsters in HIS Graveyard he could revive, e.g. 'Amazon Archer, Bazoo the Soul-Eater'")
    report(ap.parse_args())

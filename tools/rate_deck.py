"""Rate a Power of Chaos deck and recommend changes, using what the replays taught us (knowledge/11, 13, 17).

Usage:
  python tools/rate_deck.py DECK.ydc                 rate a deck file (the game's Common folder name works too: --common NAME.ydc)
  python tools/rate_deck.py REPLAY.ydr --side first|second|winner|loser    rate a deck stored inside a replay
  python tools/rate_deck.py DECK.ydc --json          machine-readable result
  python tools/rate_deck.py DECK.ydc --sims 20000    opening-hand simulation size

What it checks (all from the data in this project, nothing is invented):
  1. Legality     deck size, copies per card, the game's limited / semi-limited list (data/banlist.json of the web clone, or the built-in copy)
  2. Model score  sum of the card coefficients of the deck model (data/models/deck_model.json) and its percentile among the 229 recorded decks
  3. Structure    monsters, low-level bodies, removal, engine, defence, finishers, recursion vs the champion decks
  4. Dead cards   searchers without targets (Sonic Bird without Rituals), Fusion monsters without materials, anti-synergy (Royal Decree with your own traps)
  5. Opening      20,000 simulated six-card hands: how often you have bodies, removal, defence, an engine
  6. Advice       cards to cut, cards to add, closest champion deck
The rating is a guide: the deck model mixes deck strength with pilot skill (see knowledge/11_model_findings.md section 0).
"""
import argparse, collections, csv, glob, json, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

# ----------------------------------------------------------------------------- card knowledge (names as in cards_all.csv)
REMOVAL = {"Mystical Space Typhoon", "Dark Hole", "Raigeki", "Heavy Storm", "Giant Trunade", "Man-Eater Bug", "Penguin Soldier", "Crass Clown",
           "Change of Heart", "Snatch Steal", "Nobleman of Crossout", "Dust Tornado", "Harpie's Feather Duster", "Mirror Force", "Torrential Tribute",
           "Ring of Destruction", "Fissure", "Crush Card", "Smashing Ground", "Hammer Shot", "Tribute to The Doomed", "Offerings to the Doomed",
           "Mystic Box", "Trap Hole", "Bottomless Trap Hole", "Compulsory Evacuation Device", "Reinforcements"} - {"Reinforcements"}
ENGINE = {"Pot of Greed", "Graceful Charity", "Sangan", "Witch of the Black Forest", "Mystic Tomato", "Nimble Momonga", "Morphing Jar", "Giant Rat",
          "Fusion Sage", "Sonic Bird", "Card Destruction", "Magician of Faith", "Man-Eater Bug", "Upstart Goblin", "Solemn Wishes", "Giant Germ",
          "Mother Grizzly", "UFO Turtle", "Last Will", "Dark Magician of Chaos"} - {"Dark Magician of Chaos"}
DEFENSE = {"Scapegoat", "Kuriboh", "Waboku", "Swords of Revealing Light", "Magic Cylinder", "Mirror Force", "Torrential Tribute", "Imperial Order",
           "Mirror Wall", "Messenger of Peace", "Fairy Box", "Wall of Illusion", "Magic Jammer", "Solemn Judgment", "Seven Tools of the Bandit",
           "Call Of The Haunted", "Sakuretsu Armor", "Nobleman of Crossout", "Spirit Reaper"}
FINISH = {"Cannon Soldier", "Amazon Archer", "United We Stand", "Ring of Destruction", "Magic Cylinder", "Ceasefire", "Fire Princess", "Megamorph",
          "Rush Recklessly", "Hayabusa Knight", "Kunai with Chain", "Mage Power", "Axe of Despair", "Cyber-Stein", "Raimei", "Hinotama", "Final Flame"}
RECURSION = {"Monster Reborn", "Premature Burial", "Call Of The Haunted", "Magician of Faith"}
SELF_REPLACING = {"Mystic Tomato", "Nimble Momonga", "Sangan", "Witch of the Black Forest", "Morphing Jar", "Giant Rat", "Man-Eater Bug", "Giant Germ", "Mother Grizzly", "Penguin Soldier"}
GAIN = {"Cure Mermaid", "Solemn Wishes", "Nimble Momonga", "Dian Keto the Cure Master", "Fairy Meteor Crush"} | {"Mystic Tomato"} - {"Mystic Tomato"}
TRAP_HATE = {"Royal Decree", "Jinzo"}

# the champion decks recorded in the replays: structure targets (knowledge/17: 19 monsters, 21 spells/traps in the recommended list)
TARGET = {"monsters": (16, 22), "low": (13, 20), "removal": (7, 14), "engine": (5, 14), "defense": (5, 12), "finish": (2, 8)}


def load_cards():
    byid, byname = {}, {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "cards_all.csv"), encoding="utf8")):
        r["lv"] = int(r["level"]) if r["level"] else 0
        r["atk_n"] = int(r["atk"]) if r["atk"] else None
        r["def_n"] = int(r["def"]) if r["def"] else None
        r["isMon"] = bool(r["level"])
        byid[int(r["deck_id"])] = r
        if r["name"] not in byname or r["playable"] == "1":
            byname[r["name"]] = r
    return byid, byname


def read_ydc(path):
    d = open(path, "rb").read(); p = 8; out = []
    while p + 2 <= len(d):
        n = struct.unpack_from("<H", d, p)[0]; p += 2
        out.append(list(struct.unpack_from("<%dH" % n, d, p))); p += 2 * n
    while len(out) < 3: out.append([])
    return out[:3]


def read_deck_any(path, side):
    if path.lower().endswith(".ydr"):
        from replay_decks import read_replay, find_winner
        decks, events = read_replay(path)
        w = find_winner(events)
        pick = {"first": 0, "second": 1, "winner": 0 if w == "first" else 1, "loser": 1 if w == "first" else 0}[side or "winner"]
        return decks[pick]
    return read_ydc(path)


def load_limits():
    """copy limits: card -> max copies. Limited 1, semi-limited 2; level 0 are 'Forbidden if the option is on' and kept as warnings."""
    for p in (os.path.join(ROOT, "..", "joey_web_game", "data", "banlist.json"), os.path.join(ROOT, "data", "banlist.json")):
        if os.path.exists(p):
            js = json.load(open(p, encoding="utf8"))
            return {c["name"]: c["level"] for c in js["cards"]}
    return {}


def load_dataset():
    path = os.path.join(ROOT, "data", "dataset", "replays.jsonl")
    return [json.loads(l) for l in open(path, encoding="utf8")] if os.path.exists(path) else []


class Model:
    def __init__(self):
        self.dm = json.load(open(os.path.join(ROOT, "data", "models", "deck_model.json")))
        self.coef = {c: v["coef"] for c, v in self.dm["cards"].items()}
        self.info = self.dm["cards"]
        rows = [r for r in load_dataset() if r["winner"] in ("YOU", "OPP")]
        self.decks = {}
        for r in rows:
            for key, won in (("win_main", 1), ("lose_main", 0)):
                k = tuple(sorted(collections.Counter(r[key]).items()))
                d = self.decks.setdefault(k, [0, 0, r[key]]); d[0] += won; d[1] += 1
        self.scores = sorted(self.score(v[2]) for v in self.decks.values())
        self.rows = rows

    def score(self, names):
        return sum(self.coef.get(c, 0.0) for c in set(names))

    def percentile(self, s):
        return 100.0 * sum(1 for x in self.scores if x <= s) / max(1, len(self.scores))

    def champions(self, min_games=5, min_rate=0.85):
        return sorted(((v[0], v[1], v[2]) for v in self.decks.values() if v[1] >= min_games and v[0] / v[1] >= min_rate), reverse=True)


def fusion_info(c, byname):
    """materials of a Fusion monster from its text: ['A', 'B', ...] or None."""
    import re
    m = re.match(r'^"([^"]+)"(?:\s*\+\s*"([^"]+)")+', c["description"])
    if not m: return None
    return re.findall(r'"([^"]+)"', c["description"].split(".")[0])


def analyse(lists, byid, byname, model, limits, sims=20000, seed=7, singleton=False, banned=()):
    main, fusion, side = ([byid[i]["name"] if i in byid else f"#{i}" for i in l] for l in lists)
    cnt = collections.Counter(main)
    info = lambda n: byname.get(n)
    rep = dict(main=main, fusion=fusion, side=side, notes=[], errors=[], warnings=[], dead=[], unused_fusion=[], good=[])

    # ---- 1. legality
    n = len(main)
    if not 40 <= n <= 60: rep["errors"].append(f"main deck has {n} cards (the game wants 40 to 60)")
    if len(fusion) > 20: rep["errors"].append(f"Fusion deck has {len(fusion)} cards (maximum 20)")
    if len(side) > 15: rep["errors"].append(f"Side deck has {len(side)} cards (maximum 15)")
    allc = collections.Counter(main) + collections.Counter(side)
    for c, k in allc.items():
        if singleton and k > 1: rep["errors"].append(f"{c}: {k} copies (this format allows one copy of each card, main + side together)")
        elif k > 3: rep["errors"].append(f"{c}: {k} copies (maximum 3)")
        if c in banned: rep["errors"].append(f"{c} is banned in this format")
        lv = limits.get(c)
        if not singleton and lv in (1, 2) and k > lv: rep["errors"].append(f"{c}: {k} copies, the limit is {lv} ({'Limited' if lv == 1 else 'Semi-limited'})")
        if lv == 0: rep["warnings"].append(f"{c} is on the Forbidden list (banned only when the game's 'Forbidden Cards' option is on)")
        i = info(c)
        if i and i["playable"] != "1": rep["errors"].append(f"{c} is not a playable card in this game")

    # ---- 3. structure
    mons = [c for c in main if info(c) and info(c)["isMon"]]
    low = [c for c in mons if info(c)["lv"] <= 4]
    S = lambda group: sum(1 for c in main if c in group)
    rep["counts"] = dict(size=n, monsters=len(mons), spells_traps=n - len(mons), low=len(low), removal=S(REMOVAL), engine=S(ENGINE), defense=S(DEFENSE),
                         finish=S(FINISH), recursion=S(RECURSION), self_replacing=S(SELF_REPLACING), fusion_deck=len(fusion), side=len(side))
    for k, (lo, hi) in TARGET.items():
        key = {"monsters": "monsters", "low": "low", "removal": "removal", "engine": "engine", "defense": "defense", "finish": "finish"}[k]
        v = rep["counts"][key]
        if v < lo: rep["warnings"].append(f"only {v} {key} cards (the recorded winning decks run about {lo}-{hi})")
        elif v > hi: rep["warnings"].append(f"{v} {key} cards is more than the winning decks use ({lo}-{hi})")

    # ---- 4. dead cards and anti-synergy
    spells = [c for c in main if info(c) and not info(c)["isMon"]]
    rituals_s = {c for c in set(main) if info(c) and not info(c)["isMon"] and "Ritual Summon" in info(c)["description"]}
    rituals_m = {c for c in set(main) if info(c) and info(c)["isMon"] and "Ritual Summon" in info(c)["description"]}
    if (cnt["Sonic Bird"] or cnt["Senju of the Thousand Hands"]) and not (rituals_s or rituals_m):
        for c in ("Sonic Bird", "Senju of the Thousand Hands"):
            if cnt[c]: rep["dead"].append((c, f"x{cnt[c]}: fetches a Ritual card and the deck has none, so it is just a 1400/1000 body"))
    fus_support = [c for c in ("Polymerization", "Fusion Gate", "Cyber-Stein") if cnt[c]]
    mats_in_deck = set(main)
    versago = cnt["Versago the Destroyer"]
    live_fusions = []
    for f in sorted(set(fusion)):
        i = info(f); mats = fusion_info(i, byname) if i else None
        if not mats:
            live_fusions.append(f); continue
        missing = [m for m in mats if m not in mats_in_deck]
        ok = not missing or (len(missing) == 1 and versago > 0) or "Cyber-Stein" in fus_support
        if ok and fus_support: live_fusions.append(f)
        else:
            why = f"needs {', '.join(missing) or 'a Fusion spell'}" if fus_support else "the main deck has no Polymerization / Fusion Gate / Cyber-Stein"
            rep["unused_fusion"].append((f, f"x{fusion.count(f)}: {why}"))
    if fusion and not fus_support and fusion: rep["warnings"].append("a Fusion Deck but no Polymerization / Fusion Gate / Cyber-Stein in the main deck")
    if cnt["Polymerization"] and fusion and not live_fusions: rep["dead"].append(("Polymerization", f"x{cnt['Polymerization']}: no Fusion monster in the Fusion Deck can be made"))
    traps = [c for c in main if info(c) and not info(c)["isMon"] and info(c)["description"] and c in ("Solemn Wishes", "Call Of The Haunted", "Ring of Destruction", "Mirror Force",
             "Magic Cylinder", "Torrential Tribute", "Ceasefire", "Crush Card", "Imperial Order", "Waboku", "Mirror Wall", "Fairy Box", "Seven Tools of the Bandit", "Solemn Judgment", "Dust Tornado")]
    own_traps = len(traps)
    if cnt["Royal Decree"] and own_traps >= 3:
        rep["dead"].append(("Royal Decree", f"negates every Trap on the field, yours too: the deck has {own_traps} Trap cards of its own"))
    if cnt["Jinzo"] and own_traps >= 5:
        rep["warnings"].append(f"Jinzo shuts off your own Set Traps too ({own_traps} Trap cards in the deck): summon it only when you have none Set, or want his traps off")
    for c, qual, tag in (("Mystic Tomato", lambda i: i["isMon"] and i["attribute"] == "Dark" and (i["atk_n"] or 0) <= 1500, "DARK monsters with 1500 ATK or less"),
                         ("Sangan", lambda i: i["isMon"] and (i["atk_n"] or 0) <= 1500, "monsters with 1500 ATK or less"),
                         ("Witch of the Black Forest", lambda i: i["isMon"] and (i["def_n"] or 0) <= 1500, "monsters with 1500 DEF or less")):
        if cnt[c]:
            tg = sum(1 for x in set(main) if x != c and info(x) and qual(info(x)))
            if tg < 4: rep["warnings"].append(f"{c} has only {tg} targets in the deck ({tag})")
            else: rep["good"].append(f"{c} has {tg} different targets in the deck ({tag})")
    if cnt["United We Stand"] and len(mons) < 14: rep["warnings"].append("United We Stand wants many monsters on the field and you run few")
    if cnt["Fire Princess"] and not any(cnt[c] for c in GAIN): rep["dead"].append(("Fire Princess", "no Life Point gain in the deck to trigger her burn"))
    if cnt["Fire Princess"] and any(cnt[c] for c in GAIN): rep["good"].append("Fire Princess is paired with Life Point gain (" + ", ".join(c for c in GAIN if cnt[c]) + ")")
    if cnt["Cannon Soldier"] and (cnt["Scapegoat"] or S(SELF_REPLACING) >= 5): rep["good"].append("Cannon Soldier has fuel (Scapegoat tokens / self-replacing monsters)")
    if cnt["Thousand-Eyes Restrict"] or "Thousand-Eyes Restrict" in fusion:
        a = sum(cnt[c] for c in ("Relinquished", "Versago the Destroyer")); b = sum(cnt[c] for c in ("Thousand-Eyes Idol", "Versago the Destroyer"))
        rep["good"].append(f"Restrict plan: {a} cards can be the Relinquished half and {b} the Idol half; Polymerization/Fusion Sage access = {cnt['Polymerization'] + cnt['Fusion Sage']}")

    # ---- 2. model score
    s = model.score(main)
    rep["score"] = round(s, 2); rep["percentile"] = round(model.percentile(s), 1)
    champs = model.champions()
    rep["champion_scores"] = [round(model.score(c[2]), 2) for c in champs[:6]]
    rep["unknown_cards"] = sorted(c for c in set(main) if c not in model.coef)

    # ---- 5. opening hands
    rnd = random.Random(seed)
    stat = collections.Counter()
    for _ in range(sims):
        hand = rnd.sample(main, 6) if n >= 6 else list(main)
        hl = [c for c in hand if c in low]; hs = lambda g: any(c in g for c in hand)
        stat["bodies2"] += len(hl) >= 2; stat["nobody"] += len(hl) == 0
        stat["removal"] += hs(REMOVAL); stat["defense"] += hs(DEFENSE); stat["engine"] += hs(ENGINE | SELF_REPLACING); stat["finish"] += hs(FINISH)
        stat["brick"] += (len(hl) == 0 and not hs(ENGINE))
    rep["opening"] = {k: round(100.0 * v / sims, 1) for k, v in stat.items()}

    # ---- rating 0-100
    o = rep["opening"]
    part_model = rep["percentile"]
    part_open = max(0.0, min(100.0, 0.45 * o["bodies2"] + 0.2 * o["removal"] + 0.15 * o["defense"] + 0.2 * o["engine"] - 1.5 * o["nobody"]))
    inrange = sum(1 for k, (lo, hi) in TARGET.items() if lo <= rep["counts"][k] <= hi) / len(TARGET)
    part_struct = 100 * inrange
    deadn = sum(int(r.split(":")[0].split()[0].lstrip("x")) if False else 1 for r in rep["dead"])
    dead_cards = sum(main.count(c) + fusion.count(c) * 0 for c, _ in rep["dead"] if c in main)
    part_play = max(0.0, 100 - 12 * dead_cards - 15 * len(rep["errors"]))
    total = 0.40 * part_model + 0.25 * part_open + 0.20 * part_struct + 0.15 * part_play
    rep["parts"] = dict(model=round(part_model), opening=round(part_open), structure=round(part_struct), playable=round(part_play))
    rep["rating"] = round(total)
    rep["grade"] = "S" if total >= 85 else "A" if total >= 72 else "B" if total >= 58 else "C" if total >= 45 else "D"

    # ---- 6. advice
    rep["cuts"], rep["adds"] = [], []
    dead_names = {c for c, _ in rep["dead"] if c in main}
    cand_cut = sorted(set(main), key=lambda c: (c not in dead_names, model.coef.get(c, 0.0)))
    need = lambda: [k for k in ("removal", "engine", "defense", "finish") if rep["counts"][k] < TARGET[k][0]]
    for c in cand_cut[:6]:
        co = model.coef.get(c, 0.0)
        if c in dead_names: rep["cuts"].append((c, "does nothing in this deck"))
        elif co < -0.04: rep["cuts"].append((c, f"model coefficient {co:+.2f}: winning decks avoid it"))
    # candidates to add: strong cards the deck does not run, legal, needing no support the deck lacks
    unsupported = lambda c: (c in ("Sonic Bird", "Senju of the Thousand Hands") and not (rituals_s or rituals_m)) or c in TRAP_HATE or c in ("Polymerization", "Fusion Sage", "Fusion Gate") and not live_fusions or c == "Fire Princess"
    pool = []
    for c, co in model.coef.items():
        i = info(c)
        if not i or i["playable"] != "1" or c in main or unsupported(c): continue
        if limits.get(c) == 0: continue
        if i["isMon"] and i["lv"] >= 5: continue
        st = model.info[c]["stab"]
        if co > 0.05 and st >= 0.8: pool.append((co, c))
    for co, c in sorted(pool, reverse=True)[:8]:
        grp = [k for k, g in (("removal", REMOVAL), ("engine", ENGINE), ("defense", DEFENSE), ("finish", FINISH)) if c in g]
        rep["adds"].append((c, f"model coefficient {co:+.2f}" + (f"; the deck is short of {'/'.join(grp)}" if any(g in need() for g in grp) else "")))

    # closest champion deck
    mc = collections.Counter(main); best = None
    for w, g, k in champs:
        cc = collections.Counter(k); inter = sum((mc & cc).values()); uni = sum((mc | cc).values())
        j = inter / uni if uni else 0
        if best is None or j > best[0]: best = (j, w, g, cc)
    if best:
        j, w, g, cc = best
        rep["closest"] = dict(similarity=round(100 * j), record=f"{w}-{g}", missing=[f"{n}x {c}" if n > 1 else c for c, n in sorted((cc - mc).items(), key=lambda x: -x[1])[:10]],
                              extra=[f"{n}x {c}" if n > 1 else c for c, n in sorted((mc - cc).items(), key=lambda x: -x[1])[:10]])
    return rep


def render(rep, title):
    L = [f"# Deck rating: {title}", "", f"**Rating {rep['rating']}/100  (grade {rep['grade']})**  -  model {rep['parts']['model']}, opening hands {rep['parts']['opening']}, structure {rep['parts']['structure']}, playable {rep['parts']['playable']}", ""]
    c = rep["counts"]
    L += [f"Main {c['size']} ({c['monsters']} monsters, {c['spells_traps']} spells/traps, {c['low']} of Level 4 or lower), Fusion Deck {c['fusion_deck']}, Side Deck {c['side']}.",
          f"Removal {c['removal']}, engine {c['engine']}, defence {c['defense']}, finishers {c['finish']}, recursion {c['recursion']}, self-replacing bodies {c['self_replacing']}.",
          f"Deck-model score {rep['score']:+.2f}: better than {rep['percentile']:.0f}% of the 229 recorded decks (the best champion decks score {', '.join(f'{x:+.1f}' for x in rep['champion_scores'][:4])}).", ""]
    o = rep["opening"]
    L += ["## Opening hand (6 cards, simulated)", f"- two or more small monsters: {o['bodies2']}%   |   no small monster: {o['nobody']}%   |   a dead hand (no body, no engine): {o['brick']}%",
          f"- a removal card: {o['removal']}%   |   a defensive card: {o['defense']}%   |   an engine / self-replacing monster: {o['engine']}%   |   a finisher: {o['finish']}%", ""]
    if rep["errors"]: L += ["## Illegal"] + [f"- {x}" for x in rep["errors"]] + [""]
    if rep["dead"]: L += ["## Dead or fighting cards"] + [f"- **{c}**: {w}" for c, w in rep["dead"]] + [""]
    if rep["unused_fusion"]: L += ["## Fusion Deck cards you cannot make (harmless, but they are not part of the plan)"] + [f"- {c} {w}" for c, w in rep["unused_fusion"]] + [""]
    if rep["warnings"]: L += ["## Warnings"] + [f"- {x}" for x in rep["warnings"]] + [""]
    if rep["good"]: L += ["## What works"] + [f"- {x}" for x in rep["good"]] + [""]
    if rep["cuts"] or rep["adds"]:
        L += ["## Recommendation"]
        if rep["cuts"]: L += ["Cut: " + "; ".join(f"**{c}** ({w})" for c, w in rep["cuts"])]
        if rep["adds"]: L += ["Consider: " + "; ".join(f"**{c}** ({w})" for c, w in rep["adds"][:6])]
        L += [""]
    if rep.get("closest"):
        z = rep["closest"]
        L += [f"Closest champion deck: {z['similarity']}% similar (record {z['record']}). It has but you lack: {', '.join(z['missing']) or 'nothing'}. You have extra: {', '.join(z['extra']) or 'nothing'}.", ""]
    if rep["unknown_cards"]: L += ["Not rated by the model (seen in fewer than 8 recorded decks): " + ", ".join(rep["unknown_cards"]), ""]
    L += ["Caveat: the model learned from winners' decks, which mixes card power with pilot skill; treat the grade as +/-10 points and a lock or combo deck as under-rated."]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--side", choices=["first", "second", "winner", "loser"])
    ap.add_argument("--common", action="store_true", help="look the file up in the game's Common folder")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--sims", type=int, default=20000)
    ap.add_argument("--singleton", action="store_true", help="house format: one copy of every card (main + side together)")
    ap.add_argument("--banned", help="a text file with one banned card name per line (e.g. formats/new_rules_banned.txt) or names separated by ;")
    a = ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    path = a.path
    if a.common: path = os.path.join(os.path.expandvars(r"%APPDATA%\Yu-Gi-Oh! Power of Chaos Common"), a.path)
    byid, byname = load_cards()
    banned = set()
    if a.banned:
        txt = open(a.banned, encoding="utf8").read() if os.path.exists(a.banned) else a.banned
        banned = {x.strip() for x in txt.replace(";", chr(10)).splitlines() if x.strip() and not x.startswith("#")}
    rep = analyse(read_deck_any(path, a.side), byid, byname, Model(), load_limits(), a.sims, singleton=a.singleton, banned=banned)
    print(json.dumps(rep, indent=1, ensure_ascii=False) if a.json else render(rep, os.path.basename(path)))


if __name__ == "__main__":
    main()

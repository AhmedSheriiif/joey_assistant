"""Decode a Power of Chaos .ydr replay into a readable duel story with a board tracker.

Format notes: knowledge/05_replay_format.md.
Usage: python replay_decode.py <replay.ydr>
"""
import collections, csv, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "data", "cards_all.csv")

SEARCHERS = {"Sangan", "Witch of the Black Forest", "Berfomet", "Sonic Bird", "Giant Rat", "Mystic Tomato", "Mother Grizzly",
             "UFO Turtle", "Shining Angel", "Flying Kamakiri #1", "Giant Germ", "Nimble Momonga", "Last Will", "Insect Imitation",
             "Fusion Sage", "Bubonic Vermin", "Drill Bug", "Parasite Paracide", "Dark Magic Curtain", "Cyber Jar", "Spear Cretin"}
PHASE = {0x50: "draw phase", 0x51: "standby", 0x52: "main 1", 0x53: "battle phase",
         0x54: "main 2", 0x55: "end phase"}
SIDE = {True: "YOU", False: "OPP"}
CARD_OPS = {0xE6, 0xCE, 0xCF, 0x6F, 0x72, 0x75, 0x20, 0xAD, 0xAE, 0x86, 0x60}


def load_cards(path=CSV):
    cards = {}
    with open(path, encoding="utf8") as f:
        for r in csv.DictReader(f):
            cards[int(r["deck_id"])] = r
    return cards


def parse(path):
    d = open(path, "rb").read()
    assert d[:3] == b"YGR"
    seed = struct.unpack_from("<I", d, 24)[0]
    p = 28
    decks = []
    for _ in range(2):
        lists = []
        for _ in range(3):
            n = struct.unpack_from("<H", d, p)[0]; p += 2
            lists.append(list(struct.unpack_from("<%dH" % n, d, p))); p += 2 * n
        decks.append(lists)
    n = struct.unpack_from("<I", d, p)[0]; p += 4
    rec = [struct.unpack_from("<II", d, p + 8 * i) for i in range(n)]
    return seed, decks, rec


class Duel:
    """Board/LP tracker. Monster identity is known when summoned/set by the player's own action;
    Cyber Jar style mass summons are identified later when the card is flipped, attacked or destroyed."""

    def __init__(self, cards, decks=None, libs=None, recorder=None):
        self.cards = cards
        self.libs = {k: list(v) for k, v in libs.items()} if libs else None   # reconstructed shuffled libraries
        self.recorder = recorder                   # 'YOU' or 'OPP': the player whose client saved the replay
        self.hk = {"YOU": collections.Counter(), "OPP": collections.Counter()}   # cards known to be in hand
        self.gy = {"YOU": 0, "OPP": 0}              # monsters sent to the Graveyard (estimate)
        self.gy_cards = {"YOU": [], "OPP": []}       # their names (estimate)
        self.st_set = {"YOU": [], "OPP": []}      # names of Spell/Trap cards Set face-down and not yet used (estimate)
        self.hk_unknown = {"YOU": 0, "OPP": 0}      # cards in hand whose identity is no longer known
        self.maybe_gone = {"YOU": 0, "OPP": 0}      # cards in hk that may already have been discarded
        self.lib_exact = {"YOU": True, "OPP": True}  # library order still reproducible
        self.lib_lost = {"YOU": None, "OPP": None}   # why/when the library order was lost
        # decks: [first list, second list]; bit15 'YOU' = second list, 'OPP' = first list
        self.decks = {"YOU": list(decks[1][0]) if decks else [], "OPP": list(decks[0][0]) if decks else []}
        self.hand = {"YOU": 0, "OPP": 0}          # modelled hand size
        self.drawn = {"YOU": 0, "OPP": 0}         # cards taken from the deck so far
        self.accounted = {"YOU": collections.Counter(), "OPP": collections.Counter()}   # copies seen leaving the hand
        self.turn_plays = []                      # plays from hand in the current turn
        self.lp = {"YOU": 8000, "OPP": 8000}
        self.field = {"YOU": [None] * 5, "OPP": [None] * 5}
        self.facedown = {"YOU": [False] * 5, "OPP": [False] * 5}
        self.jar = False
        self.reveals = {"YOU": [], "OPP": []}
        self.selected = {"YOU": [], "OPP": []}
        self.pending_reveal = None   # (side, zone) set by op 0x80, filled by next 0x75
        self.turn = 0
        self.out = []
        self.events = []
        self.dead = {"YOU": None, "OPP": None}
        self.last_attack = None      # (attacker side, attacker zone, target zone or None, index of its line)

    def name(self, cid):
        r = self.cards.get(cid)
        return r["name"] if r else f"#{cid}"

    def stat(self, cid, k):
        try:
            return int(self.cards[cid][k])
        except (TypeError, ValueError, KeyError):
            return None

    def mon(self, side, slot):
        cid = self.field[side][slot] if 0 <= slot < 5 else None
        if cid is None:
            return "unknown monster"
        n = self.name(cid)
        return ("face-down " + n) if self.facedown[side][slot] else n

    def ev(self, kind, side, **kw):
        self.events.append(dict(turn=self.turn, kind=kind, side=side, **kw))

    def say(self, s):
        self.out.append(s)

    def library(self, side):
        return max(0, len(self.decks[side]) - self.drawn[side]) if self.decks[side] else None

    def unseen(self, side):
        """Deck cards not yet seen leaving the hand: the pool the hand and library are drawn from."""
        c = collections.Counter(self.decks[side]); c.subtract(self.accounted[side])
        return +c

    def take_cards(self, side, n):
        for _ in range(n):
            if self.libs and self.lib_exact[side] and self.libs[side]:
                self.hk[side][self.libs[side].pop(0)] += 1
            else:
                self.hk_unknown[side] += 1

    def lose_sync(self, side, why):
        if self.lib_exact[side]:
            self.lib_exact[side] = False
            self.lib_lost[side] = f"turn {self.turn}: {why}"

    def decision_state(self, side):
        """State at the moment of a decision by `side`: hand (names), whether it is exact, board and life points."""
        other = "OPP" if side == "YOU" else "YOU"
        exact = bool(self.libs) and self.lib_exact[side] and self.hk_unknown[side] == 0 and self.maybe_gone[side] == 0
        fl = lambda sd: [(self.name(c), self.facedown[sd][i]) for i, c in enumerate(self.field[sd]) if c is not None]
        return dict(hand_before=self.hand_list(side), hand_exact=exact, field_me=fl(side), field_opp=fl(other),
                    set_me=list(self.st_set[side]), set_opp=list(self.st_set[other]), gy_me=self.gy[side], gy_opp=self.gy[other], gy_cards_me=list(self.gy_cards[side]), gy_cards_opp=list(self.gy_cards[other]), st_me=len(self.st_set[side]), st_opp=len(self.st_set[other]),
                    lp_me=self.lp[side], lp_opp=self.lp[other],
                    mon_me=sum(c is not None for c in self.field[side]), mon_opp=sum(c is not None for c in self.field[other]))

    def hand_list(self, side):
        return sorted(self.name(c) for c, n in self.hk[side].items() for _ in range(n)) if self.libs else None

    def hand_text(self, side):
        known = []
        for c, n in sorted(((c, n) for c, n in self.hk[side].items() if n > 0), key=lambda x: self.name(x[0])):
            known.append(f"{n}x {self.name(c)}" if n > 1 else self.name(c))
        txt = ", ".join(known) if known else "-"
        extra = []
        if self.maybe_gone[side]:
            extra.append(f"up to {self.maybe_gone[side]} of these already discarded")
        if self.hk_unknown[side]:
            extra.append(f"+{self.hk_unknown[side]} unknown")
        return txt + (f"   ({'; '.join(extra)})" if extra else "")

    def play_from_hand(self, side, hi, slot):
        """slot is the 0-based position of the card in the hand; returns the hand size before the play."""
        before = self.hand[side]
        if slot >= before:
            self.hand[side] = before = slot + 1      # cards entered the hand without being logged (search effects)
        self.hand[side] -= 1
        self.accounted[side][hi] += 1
        if self.hk[side][hi] > 0:
            self.hk[side][hi] -= 1
            if self.maybe_gone[side] > sum(self.hk[side].values()):
                self.maybe_gone[side] = sum(self.hk[side].values())
        elif self.hk_unknown[side] > 0:
            self.hk_unknown[side] -= 1
        elif self.accounted[side][hi] > 1:
            pass                                   # the card was played before and came back to the hand (bounce / Giant Trunade / recycling)
        elif self.libs:
            self.lose_sync(side, f"played {self.name(hi)} that was not in the reconstructed hand")
        return before
        if slot > before:
            self.hand[side] = before = slot          # cards entered the hand without being logged (search effects)
        self.hand[side] -= 1
        self.accounted[side][hi] += 1
        return before

    def step(self, a, b):
        op = a & 0x7FFF; you = bool(a & 0x8000); side = SIDE[you]; other = SIDE[not you]; hi = a >> 16
        card = self.name(hi) if op in CARD_OPS and hi in self.cards else None
        if op == 0x01:
            self.turn += 1
            self.ev('turn', side, hand_cards_you=self.hand_list('YOU'), hand_cards_opp=self.hand_list('OPP'), exact_you=self.lib_exact['YOU'], exact_opp=self.lib_exact['OPP'], hand_you=self.hand['YOU'], hand_opp=self.hand['OPP'], lib_you=self.library('YOU'), lib_opp=self.library('OPP'), lp_you=self.lp['YOU'], lp_opp=self.lp['OPP'], mon_you=sum(c is not None for c in self.field['YOU']), mon_opp=sum(c is not None for c in self.field['OPP']))
            self.say(f"\n=== Turn {self.turn}: {side}   (LP YOU {self.lp['YOU']} / OPP {self.lp['OPP']}) ===")
            self.say(f"  hand: YOU {self.hand['YOU']} / OPP {self.hand['OPP']}   library: YOU {self.library('YOU')} / OPP {self.library('OPP')}")
            if self.libs:
                for s_ in ("YOU", "OPP"):
                    tag = " (recorder)" if s_ == self.recorder else ""
                    state = "exact" if self.lib_exact[s_] else "partly unknown"
                    self.say(f"    {s_}{tag} hand [{state}]: {self.hand_text(s_)}")
        elif op in PHASE:
            self.say(f"  [{PHASE[op]}]")
            if op == 0x52:
                self.ev('main1', side, **self.decision_state(side))
            if op == 0x50:
                self.jar = False
            if op == 0x55:
                self.ev('end_turn', side, **self.decision_state(side))
                if self.hand[side] > 6:
                    self.say(f"    {side} discards down to 6 cards (hand limit)")
                    self.maybe_gone[side] = min(sum(self.hk[side].values()), self.maybe_gone[side] + self.hand[side] - 6)
                    self.hand[side] = 6
                self.say(f"    end of turn: {side} holds {self.hand[side]} card(s) in hand")
        elif op == 0x04:
            self.say(f"  [DUEL END]  final LP: YOU {self.lp['YOU']} / OPP {self.lp['OPP']}")
        elif op == 0x61:
            self.hand[side] += b; self.drawn[side] += b
            self.take_cards(side, b)
            self.say(f"  {side} draws {b}  (hand now {self.hand[side]}, library {self.library(side)})")
        elif op == 0xCE and card:
            slot = (b >> 8) & 0xFF
            fd = bool((b >> 24) & 1)
            self.field[side][slot] = hi; self.facedown[side][slot] = fd
            snap = self.decision_state(side)
            hslot = b & 0xFF; hsize = self.play_from_hand(side, hi, hslot)
            self.ev('set_monster' if fd else 'summon', side, card=card, zone=slot, hand_slot=hslot, hand_size=hsize, **snap)
            self.say(f"  {side} {'SETS' if fd else 'SUMMONS'} {card} in monster zone {slot}" + (" (face-down)" if fd else "") + f"  [card {hslot + 1} of {hsize} in hand]")
        elif op == 0xCF and card:
            snap = self.decision_state(side)
            hslot = b & 0xFF; hsize = self.play_from_hand(side, hi, hslot)
            self.say(f"  {side} {'ACTIVATES' if (b >> 16) & 1 else 'SETS'} {card} (S/T zone {(b >> 8) & 0xF})  [card {hslot + 1} of {hsize} in hand]")
            self.ev('activate' if (b >> 16) & 1 else 'set_st', side, card=card, hand_slot=hslot, hand_size=hsize, **snap)
            if not (b >> 16) & 1:
                self.st_set[side].append(card)
        elif op == 0xE6 and card and b == 0x40000:
            self.selected[side].append(hi)
        elif op == 0x72 and card:
            self.say(f"    effect: {card}")
            self.ev('effect', side, card=card)
            if card in self.st_set[side]:
                self.st_set[side].remove(card)
            if card == "Graceful Charity":
                self.hand[side] = max(0, self.hand[side] - 2)
                self.maybe_gone[side] = min(sum(self.hk[side].values()), self.maybe_gone[side] + 2)
            elif card in SEARCHERS:
                self.hand[side] += 1
                self.hk_unknown[side] += 1
                self.lose_sync(side, f"{card} searched/shuffled the deck")
            elif card in ("Morphing Jar", "Morphing Jar #2"):
                for s_ in ("YOU", "OPP"):
                    self.hand[s_] = 0; self.hk[s_].clear(); self.hk_unknown[s_] = 0; self.maybe_gone[s_] = 0   # both discard; the 5 new draws follow as draw events
            la = self.last_attack
            if card == "Wall of Illusion" and la and la[2] is not None and (la[0] != side):
                self.say(f"    -> Wall of Illusion returns {la[0]}'s attacking {self.mon(la[0], la[1])} to its owner's hand (damage still counts)")
                self.field[la[0]][la[1]] = None
            if card == "Cyber Jar":
                self.field = {"YOU": [None] * 5, "OPP": [None] * 5}
                self.facedown = {"YOU": [False] * 5, "OPP": [False] * 5}
                self.jar = True
                self.reveals = {"YOU": [], "OPP": []}
                self.selected = {"YOU": [], "OPP": []}
        elif op == 0x80:
            self.pending_reveal = (side, hi)
        elif op == 0x75 and card:
            if self.pending_reveal:
                s, z = self.pending_reveal
                if 0 <= z < 5:
                    self.field[s][z] = hi; self.facedown[s][z] = False
                    la = self.last_attack
                    if la and la[2] == z and la[0] != s:
                        self.out[la[3]] = self.out[la[3]].replace("unknown monster (zone %d)" % z, "%s (zone %d)" % (self.name(hi), z))
                self.pending_reveal = None
            if self.jar:
                self.reveals[side].append(hi)
        elif op == 0x70:
            s = "YOU" if hi & 1 else "OPP"; zone = hi >> 8
            if self.jar:
                cid = self.selected[s].pop(0) if self.selected[s] else None
            else:
                cid = self.dead[s]
            if self.jar and self.hand[s] > 0:
                self.hand[s] -= 1
            if 0 <= zone < 5:
                self.field[s][zone] = cid; self.facedown[s][zone] = False
            self.say(f"    {s} special summons {self.name(cid) if cid else 'a monster'} to zone {zone}")
        elif op == 0x33:
            t = b & 0xFF
            self.say(f"  {side} attacks with {self.mon(side, hi)} (zone {hi}) -> {other}'s {self.mon(other, t)} (zone {t})")
            self.last_attack = (side, hi, t, len(self.out) - 1)
            self.ev('attack', side, attacker=self.field[side][hi], target=self.field[other][t] if 0 <= t < 5 else None)
            self.facedown[side][hi] = False
        elif op == 0x34:
            self.say(f"  {side} attacks DIRECTLY with {self.mon(side, hi)} (zone {hi})")
            self.last_attack = (side, hi, None, len(self.out) - 1)
            self.ev('direct', side, attacker=self.field[side][hi])
            self.facedown[side][hi] = False
        elif op == 0x3C:
            self.dead[side] = self.field[side][hi] if 0 <= hi < 5 else None
            self.say(f"    {side}'s {self.mon(side, hi)} (zone {hi}) is destroyed in battle")
        elif op in (0x7C, 0x79):                      # 0x79: destroyed by a card effect (zones 0-4 monsters, 5-9 Spell/Trap)
            if 0 <= hi < 5:
                if self.field[side][hi] is not None:
                    self.gy[side] += 1
                    self.gy_cards[side].append(self.name(self.field[side][hi]))
                self.field[side][hi] = None
        elif op == 0x43:
            self.lp[side] -= hi
            self.say(f"    {side} loses {hi} LP -> {self.lp[side]}")
            self.ev('lp_loss', side, amount=hi, cost=(b == 0), lp=self.lp[side])
        elif op == 0x42:
            self.lp[side] += hi
            self.say(f"    {side} gains {hi} LP -> {self.lp[side]}")
            self.ev('lp_gain', side, amount=hi, lp=self.lp[side])

    def run(self, rec):
        for a, b in rec:
            self.step(a, b)
        return self.out


def analyse(path, cards):
    raw = open(path, "rb").read()
    seed, decks, rec = parse(path)
    first_side = next((SIDE[bool(a & 0x8000)] for a, b in rec if (a & 0x7FFF) == 0x01), None)
    libs = None
    if first_side:
        from hands import initial_libraries
        libs = initial_libraries([decks[0][0:1][0], decks[1][0:1][0]] if False else [decks[0], decks[1]], seed, 1 if first_side == "YOU" else 0)
    flag16 = struct.unpack_from("<I", raw, 16)[0]
    recorder = "YOU" if flag16 == 1 else "OPP"
    d = Duel(cards, decks, libs, recorder)
    d.run(rec)
    lp = d.lp
    how = "lp"
    winner = "YOU" if lp["OPP"] <= 0 < lp["YOU"] else "OPP" if lp["YOU"] <= 0 < lp["OPP"] else None
    if winner is None:
        ops = [(a & 0x7FFF, SIDE[bool(a & 0x8000)]) for a, b in rec]
        loser = None
        if len(ops) >= 2 and ops[-2][0] == 0x05:          # surrender: flagged side gives up
            loser, how = ops[-2][1], "surrender"
        elif len(ops) >= 2 and ops[-2][0] == 0x61:         # drew from an empty deck
            loser, how = ops[-2][1], "deck-out"
        if loser:
            winner = "OPP" if loser == "YOU" else "YOU"
        else:
            winner, how = "unknown", "unknown"
    first = next((e["side"] for e in d.events if e["kind"] == "turn"), None)
    return dict(seed=seed, decks=decks, events=d.events, lp=lp, winner=winner, first=first, how=how,
                turns=d.turn, story=d.out, version=raw[4:12].hex(), recorder=recorder, lib_lost=d.lib_lost)


def story(path, cards):
    seed, decks, rec = parse(path)
    d = Duel(cards)
    return [f"seed={seed}  YOU=2nd deck list, OPP=1st deck list"] + d.run(rec)


if __name__ == "__main__":
    print("\n".join(story(sys.argv[1], load_cards())))

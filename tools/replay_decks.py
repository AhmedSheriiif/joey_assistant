"""Give it a replay (.ydr), get back both decks.

Usage:
  python tools/replay_decks.py REPLAY.ydr [REPLAY2.ydr ...]        print both decks (main, fusion, side) with card names
  python tools/replay_decks.py FOLDER                              every .ydr in the folder
  python tools/replay_decks.py REPLAY.ydr --export OUTDIR          also write the decks as .ydc files you can load in the game
  python tools/replay_decks.py REPLAY.ydr --only winner            only print the winner's deck (also: loser, first, second)

The replay stores two decks. 'first' is the first deck list in the file, 'second' the other one; neither is necessarily you.
The winner is worked out from the game log (life points, surrender or deck-out).
Only the Python standard library is needed.
"""
import argparse, collections, csv, glob, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CARDS_CSV = os.path.join(HERE, "..", "data", "cards_all.csv")
YDC_HEADER = bytes.fromhex("01f312005754cb3f")      # same header as the .ydc files in the game's Common folder


def load_names():
    names = {}
    if os.path.exists(CARDS_CSV):
        with open(CARDS_CSV, encoding="utf8") as fh:
            for r in csv.DictReader(fh):
                names[int(r["deck_id"])] = r["name"]
    return names


def read_replay(path):
    d = open(path, "rb").read()
    if d[:3] != b"YGR":
        raise ValueError("not a Power of Chaos replay (missing 'YGR' header)")
    p = 28
    decks = []
    for _ in range(2):
        lists = []
        for _ in range(3):
            n = struct.unpack_from("<H", d, p)[0]; p += 2
            lists.append(list(struct.unpack_from("<%dH" % n, d, p))); p += 2 * n
        decks.append(lists)
    n = struct.unpack_from("<I", d, p)[0]; p += 4
    events = [struct.unpack_from("<II", d, p + 8 * i) for i in range(n)]
    return decks, events


def find_winner(events):
    """Return 'first' or 'second' (which deck list won) or None. Bit 15 of an event = second list."""
    lp = {True: 8000, False: 8000}
    last = []
    for a, b in events:
        op = a & 0x7FFF; second = bool(a & 0x8000); hi = a >> 16
        if op == 0x43:
            lp[second] -= hi
        elif op == 0x42:
            lp[second] += hi
        last.append((op, second))
    if lp[False] <= 0 < lp[True]:
        return "second"
    if lp[True] <= 0 < lp[False]:
        return "first"
    if len(last) >= 2 and last[-2][0] == 0x05:          # surrender: the flagged side gave up
        return "first" if last[-2][1] else "second"
    if len(last) >= 2 and last[-2][0] == 0x61:          # drew from an empty deck
        return "first" if last[-2][1] else "second"
    return None


def fmt(ids, names):
    c = collections.Counter(ids)
    return ", ".join(f"{n}x {names.get(i, '#' + str(i))}" if n > 1 else names.get(i, "#" + str(i))
                     for i, n in sorted(c.items(), key=lambda x: (-x[1], names.get(x[0], ""))))


def write_ydc(path, lists):
    data = YDC_HEADER
    for l in lists:
        data += struct.pack("<H", len(l)) + struct.pack("<%dH" % len(l), *l)
    open(path, "wb").write(data)


def main():
    ap = argparse.ArgumentParser(description="Print the decks stored in Power of Chaos replays.")
    ap.add_argument("paths", nargs="+", help="replay files or folders")
    ap.add_argument("--export", metavar="DIR", help="write the decks as .ydc files into DIR")
    ap.add_argument("--only", choices=["winner", "loser", "first", "second"], help="print only one deck")
    args = ap.parse_args()
    names = load_names()
    files = []
    for p in args.paths:
        files += sorted(glob.glob(os.path.join(p, "*.ydr"))) if os.path.isdir(p) else [p]
    if args.export:
        os.makedirs(args.export, exist_ok=True)
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        try:
            decks, events = read_replay(f)
        except Exception as e:
            print(f"== {base}: cannot read ({e})\n"); continue
        winner = find_winner(events)
        roles = {"first": decks[0], "second": decks[1]}
        print(f"== {base}   winner: {winner or 'unknown'}")
        for role, lists in roles.items():
            tag = "WINNER" if role == winner else "loser" if winner else ""
            if args.only == "winner" and role != winner: continue
            if args.only == "loser" and (role == winner or winner is None): continue
            if args.only in ("first", "second") and args.only != role: continue
            main_, fus, side = lists
            print(f"-- {role} deck {('(' + tag + ')') if tag else ''}: main {len(main_)}, fusion {len(fus)}, side {len(side)}")
            print("   Main:   " + fmt(main_, names))
            if fus:
                print("   Fusion: " + fmt(fus, names))
            if side:
                print("   Side:   " + fmt(side, names))
            if args.export:
                out = os.path.join(args.export, f"{base}_{role}{'_WIN' if role == winner else ''}.ydc".replace(" ", "_"))
                write_ydc(out, lists)
        print()
    if args.export:
        print("decks written to", os.path.abspath(args.export))


if __name__ == "__main__":
    main()

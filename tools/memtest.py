"""Compare a replay's computed hands with a memory snapshot: python tools/memtest.py REPLAY.ydr SNAPSHOT.bin"""
import json, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hands import initial_libraries
from replay_decks import read_replay

rep, snap = sys.argv[1], sys.argv[2]
d = open(rep, "rb").read()
seed = struct.unpack_from("<I", d, 24)[0]
first_moves_second = struct.unpack_from("<I", d, 20)[0]
decks, ev = read_replay(rep)
first_list = 1 if first_moves_second else 0
libs = initial_libraries(decks, seed, first_list)
print("seed", seed, "flag20", first_moves_second)
data = open(snap, "rb").read(); regions = json.load(open(snap[:-4] + ".json"))


def where(i):
    for base, size, p in regions:
        if p <= i < p + size:
            return base + i - p


for label, lib in libs.items():
    for n in (5, 6, 8, 12, 40):
        ids = lib[:n]
        for w, tag in ((2, "<H"), (4, "<I")):
            pat = b"".join(struct.pack(tag, x) for x in ids)
            hits = []; i = -1
            while len(hits) < 5:
                i = data.find(pat, i + 1)
                if i < 0:
                    break
                hits.append(hex(where(i)))
            print(label, "first", n, "cards as", w * 8, "bit:", hits or "no hit")
    print(label, "hand ids:", lib[:5])

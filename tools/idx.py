import struct, sys
P = r"C:\Program Files (x86)\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion\data.dat"
f = open(P, "rb")
f.seek(0)
head = f.read(12)
print(head)
ents = []
i = 0
while True:
    f.seek(12 + 268 * i)
    e = f.read(268)
    if len(e) < 268:
        break
    name = e[:256]
    if name[0] == 0:
        break
    # "swap hex values of each byte" = nibble swap
    s = bytes(((b & 0xF) << 4) | (b >> 4) for b in name).split(b"\0")[0]
    off, usz, csz = struct.unpack("<III", e[256:268])
    ents.append((s.decode("latin1"), off, usz, csz))
    i += 1
    if i > 20000:
        break
print(len(ents))
import json
json.dump(ents, open("idx.json", "w"))
for e in ents:
    if not e[0].lower().endswith((".bmp", ".wav")):
        print(e)

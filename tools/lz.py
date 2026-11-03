import json, itertools
P = r"C:/Program Files (x86)/Yu-Gi-Oh!/Yu-Gi-Oh!/Joey The Passion/data.dat"
ents = json.load(open("idx.json"))
D = {e[0]: e for e in ents}
F = open(P, "rb")

def raw(n):
    _, o, u, c = D[n]
    F.seek(o)
    return F.read(c), u

def lzss(b, usz, r0, fill, order, minlen=3, off_base=0):
    N = 4096
    win = bytearray([fill]) * N
    r = r0
    out = bytearray()
    i = 0
    while i < len(b) and len(out) < usz:
        fl = b[i]; i += 1
        for k in range(8):
            if len(out) >= usz or i >= len(b):
                break
            bit = (fl >> k) & 1
            if bit:
                c = b[i]; i += 1
                out.append(c); win[r] = c; r = (r + 1) % N
            else:
                if i + 1 >= len(b):
                    break
                x, y = b[i], b[i + 1]; i += 2
                if order == 0:
                    off = x | ((y & 0xF0) << 4); ln = (y & 0x0F) + minlen
                else:
                    off = y | ((x & 0xF0) << 4); ln = (x & 0x0F) + minlen
                for j in range(ln):
                    c = win[(off + j) % N]
                    out.append(c); win[r] = c; r = (r + 1) % N
    return bytes(out)

if __name__ == "__main__":
    b, u = raw("card\\list_card.txt")
    for r0, fill, order in itertools.product((4096 - 18, 0, 4096 - 17), (0x20, 0), (0, 1)):
        o = lzss(b, u, r0, fill, order)
        print(r0, fill, order, len(o), o[:60])

"""Read-only look at a Windows executable: sections, imported DLLs and functions, and interesting strings.
Usage: python tools/pe_info.py "path\\to\\joey_pc.exe"
"""
import re, struct, sys

path = sys.argv[1]
d = open(path, "rb").read()
pe = struct.unpack_from("<I", d, 0x3C)[0]
assert d[pe:pe + 4] == b"PE\0\0"
nsec, = struct.unpack_from("<H", d, pe + 6)
opt_size, = struct.unpack_from("<H", d, pe + 20)
opt = pe + 24
magic, = struct.unpack_from("<H", d, opt)
imagebase, = struct.unpack_from("<I", d, opt + 28)
entry, = struct.unpack_from("<I", d, opt + 16)
dll_char, = struct.unpack_from("<H", d, opt + 70)
print(f"PE32 {'(32-bit)' if magic == 0x10b else '(64-bit)'} image base {imagebase:#x}, entry {entry:#x}, ASLR={'yes' if dll_char & 0x40 else 'no'}, DEP={'yes' if dll_char & 0x100 else 'no'}")
sec_off = opt + opt_size
secs = []
for i in range(nsec):
    name, vsize, va, rsize, roff = struct.unpack_from("<8sIIII", d, sec_off + 40 * i)
    secs.append((name.rstrip(b"\0").decode(), va, vsize, roff, rsize))
    print(f"  section {secs[-1][0]:8} va {va:#08x} size {vsize:#08x} raw {roff:#08x}+{rsize:#x}")

def rva2off(rva):
    for n, va, vs, ro, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rva - va + ro
    return None

imp_rva, imp_size = struct.unpack_from("<II", d, opt + 104)
off = rva2off(imp_rva)
dlls = {}
while off:
    ilt, ts, fwd, name_rva, iat = struct.unpack_from("<IIIII", d, off)
    if not name_rva:
        break
    name = d[rva2off(name_rva):].split(b"\0")[0].decode()
    funcs = []
    t = rva2off(ilt or iat)
    while t:
        v, = struct.unpack_from("<I", d, t)
        if not v:
            break
        if v & 0x80000000:
            funcs.append(f"#{v & 0xFFFF}")
        else:
            funcs.append(d[rva2off(v) + 2:].split(b"\0")[0].decode())
        t += 4
    dlls[name] = funcs
    off += 20
print("\nImported DLLs:")
for n, f in dlls.items():
    print(f"  {n}: {len(f)} functions")
interesting = re.compile(r"(?i)^(send|recv|connect|bind|listen|accept|socket|select|WSA|gethostby|inet_|IsDebuggerPresent|CheckRemoteDebugger|ReadProcessMemory|WriteProcessMemory|VirtualProtect|CreateFile|GetTickCount|timeGetTime|rand|srand|time|DirectPlay|DirectDraw|DirectSound|Direct3D|CRC|Crypt)")
print("\nInteresting imports:")
for n, f in dlls.items():
    hits = [x for x in f if interesting.search(x)]
    if hits:
        print(f"  {n}: {', '.join(hits)}")

strs = set(m.group().decode() for m in re.finditer(rb"[ -~]{6,}", d))
kw = re.compile(r"(?i)(seed|random|shuffle|replay|\.ydr|\.ydc|crc|checksum|version|packet|lan|gameranger|port|ip address|connect|janken|rock|chat|cheat|debug|speedy|-fps|-win|dpfp|guest|host)")
print("\nSelected strings:")
for s in sorted(x for x in strs if kw.search(x))[:90]:
    print("  ", s[:120])

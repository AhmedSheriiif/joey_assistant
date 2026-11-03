"""Read-only snapshot of the memory of the running game (for testing on your own machine, e.g. against Joey the computer).

  python tools/memsnap.py                 writes data/memsnap/<time>.bin plus an index of the regions
  python tools/memsnap.py --find 12,45,7  lists addresses in the latest snapshot where these 16-bit card ids appear in a row

It only opens the process with PROCESS_VM_READ | PROCESS_QUERY_INFORMATION; it never writes to the game.
Use it for your own proof-of-concept tests (own machine, computer opponent); do not run it during matches against other people.
"""
import argparse, ctypes, ctypes.wintypes as wt, glob, json, os, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "data", "memsnap"))
PROCESS_VM_READ, PROCESS_QUERY_INFORMATION = 0x10, 0x400
MEM_COMMIT, PAGE_NOACCESS, PAGE_GUARD = 0x1000, 0x01, 0x100


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p), ("AllocationProtect", wt.DWORD),
                ("RegionSize", ctypes.c_size_t), ("State", wt.DWORD), ("Protect", wt.DWORD), ("Type", wt.DWORD)]


def pid_of(name="joey_pc.exe"):
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        p = [x.strip('"') for x in line.split('","')]
        if len(p) > 1 and p[0].lower() == name:
            return int(p[1])
    raise SystemExit("The game is not running.")


def snapshot():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = wt.HANDLE
    h = k.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid_of())
    if not h:
        raise SystemExit("Could not open the game process (try running the terminal as administrator).")
    os.makedirs(OUT, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    binp = os.path.join(OUT, stamp + ".bin"); regions = []; addr = 0; pos = 0
    mbi = MBI()
    with open(binp, "wb") as f:
        while addr < 0x7FFF0000 and k.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            size = mbi.RegionSize; base = mbi.BaseAddress or 0
            if mbi.State == MEM_COMMIT and not (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) and size <= 256 * 1024 * 1024:
                buf = ctypes.create_string_buffer(size); got = ctypes.c_size_t(0)
                if k.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(got)) and got.value:
                    f.write(buf.raw[:got.value]); regions.append([base, got.value, pos]); pos += got.value
            addr = base + size
    k.CloseHandle(h)
    json.dump(regions, open(binp[:-4] + ".json", "w"))
    print(f"saved {pos / 1e6:.1f} MB in {len(regions)} regions -> {binp}")


def find(ids):
    files = sorted(glob.glob(os.path.join(OUT, "*.bin")))
    if not files:
        raise SystemExit("no snapshot yet")
    binp = files[-1]; regions = json.load(open(binp[:-4] + ".json")); data = open(binp, "rb").read()
    for width, tag in ((2, "<H"), (4, "<I")):
        pat = b"".join(struct.pack(tag, i) for i in ids); i = -1; n = 0
        while True:
            i = data.find(pat, i + 1)
            if i < 0:
                break
            for base, size, p in regions:
                if p <= i < p + size:
                    print(f"{width * 8}-bit ids at 0x{base + i - p:08X}"); break
            n += 1
            if n >= 40:
                print("...more"); break
        print(f"{n} hit(s) for {width * 8}-bit values")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--find", help="comma separated card ids")
    a = ap.parse_args()
    if a.find:
        find([int(x) for x in a.find.split(",")])
    else:
        snapshot()

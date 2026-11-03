"""Fingerprint a Joey the Passion installation so an organiser can check every player runs the same files.
Usage: python tools/verify_install.py ["path to game folder"]   -> prints SHA-256 and size of the program and data files."""
import hashlib, os, sys
GAME = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files (x86)\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion"
for name in ("joey_pc.exe", "data.dat", "Voice.dat"):
    p = os.path.join(GAME, name)
    if not os.path.exists(p):
        print(f"{name}: missing"); continue
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    print(f"{name:12} {os.path.getsize(p):>12} bytes  sha256 {h.hexdigest()}")

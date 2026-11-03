"""Make Joey the Passion quieter and faster: silence Joey's voice lines and blank his reaction pictures.

  python tools/quiet_joey.py            dry run: shows exactly what would change, writes nothing
  python tools/quiet_joey.py --apply    patch the game (the game must be CLOSED); a journal of the original bytes is saved first
  python tools/quiet_joey.py --restore  put every original byte back

What it changes (only inside the files Voice.dat and data.dat in the game folder, never their size):
  1. Voice.dat: the samples of joey_01..joey_52.wav and exodia_*.wav become silence and their header lengths are cut to ~0.05 s.
  2. data.dat: the 17 scripts in j\\bust_up\\*.txt (Joey's win / lose / reaction / summon / start pictures) get every image replaced by null.bmp,
     the blank image the game itself uses; the scripts are stored uncompressed in place (same offset, never longer than before).
Sound effects, music and the rest of the game are untouched. The journal is data/quiet_joey_backup/ (about 8 MB).
If the game ever misbehaves, run --restore. Launch flags that also help: add  -speedy  (faster animations) to the game shortcut.
"""
import argparse, json, os, re, struct, subprocess, sys

GAME = r"C:\Program Files (x86)\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion"
HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.abspath(os.path.join(HERE, "..", "data", "quiet_joey_backup"))
JOURNAL_JSON = os.path.join(BACKUP, "journal.json"); JOURNAL_BIN = os.path.join(BACKUP, "journal.bin")
BS = chr(92)
EXPECTED_SIZE = {"data.dat": 318892812, "Voice.dat": None}


def lzss(b, usz, r0=4078, fill=32):
    """The game's LZSS (flag byte LSB first, 12-bit offset + 4-bit length, window starts at 4078)."""
    N = 4096; win = bytearray([fill]) * N; r = r0; out = bytearray(); i = 0
    while i < len(b) and len(out) < usz:
        fl = b[i]; i += 1
        for k in range(8):
            if len(out) >= usz or i >= len(b):
                break
            if (fl >> k) & 1:
                c = b[i]; i += 1; out.append(c); win[r] = c; r = (r + 1) % N
            else:
                if i + 1 >= len(b):
                    break
                x, y = b[i], b[i + 1]; i += 2
                off = x | ((y & 0xF0) << 4); ln = (y & 0x0F) + 3
                for j in range(ln):
                    c = win[(off + j) % N]; out.append(c); win[r] = c; r = (r + 1) % N
    return bytes(out)


def lzss_encode(data, r0=4078, fill=32):
    """Greedy encoder for the game's LZSS (inverse of lzss())."""
    N = 4096; win = bytearray([fill]) * N; r = r0; out = bytearray(); i = 0
    while i < len(data):
        flag = 0; chunk = bytearray()
        for k in range(8):
            if i >= len(data):
                break
            best_len, best_off = 0, 0
            for off in range(N):                       # brute force is fine for scripts of a few hundred bytes
                ln = 0
                while ln < 18 and i + ln < len(data) and win[(off + ln) % N] == data[i + ln]:
                    # a match may not run into bytes that are written during the copy unless they equal what we copy
                    ln += 1
                if ln > best_len:
                    best_len, best_off = ln, off
            if best_len >= 3:
                chunk += bytes([best_off & 0xFF, ((best_off >> 4) & 0xF0) | (best_len - 3)])
                for j in range(best_len):
                    win[r] = data[i + j]; r = (r + 1) % N
                i += best_len
            else:
                flag |= 1 << k; chunk.append(data[i]); win[r] = data[i]; r = (r + 1) % N; i += 1
        out.append(flag); out += chunk
    return bytes(out)


def rewrite_script(text):
    """Every image name becomes null.bmp (the blank image the game itself uses); comments (Shift-JIS notes) are dropped so the
    uncompressed script fits in the space the compressed one used."""
    # Version 2: the first picture of a script (and any picture whose name ends in '#', i.e. colour-keyed backgrounds) becomes the game's
    # transparent 'dummy#.bmp' (this is exactly how the game's own do-nothing script activate.txt starts); every other picture becomes the
    # 1x1 'null.bmp'. Version 1 used null.bmp for the first picture too, which the game drew as a dark panel.
    # Comment text is cut to a bare '//' (a blank line would be read as a section separator).
    pic = re.compile(rb"[^\s/\\]+(?:/[^\s/\\]+)*\.(?:bmp|yga)")
    first = [True]
    def sub(m):
        name = m.group(0)
        out = b"dummy#.bmp" if (first[0] or name.lower().endswith(b"#.bmp")) else b"null.bmp"
        first[0] = False
        return out
    body = re.sub(rb"//[^\r\n]*", b"//", text)
    return pic.sub(sub, body)


def read_index(path):
    f = open(path, "rb"); ents = []; i = 0
    while True:
        f.seek(12 + 268 * i); e = f.read(268)
        if len(e) < 268 or e[0] == 0:
            break
        name = bytes(((b & 15) << 4) | (b >> 4) for b in e[:256]).split(b"\0")[0].decode("latin1")
        off, usz, csz = struct.unpack("<III", e[256:268])
        ents.append(dict(name=name, off=off, usz=usz, csz=csz, rec=12 + 268 * i)); i += 1
    f.close()
    return ents


def game_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq joey_pc.exe"], capture_output=True, text=True).stdout
    return "joey_pc.exe" in out


def plan():
    voice = os.path.join(GAME, "Voice.dat"); data = os.path.join(GAME, "data.dat")
    changes = []                         # dicts: file, offset, new(bytes), note
    # ---- voices
    vf = open(voice, "rb")
    for e in read_index(voice):
        base = e["name"].lower().split(BS)[-1]
        if not (re.fullmatch(r"joey_\d+\.wav", base) or base.startswith("exodia_")):
            continue
        vf.seek(e["off"]); raw = vf.read(e["usz"])
        if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
            continue
        # find the 'data' chunk
        p = raw.find(b"data")
        if p < 0:
            continue
        keep = 2048 - (2048 % 4)
        dsize = struct.unpack_from("<I", raw, p + 4)[0]
        new = bytearray(raw)
        struct.pack_into("<I", new, 4, p + 8 + keep - 8)          # RIFF size
        struct.pack_into("<I", new, p + 4, keep)                  # data size
        new[p + 8:] = b"\0" * (len(new) - (p + 8))                # silence everywhere
        changes.append(dict(file="Voice.dat", offset=e["off"], old=raw, new=bytes(new), note=f"voice {base} ({dsize} -> {keep} bytes of audio)"))
    vf.close()
    # ---- bust-up scripts
    df = open(data, "rb")
    for e in read_index(data):
        n = e["name"].lower()
        if not (n.startswith("j" + BS + "bust_up" + BS) and n.endswith(".txt") and BS not in n[len("j" + BS + "bust_up" + BS):]):
            continue
        df.seek(e["off"]); raw = df.read(e["csz"])
        text = lzss(raw, e["usz"]) if e["csz"] != e["usz"] else raw
        new = rewrite_script(text)
        if new == text.replace(b"\r\n\r\n", b"\r\n") or all(l.strip().startswith((b"null.bmp", b"dummy#.bmp", b"//")) or not l.strip()
                                                              for l in text.splitlines()):
            continue                                       # already shows nothing (activate.txt): leave it alone
        comp = lzss_encode(new)
        assert lzss(comp, len(new)) == new, "LZSS round trip failed"
        if len(comp) > e["csz"]:
            raise SystemExit(f"{e['name']}: replacement does not fit ({len(comp)} > {e['csz']})")
        rec = dict(file="data.dat", offset=e["off"], old=raw, new=comp, note=f"script {e['name'].split(BS)[-1]} ({e['usz']} -> {len(new)} bytes, stored {e['csz']} -> {len(comp)})",
                   rec=e["rec"], rec_old=None, usz_new=len(new), csz_new=len(comp))
        changes.append(rec)
    df.close()
    return changes


def apply(changes):
    os.makedirs(BACKUP, exist_ok=True)
    if os.path.exists(JOURNAL_JSON):
        raise SystemExit("A journal already exists: run --restore first (or delete data/quiet_joey_backup) before applying again.")
    journal = []; blob = bytearray()
    handles = {}
    for c in changes:
        f = handles.setdefault(c["file"], open(os.path.join(GAME, c["file"]), "r+b"))
        entry = dict(file=c["file"], offset=c["offset"], length=len(c["old"]), bin_off=len(blob), note=c["note"])
        blob += c["old"]
        if "rec" in c:
            f.seek(c["rec"] + 256); entry["rec"] = c["rec"]; entry["rec_old"] = f.read(12).hex()
        journal.append(entry)
    open(JOURNAL_BIN, "wb").write(bytes(blob)); json.dump(journal, open(JOURNAL_JSON, "w"), indent=1)   # journal first, patch second
    for c in changes:
        f = handles[c["file"]]
        if "rec" in c:                                                  # scripts become uncompressed: usz = csz = new length
            f.seek(c["rec"] + 256); off, usz, csz = struct.unpack("<III", f.read(12))
            f.seek(c["rec"] + 256); f.write(struct.pack("<III", off, c["usz_new"], c["csz_new"]))
        f.seek(c["offset"]); f.write(c["new"])
    for f in handles.values():
        f.close()
    print(f"patched {len(changes)} entries. Journal saved in {BACKUP}. Start the game and test; use --restore to undo.")


def restore():
    if not os.path.exists(JOURNAL_JSON):
        raise SystemExit("nothing to restore (no journal)")
    journal = json.load(open(JOURNAL_JSON)); blob = open(JOURNAL_BIN, "rb").read(); handles = {}
    for e in journal:
        f = handles.setdefault(e["file"], open(os.path.join(GAME, e["file"]), "r+b"))
        f.seek(e["offset"]); f.write(blob[e["bin_off"]:e["bin_off"] + e["length"]])
        if "rec" in e:
            f.seek(e["rec"] + 256); f.write(bytes.fromhex(e["rec_old"]))
    for f in handles.values():
        f.close()
    os.remove(JOURNAL_JSON); os.remove(JOURNAL_BIN)
    print("restored the original game files")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); ap.add_argument("--restore", action="store_true")
    ap.add_argument("--reapply", action="store_true", help="restore the originals, then apply the current version of the patch")
    a = ap.parse_args()
    if a.restore or a.apply or a.reapply:
        if game_running():
            raise SystemExit("The game is running. Close Yu-Gi-Oh! Power of Chaos first, then run this again.")
    if a.restore:
        restore(); sys.exit()
    if a.reapply:
        if os.path.exists(JOURNAL_JSON):
            restore()
        a.apply = True
    ch = plan()
    v = [c for c in ch if c["file"] == "Voice.dat"]; s = [c for c in ch if c["file"] == "data.dat"]
    print(f"{len(v)} voice files and {len(s)} reaction scripts would be changed:")
    for c in ch[:6] + ch[-4:]:
        print("  ", c["note"])
    if a.apply:
        apply(ch)
    else:
        print("\nDry run only. Close the game, then run with --apply (and --restore to undo).")

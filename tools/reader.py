"""Read the game screen: recognise the cards in your hand by matching them with the game's own card art.

Pipeline: screen.py captures the game window (even when covered) -> this module finds the cards -> advisor/lookahead use the names.
The game draws an 800x600 picture in the top-left of its window. Card images (200x290) come from data.dat.
Run `python tools/reader.py --build` once to extract the templates, then `python tools/reader.py` to read the hand on screen.
"""
import argparse, io, json, os, re, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
TPL = os.path.join(ROOT, "data", "card_templates.npz")
CARD_W, CARD_H = 95, 138                       # size of a hand card on the 800x600 screen
HAND_Y = 529                                   # top edge of the hand cards
VIS_W, VIS_H = 80, 71                          # the part of a card that is not covered by its neighbour / the screen edge


def build():
    sys.path.insert(0, HERE); os.chdir(HERE)
    import lz, csv
    BS = chr(92)
    lb, lu = lz.raw("card" + BS + "list_card.txt")
    txt = lz.lzss(lb, lu, 4078, 32, 0).decode("latin1")
    ents = json.load(open(os.path.join(HERE, "idx.json")))
    have = {e[0].lower(): e for e in ents}
    play = {r["name"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "cards_game.csv"), encoding="utf8"))}
    names, imgs, seen = [], [], set()
    for m in re.finditer(r"//\t(.*?)\r?\n//\t(\d+):\[(\d+)\]\r?\n(\S+\.bmp)", txt):
        name, bmp = m.group(1).strip(), m.group(4).strip()
        if name not in play or name in seen:
            continue
        key = ("card" + BS + bmp).lower()
        if key not in have:
            continue
        seen.add(name)
        raw, usz = lz.raw(have[key][0])
        im = Image.open(io.BytesIO(raw)).convert("RGB").resize((CARD_W, CARD_H), Image.LANCZOS)
        a = np.asarray(im)[:VIS_H, :VIS_W]
        names.append(name); imgs.append(a)
    np.savez_compressed(TPL, names=np.array(names), imgs=np.stack(imgs))
    print(len(names), "card templates saved to", TPL)


_T = {}
def templates():
    if not _T:
        z = np.load(TPL, allow_pickle=False)
        names = z["names"]; imgs = z["imgs"].astype(np.float32)
        flat = imgs.reshape(len(names), -1)
        flat = flat - flat.mean(axis=1, keepdims=True)
        flat /= (np.linalg.norm(flat, axis=1, keepdims=True) + 1e-6)
        _T["names"] = names; _T["flat"] = flat
    return _T["names"], _T["flat"]


def match_patch(patch):
    """Best card for a (VIS_H, VIS_W, 3) patch: returns (name, score, second_score)."""
    names, flat = templates()
    v = patch.astype(np.float32).reshape(-1)
    v = v - v.mean(); v /= (np.linalg.norm(v) + 1e-6)
    sc = flat @ v
    i = np.argsort(-sc)[:2]
    return str(names[i[0]]), float(sc[i[0]]), float(sc[i[1]])


def read_hand(img, y0=HAND_Y, x_range=(256, 700)):
    """Find the hand cards in an 800x600 screen image (PIL). Returns [(name, score, x)] left to right."""
    a = np.asarray(img.convert("RGB"))
    names, flat = templates()
    # score of the best template at every x (small y jitter), then pick separated peaks
    best = {}
    for x in range(x_range[0], x_range[1]):
        top = (None, -1)
        for dy in (-1, 0, 1):
            p = a[y0 + dy:y0 + dy + VIS_H, x:x + VIS_W]
            if p.shape[:2] != (VIS_H, VIS_W):
                continue
            n, s, s2 = match_patch(p)
            if s > top[1]:
                top = (n, s)
        best[x] = top
    peaks = []
    for x in sorted(best, key=lambda k: -best[k][1]):
        if best[x][1] < 0.55:
            break
        if all(abs(x - px) >= 60 for px, _, _ in peaks):
            peaks.append((x, best[x][0], best[x][1]))
    peaks.sort()
    return [(n, round(s, 3), x) for x, n, s in peaks]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="extract card templates from data.dat")
    ap.add_argument("--image", help="read this screenshot instead of capturing the game window")
    a = ap.parse_args()
    if a.build:
        build(); sys.exit()
    if a.image:
        img = Image.open(a.image)
    else:
        sys.path.insert(0, HERE)
        import screen
        w = screen.find_window()
        img, _ = screen.grab_window_printwindow(w[0])
    for n, s, x in read_hand(img):
        print(f"x={x:3d}  {n}  (score {s})")

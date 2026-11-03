"""Copy the card pictures from YOUR installed game into the web project's local art folder (private use only).

  python tools/export_art.py            writes joey_web_game/art/<card id>.jpg (200x290) and art/index.json

The pictures are Konami's. They are extracted from your own copy of the game for a private prototype; keep the art folder out of anything you publish.
"""
import csv, io, json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "joey_web_game", "art"))
BS = chr(92)


def main():
    sys.path.insert(0, HERE); os.chdir(HERE)
    import lz
    lb, lu = lz.raw("card" + BS + "list_card.txt")
    txt = lz.lzss(lb, lu, 4078, 32, 0).decode("latin1")
    ents = json.load(open(os.path.join(HERE, "idx.json")))
    have = {e[0].lower(): e for e in ents}
    ids = {int(r["deck_id"]) for r in csv.DictReader(open(os.path.join(HERE, "..", "data", "cards_game.csv"), encoding="utf8"))}
    os.makedirs(OUT, exist_ok=True)
    done = []
    for m in re.finditer(r"//\t(.*?)\r?\n//\t(\d+):\[(\d+)\]\r?\n(\S+\.bmp)", txt):
        cid, bmp = int(m.group(3)), m.group(4).strip()
        if cid not in ids:
            continue
        key = ("card" + BS + bmp).lower()
        if key not in have:
            continue
        raw, usz = lz.raw(have[key][0])
        Image.open(io.BytesIO(raw)).convert("RGB").resize((200, 290), Image.LANCZOS).save(os.path.join(OUT, f"{cid}.jpg"), quality=88)
        done.append(cid)
    json.dump(sorted(set(done)), open(os.path.join(OUT, "index.json"), "w"))
    open(os.path.join(OUT, "README.txt"), "w").write("Card pictures extracted from a private copy of the game. Do not publish or redistribute this folder.\n")
    print(len(set(done)), "pictures written to", OUT)


if __name__ == "__main__":
    main()

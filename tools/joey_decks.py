"""Extract Joey's AI decks (j\\file\\*.ydc) from the game's data.dat and write knowledge/09_joey_decks.md."""
import collections, csv, json, os, struct, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DAT = r"C:\Program Files (x86)\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion\data.dat"
IDX = os.environ.get("JOEY_IDX", os.path.join(ROOT, "tools", "idx.json"))


def build_index():
    f = open(DAT, "rb"); ents = []; i = 0
    while True:
        f.seek(12 + 268 * i); e = f.read(268)
        if len(e) < 268 or e[0] == 0:
            break
        name = bytes(((b & 15) << 4) | (b >> 4) for b in e[:256]).split(b"\0")[0].decode("latin1")
        off, usz, csz = struct.unpack("<III", e[256:268]); ents.append((name, off, usz, csz)); i += 1
    return ents


def main():
    cards = {}
    with open(os.path.join(ROOT, "data", "cards_all.csv"), encoding="utf8") as fh:
        for r in csv.DictReader(fh):
            cards[int(r["deck_id"])] = r["name"]
    ents = build_index()
    f = open(DAT, "rb")
    out = ["# Joey's AI decks (extracted from data.dat, `j\\file\\*.ydc`)\n",
           "Names: `cpu_NNN` = early decks (star level = first digit of NNN); `ful_<level><theme>` = full-power sets for stars 0-3 of the "
           "high-level pool. Theme codes: ge1/ge2 general, dec/gam (draw/luck), fus fusion, hik/hnd hand, ins insect, mix mixed, red Red-Eyes/dragon, "
           "too Toon, uij/umi Umi/water, val Valkyrion/Magnet, all/exo/grv/yam special (Exodia, graveyard, Yami).\n",
           "The 9-star full-power list in knowledge/02_tips.md came from a 2004 FAQ; this file is read straight from your game.\n"]
    for name, off, usz, csz in ents:
        if not (name.startswith("j\\file\\") and name.endswith(".ydc")):
            continue
        f.seek(off); d = f.read(csz)
        p = 8; lists = []
        while p + 2 <= len(d):
            n = struct.unpack_from("<H", d, p)[0]; p += 2
            lists.append(list(struct.unpack_from("<%dH" % n, d, p))); p += 2 * n
        main_deck = collections.Counter(lists[0])
        out.append(f"\n## {os.path.basename(name)[:-4]}  ({len(lists[0])} cards, fusion {len(lists[1]) if len(lists) > 1 else 0})")
        out.append(", ".join(f"{v}x {cards.get(k, '#' + str(k))}" for k, v in sorted(main_deck.items(), key=lambda x: (-x[1], cards.get(x[0], '')))))
        if len(lists) > 1 and lists[1]:
            out.append("Fusion: " + ", ".join(f"{v}x {cards.get(k, '#' + str(k))}" for k, v in collections.Counter(lists[1]).most_common()))
    open(os.path.join(ROOT, "knowledge", "09_joey_decks.md"), "w", encoding="utf8").write("\n".join(out) + "\n")
    print("decks written")


if __name__ == "__main__":
    main()

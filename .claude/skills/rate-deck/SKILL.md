---
name: rate-deck
description: Rate a Yu-Gi-Oh! Power of Chaos deck (.ydc file, or a deck stored in a .ydr replay) and recommend cuts and additions. Use when the user asks to check, rate, review, improve or compare a deck, or gives a .ydc path.
---

# Rate a deck

1. Run the tool (from the project root, `joey_assistant`):
   `python tools/rate_deck.py "<path to .ydc>"`
   - a deck inside a replay: `python tools/rate_deck.py REPLAY.ydr --side winner|loser|first|second`
   - the game's own folder is `%APPDATA%\Yu-Gi-Oh! Power of Chaos Common`; add `--common NAME.ydc` to look there.
   - `--json` for machine-readable output.
2. Read the report, then give the user YOUR opinion, not a paste of the report:
   - **Illegal / dead / fighting cards first** (searchers without targets, Fusion monsters that cannot be made, Royal Decree with its own Traps).
   - Then structure (removal, engine, defence, finishers against the champion ranges) and the opening-hand numbers.
   - Then concrete swaps (cut X, add Y) that keep the deck's plan.
3. Judge the **plan**, not only the number. The model (`data/models/deck_model.json`) learned which cards winners' decks contain, so it under-rates lock and combo decks and cannot score cards it has seen in fewer than 8 recorded decks (Relinquished, Thousand-Eyes cards, Fusion Sage ...). Say so when the deck is such a deck, and use the card texts in `data/cards_all.csv` plus `knowledge/12_combo_ideas.md` for the plan.
4. Check legality against the game's limits (the tool does: `joey_web_game/data/banlist.json`, read from joey_pc.exe) and the pool: only cards flagged `playable` in `data/cards_all.csv` exist. Cards from later sets (Metamorphosis, Tsukuyomi, Book of Moon ...) are NOT in the game.
5. If asked to build a better deck, write it with the helper pattern in `tools/build_deck.py` (ids from `cards_all.csv` `deck_id`, header `01f312005754cb3f`) into `champion_decks/` and rate it with this tool before presenting it.

What we already know (read when advising): `knowledge/13_how_to_play_and_win.md` (what wins), `11_model_findings.md` (cards that help or hurt, and the limits of the data), `17_best_deck.md` (the recommended list), `10_champion_decks.md`.

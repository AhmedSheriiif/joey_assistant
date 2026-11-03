---
name: rate-replay
description: Rate a Yu-Gi-Oh! Power of Chaos replay (.ydr), say what each player did well or badly, what the user could do better, and learn from it (add it to the dataset and retrain). Use when the user gives a replay, asks "what went wrong", "analyse this game", "rate my play" or wants insights about a player.
---

# Rate a replay

1. Run the tool (from the project root, `joey_assistant`):
   `python tools/rate_replay.py "<replay.ydr>" --me YOU|OPP`
   - In a replay file the decoder labels the SECOND deck list `YOU` and the first `OPP`; that is not necessarily the user. Known files are in `data/user_sides.json` (no_bas_1-6 = `OPP`, anas1 and 0cards_deck_win = `YOU`). If the side is unknown, ask the user, or rate both.
   - `--learn` copies the replay into `learned_replays/`, records the side in `data/user_sides.json` and runs `tools/ingest.py` (rebuilds the dataset and `knowledge/07_learned_patterns.md`).
   - `--learn --retrain` also retrains the deck, position and behaviour models (slow) and refreshes the benchmark cache.
2. The report covers, for each player: result, style, damage sources, life-point race, opening turn, tempo against the winners and losers of the 240 recorded games, deck rating (`tools/rate_deck.py`), mistakes the log can show (free attacks not taken, possible lethal, turns that ended inside his burst range, useful cards left in hand or Set cards unused at the loss), and the big turns (3000+ damage) with their cards.
3. Turn it into coaching, in this order:
   - **The turning point**: the turn the life-point lead changed for good, and why (read the story in `data/replays/*/<name>.txt`, which has `YOU hand [exact]` lines).
   - **What the user could do better**: pick the 2-3 items that cost the most; check each one in the story text before stating it (the tool flags candidates, e.g. a "free attack" may have been blocked by a Set Swords of Revealing Light).
   - **What the other player teaches**: their line, deck and timing; say whether it matches the known frames in `knowledge/13_how_to_play_and_win.md` section 4, or is NEW (then add it to `knowledge/12_combo_ideas.md`).
4. Be honest about limits: hands are exact only until a search or shuffle effect, the field is rebuilt from the log, and the log shows what was played, not what was held back. Do not claim to know a player's intent.
5. To learn from it, offer `--learn` (and `--retrain` when several new replays were added), then read `knowledge/07_learned_patterns.md` / `11_model_findings.md` and fold real new findings into `knowledge/06_playbook.md`. Losses and new opponents are the most valuable additions.

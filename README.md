# Joey the Passion assistant

Goal: an assistant that helps during Yu-Gi-Oh! Power of Chaos: Joey the Passion duels, learning from your replays.

## Layout
- `knowledge/01-06` rules, tips, card pool, your decks, replay format, playbook (hand-written + researched)
- `knowledge/07_learned_patterns.md` auto-generated statistics from all replays
- `knowledge/08_meta_and_strategy.md` the tournament meta and strategy rules distilled from 236 replays
- `knowledge/09_joey_decks.md` Joey's AI decks (weak; reference only)
- `knowledge/10_champion_decks.md` + `champion_decks/*.ydc` the proven tournament decks, loadable in the game
- `knowledge/11_model_findings.md` trained models: card values, hidden gems, how champions play (corrects 08)
- `data/models/` saved models and tables
- `data/cards_all.csv` all 1114 database entries (771 playable, flagged in the `playable` column) (name, level, attribute, type, ATK/DEF, text), extracted from the game's data.dat
- `data/replays/*.txt` readable story of each replay; `data/dataset/replays.jsonl` structured events
- `tools/replay_decode.py` single replay decoder; `tools/ingest.py` batch pipeline; other scripts rebuild the card data

## Adding replays (the learning loop)
1. Save replays in the game (they land in `%APPDATA%\Yu-Gi-Oh! Power of Chaos Common`), or drop them into `My Hand` / `My opp's Hand` in this folder.
2. Run `python tools/ingest.py [extra_folder]` (duplicates are detected and skipped).
3. Retrain with `python tools/train_deck.py`, `python tools/train_position.py`, `python tools/train_behavior.py`, then read `knowledge/11_model_findings.md` and `knowledge/07_learned_patterns.md`; ask Claude to fold new findings into `06_playbook.md`.

Include **losses** and different opponents/difficulty levels: a dataset of only wins can't show what goes wrong.

## Which side is you?
In a replay file the decoder labels the second deck list 'YOU' and the first 'OPP'. That is not necessarily the user. Put the
side that is you into `data/user_sides.json` (known: anas1 and 0cards_deck_win = YOU, no_bas_1-6 = OPP); stories for those
files are relabelled so that YOU is the user.

## Hand tracking in the logs
Each story line for a card played from the hand ends with `[card k of N in hand]`; each turn shows hand size and library size.
The log does not list drawn cards, but the game's shuffle is deterministic, so `tools/hands.py` rebuilds each player's shuffled deck from the replay seed. Stories show
`YOU hand [exact]: ...` and `OPP (recorder) hand ...` at every turn start. Exact until a search/shuffle effect; see `knowledge/05_replay_format.md`.
`python tools/validate_hands.py` re-checks the method (89% of player-sides consistent).

## Get the decks out of a replay
`python tools/replay_decks.py REPLAY.ydr` prints both decks (main, fusion, side) with card names and says which side won.
Add `--only winner` for just the winner's deck, a folder instead of a file for many replays, and `--export OUTDIR` to write
the decks as `.ydc` files you can copy into the game's Common folder and load in the deck editor.

## Play advisor (first version)
`python tools/advisor.py --hand "card1, card2, ..." --lp-me 8000 --lp-opp 8000 --mon-me 0 --mon-opp 1 --turn 5` ranks the next action
from the winners' decisions (hand + board). See `knowledge/14_hand_decisions.md`. Retrain after adding replays: `python tools/ingest.py` then `python tools/train_policy.py`.

## Lookahead (burst planner + danger check)
`python tools/advisor.py --hand ... --my-monsters ... --opp-monsters ... --lp-me ... --lp-opp ... --opp-st N` first checks whether you have lethal this turn,
then how dangerous his next turn is, then shows what winners usually do. Details: `knowledge/15_lookahead.md`.

## Quiet Joey (no voices, no reaction pictures)
`python tools/quiet_joey.py` (dry run) -> close the game -> `python tools/quiet_joey.py --apply`; undo with `--restore`.
It silences Joey's voice lines and blanks his win / lose / reaction pictures, keeping a journal of the original bytes in `data/quiet_joey_backup/`.
Add `-speedy` to the game shortcut for faster animations.

## Screen reader (work in progress)
`python tools/reader.py --build` once, then `python tools/reader.py` reads the cards in your hand from the running game window
(captured even when the window is covered, `tools/screen.py`) by matching the game's own card art. Fields and life points are next.

## Coach tools (rate a deck, rate a replay)
- `python tools/rate_deck.py DECK.ydc` rates a deck 0-100 (legality against the game's limits, deck-model score and percentile, structure, dead cards, simulated opening hands) and recommends cuts and additions. Also `REPLAY.ydr --side winner|loser|first|second`.
- `python tools/rate_replay.py REPLAY.ydr --me YOU|OPP` rates both players (style, damage sources, life-point race, tempo against the recorded winners and losers, free attacks not taken, possible lethal, turns left inside his burst range, big turns with their cards) and says what could be better. `--learn` adds the replay to the dataset (`learned_replays/`, then `tools/ingest.py`), `--retrain` retrains the models.
- Claude skills for both: `.claude/skills/rate-deck`, `.claude/skills/rate-replay`. Notes on the Thousand-Eyes lock: `knowledge/21_restrict_lock.md`; the deck itself: `champion_decks/Restrict_Lock.ydc`.

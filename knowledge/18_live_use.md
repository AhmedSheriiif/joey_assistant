# Using the advisor during a duel: options and plan

## What the advisor needs each time it is asked
Your hand, both fields (monster names and positions), both life points, how many Set Spell/Trap cards each side has, the monsters in his Graveyard, and whether you already used your Normal Summon. It answers in under a second.

## Three moments per turn (not continuous)
1. **After your draw (start of Main Phase 1):** kill check, then ranked plays.
2. **Before the Battle Phase:** trap risk, which cards to clear first, attack with the boosted monster first (the order cost 500 life in `no_bas_3`).
3. **Before you end the turn:** the danger check. This is the one that would have saved `no_bas_3`.
Plus on his turn: remember what he has shown (cards seen so far), and whether to spend Waboku / Kuriboh / Mirror Force.

## Ways to feed it the state
| Mode | How it works | Good | Bad |
|---|---|---|---|
| **A. Quick entry** | A small companion window or terminal: you type short commands (`hand ...`, `me ...`, `opp ...`, `lp 6200 2300`), with name auto-complete from your deck list. It remembers what you drew, tracks your library and the cards he has shown. | Fast to build, offline, exact, no recognition errors | Typing takes time each turn |
| **B. Screenshot reading** | You ask ("advise"); I take a screenshot of the game window (computer use), read the hand, fields and life points, and run the advisor. | No typing | 10-30 seconds a call; may misread a card name or ATK; needs the game window visible; only works while this session is attached to your desktop |
| **C. Reading game memory/network** | Not recommended: fragile, may be treated as cheating by the game or a tournament. | | |
Recommended: **B for convenience with A as the fallback** (and the same state format for both).

## Improvements worth doing before relying on it
1. Make the field tracking reliable (positions, equips, which monsters came back after effects); at the moment it is only approximate after complex effects.
2. Opponent memory: load his deck from game 1 of the match with `tools/replay_decks.py`, then count which of his cards remain (which traps and which Snatch Steal / Monster Reborn are left).
3. Attack-order advice (boosted monster first, bait with the weakest) and a "play around Torrential / Mirror Force" check.
4. Calibrate on your own past turns with `tools/audit_replay.py`: it should flag your real kills and the dangers that really came.

## Fair-play check
You mentioned a tournament with a prize. Many events do not allow outside assistance during a game. Check the rules with the organisers before using any live help there; use it freely in practice, ladder and replay review.

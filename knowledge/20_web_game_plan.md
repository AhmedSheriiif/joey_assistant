# Plan: our own web game based on Power of Chaos: Joey the Passion

## What we already have to build from
- **Rules and flow:** 6 phases, summons, positions, battle damage, hand limit, LP 8000 (`01_rulings.md`), plus the game's own tutorial text still to be mined (`data.dat` j\tutorial, 627 UI strings).
- **Card data:** 771 playable cards with name, level, attribute, type, ATK/DEF, text and passcode (`data/cards_game.csv`); Joey's 58 AI decks; 9 champion decks and the best deck (`champion_decks/`).
- **A test oracle:** 240 tournament replays as full event logs (draws, summons, attacks, damage, life points), plus the exact shuffle (`tools/hands.py`). A new engine can be checked by replaying the recorded decisions and comparing damage and life points event by event.
- **Strategy tools:** the advisor and lookahead can become the computer opponent and hint system.

## Scope that matters
Across the replays only **223 of the 771 cards** appear, and **101 cards cover 95%** of deck slots (161 cover 99%). Card kinds among them: 105 Spell/Trap, 78 monsters with continuous or triggered effects, 22 with Special Summon effects, 18 flip effects. So a first playable version needs about 100 card scripts, not 771.

## Architecture
- **Engine (TypeScript, runs in the browser and on a server):** pure state machine `state + action -> new state + event log`, deterministic from a seed. Event log in the same shape as the replay events so old replays can be viewed and the engine can be tested against them.
- **Effects as data + small scripts:** most cards reduce to a few primitives (destroy, draw, special summon, equip modifier, LP change, control change, flip trigger, continuous modifier). Write those once, then one short definition per card.
- **Chain/timing:** start with a simple response window (each side may respond once per trigger), as the original game does.
- **Server:** authoritative game state; each client gets only its own hand and the public board; shuffle by commit-reveal; Rock-Paper-Scissors committed and revealed by the server. This removes the information leak found in the original.
- **Client:** HTML canvas or DOM board with drag-and-drop, hand/field/graveyard, life points, chain prompts; the advisor runs as an optional hint panel.
- **AI opponent:** use Joey's 58 decks plus the champion decks, driven by the advisor's policy and lookahead.

## Assets and legal note
The card art, music and voices in `data.dat` / `Voice.dat` belong to Konami. For a private prototype using your own copy is fine; for anything public we should use original art and names or a licensed set. Card names and rules text are the part to check with a lawyer before publishing.

## Milestones
1. Engine core: deck, shuffle, turns, summon/set/flip/attack, LP, hand limit; replay viewer for `.ydr` files.
2. 30 most-used card scripts (Scapegoat, MST, Sangan, Mystic Tomato, Nimble Momonga, Man-Eater Bug, Penguin Soldier, Graceful Charity, Pot of Greed, Monster Reborn, Premature Burial, Mirror Force, Torrential Tribute, Magic Cylinder, Swords, Giant Trunade, United We Stand, Cannon Soldier, Amazon Archer, ...). Verify against replays.
3. Single-player vs AI with the best deck; deck editor with limit list.
4. Two-player online with the secure protocol; ladder and replay storage.
5. Remaining effects up to 100 cards, then up to 160.

## What I can start now
A TypeScript engine skeleton with the card table, turn/phase machine, battle rules and the replay-verification harness (feed a `.ydr` and compare LP and damage).

# Recommended deck (all cards allowed except Delinquent Duo, The Forceful Sentry, Confiscation)

File: `champion_decks/Best_Deck.ydc` (copy to `%APPDATA%\Yu-Gi-Oh! Power of Chaos Common`). Builder and checks: `tools/build_deck.py`.
Assumption: the game's usual copy limits still apply (the replays show the limited cards at 1 copy, Morphing Jar and Nobleman at 2). I checked that no card exceeds what was ever seen in the replays.

## Main deck (40): 19 monsters, 21 spells/traps
Monsters: 3x Mystic Tomato, 3x Nimble Momonga, 2x Penguin Soldier, 2x Man-Eater Bug, Cannon Soldier, Crass Clown, Sangan, Witch of the Black Forest, Jinzo, Amazon Archer, Kuriboh, Morphing Jar, Magician of Faith.
Spells/traps: 3x Scapegoat, 2x Mystical Space Typhoon, Giant Trunade, Graceful Charity, Pot of Greed, Monster Reborn, Premature Burial, Call of the Haunted, United We Stand, Snatch Steal, Change of Heart, Dark Hole, Raigeki, Heavy Storm, Torrential Tribute, Mirror Force, Magic Cylinder, Swords of Revealing Light.
Fusion deck (free): Blue-Eyes Ultimate Dragon, St. Joan, The Last Warrior from Another Planet, Alligator's Sword Dragon, Thousand-Eyes Restrict.
Side deck (15): Waboku, Imperial Order, Mirror Wall, 2x Nobleman of Crossout, 2x Dust Tornado, Ceasefire, Ring of Destruction, 2x Rush Recklessly, Crush Card, Kunai with Chain, Wall of Illusion, Fissure.

## Why these cards (each backed by the replay data)
- **Bodies that replace themselves (11 cards):** Mystic Tomato x3 (66% of decks containing it won, top coefficient), Nimble Momonga x3 (heals 1000 and rebuys itself), Penguin Soldier x2 (best deck-model coefficient, bounces two monsters), Man-Eater Bug x2 (kills any monster face-down or not), Sangan, Witch, Crass Clown (bounce, best play impact after Cannon Soldier).
- **Finishers:** Cannon Soldier (strongest single card: 6 of 9 champions, 59-16 deck record, 7+ points of win chance per turn), Amazon Archer (lift 6.0 in big-damage turns), United We Stand, Change of Heart / Snatch Steal (the Spell OTK: your own wins in `no_bas`).
- **Reset and clear:** Raigeki, Dark Hole, Heavy Storm, Giant Trunade, MST x2 (9/9 champions), Man-Eater Bug.
- **Engine:** Pot of Greed, Graceful Charity, Morphing Jar, Magician of Faith (recycles the one-shot spells), Monster Reborn, Premature Burial, Call of the Haunted.
- **Defence in the same cards:** Torrential Tribute, Mirror Force, Magic Cylinder (reactive damage), Swords of Revealing Light, Scapegoat x3 (blockers and burn fuel), Kuriboh.
- **Left out on purpose:** Ring of Destruction, Ceasefire, Imperial Order (weak coefficients; kept in the side deck), Nobleman (side), Slate Warrior, Giant Rat and The Rock Spirit (low coefficients despite being common), Fissure (43% win rate of decks using it), Cyber-Stein and the fusion plan (10 wins in 26).

## Checks
- Deck-model score (sum of card coefficients): this deck +3.32 versus +3.26 for the 28-0 champion deck and 2.1-2.6 for the others. This is not independent proof (the model is trained on the same replays).
- Simulated opening six cards (20,000 hands): 85% have two or more Level 4 or lower monsters; 92% a removal/steal card; 71% a defensive card; 39% a draw engine; 28% a burn finisher; 2% no low monster.

## How to play it (from the findings)
- Turn 1: Set one monster and one or two traps. Keep MST/Heavy Storm for his traps.
- From your second turn: clear the blocker (Man-Eater Bug, Penguin, Crass Clown, MST, Raigeki, Change of Heart) and hit directly.
- Win with the Spell package (Change of Heart / Snatch Steal + Reborn / Premature Burial + United We Stand) or with Cannon Soldier / Archer burn; check `tools/advisor.py` for a kill every turn.
- Before ending your turn run the danger check: the loss in `no_bas_3` was a 6600 kill against 6200 life.
- Swap from the side deck after game 1 of a match: against Spell-package decks add Waboku, Imperial Order, Mirror Wall; against stall decks (Needle Worm, Solemn Wishes) add Dust Tornado, Ceasefire.

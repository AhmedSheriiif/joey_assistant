# Model findings: what the replays teach (trained on 236 games)

Models and scripts: `tools/train_deck.py`, `tools/train_position.py`, `tools/train_behavior.py`, `tools/export_champions.py`.
Saved models and tables: `data/models/` (deck_model.json, position_model.json (xgboost), play_impact.json, behavior_rules.txt).
Champion decks you can load in the game: `champion_decks/*.ydc` (gallery in `10_champion_decks.md`).

## 0. Read this first: how reliable is this data?
- The 236 games are only **174 distinct matchups, 227 distinct decks and 57 independent groups**. The set is dominated by *series*: one deck went **28-0**, another **19-0**, another **11-0**, then 7-0, 6-0, 6-0, 5-0, 5-0. Several decks went 0-12, 0-9, 0-8 against them.
- So deck strength and pilot skill are mixed together. A card being "in winning decks" can mean "the card is good" or "the strong player happened to play it". Anything below that rests on only one or two series is flagged.
- My first report counted every game separately, which inflated the numbers (including the "43-card decks win 77%" and "Cannon Soldier 67%" claims in 07/08). After removing repeats, **deck size and monster count have no effect** (correlation with win rate about -0.1 to 0). The corrected figures are in this file. Where 08 disagrees with this file, trust this file.
- No hand information exists in the logs (only the cards that were played), so decisions like "what the player held back" cannot be learned yet.

## 1. Deck model: which cards are in the deck of the player who wins
Logistic regression on card presence, winner deck minus loser deck, distinct matchups only, cross-validated with groups so no deck family is in both train and test.
- Held-out accuracy **78%, AUC 0.85** (chance = 50%). That is strong, but it partly measures "recognizable champion shells and their variants" rather than pure card power.
- Strongest positive cards (stable in 95%+ of bootstrap resamples): Penguin Soldier, Giant Trunade, Kunai with Chain, Mystic Tomato, Rush Recklessly, Cannon Soldier, Crush Card, United We Stand, Mirror Force, Call of the Haunted, Mirror Wall, Scapegoat, Man-Eater Bug, Graceful Charity, Mystical Space Typhoon, Crass Clown, Torrential Tribute, Kuriboh.
- Strongest negatives (almost never helpful): Offerings to the Doomed (3 wins vs 36 losses), Mechanicalchaser (1-21), The Fiend Megacyber (11-45), Sinister Serpent (9-35), Tribute to the Doomed (10-28), Mask of Darkness, 4-Starred Ladybug of Doom, Fissure, Solemn Wishes, Painful Choice, Card Destruction, Acid Trap Hole.

## 2. Cards you must include (the champion core)
Present in **at least 7 of the 9 champion decks** (and in most other decks too):
Mystical Space Typhoon (9/9), Sangan, Man-Eater Bug, Morphing Jar, Swords of Revealing Light, Magic Cylinder, Graceful Charity, Premature Burial, Giant Trunade (8/9 each); Call of the Haunted, Monster Reborn, Mirror Force, Torrential Tribute, Scapegoat, United We Stand, Witch of the Black Forest, Dimensional Warrior, Penguin Soldier (7/9 each).
The one-copy power spells (Pot of Greed, Dark Hole, Heavy Storm, Snatch Steal, Ring of Destruction) are in most champion lists but not all.

## 3. Hidden gems (low usage, strong evidence)
Evidence is shown as: usage across distinct decks | decks where only the winner had it vs only the loser | champion decks containing it | play-impact.
| Card | Usage | Winner-only vs loser-only | Champions | Why it helps |
|---|---|---|---|---|
| **Cannon Soldier** | 32% | 59 vs 16 | **6/9** | Tribute any monster for 500 direct damage. Fires on 22% of winning turns; it is the best finisher in the pool and pairs with Scapegoat/Kuriboh tokens and Giant Germ/Momonga recursion. Highest play-impact (+6.9 pts win chance per turn used). |
| **Crass Clown** | 11% | 42 vs 14 | 3/9 | When it is switched from Defense to Attack Position it bounces an opposing monster. A cheap repeatable removal/tempo tool. Impact +5.2. |
| **Rush Recklessly** | 28% | 47 vs 11 | 3/9 | Quick-Play +700 ATK for a turn: wins combat or adds lethal damage with no Tribute. In the 11-0 water deck (x3). |
| **Kuriboh** | 21% | 36 vs 18 | **5/9** | Hand-discard shield that negates one hit of battle damage; keeps LP high while the burn/direct plan runs. |
| **Mirror Wall** | 22% | 38 vs 13 | 2/9 | Halves attackers' ATK (upkeep 2000 LP): a lock for stall/burn decks. |
| **Crush Card** | 19% | 37 vs 13 | 1/9 | Kills a deck's big monsters outright (Tribute a DARK monster with ATK 1000 or less). |
| **Kunai with Chain** | 21% | 41 vs 6 | 2/9 | Shifts an attacker to Defense and gives +500 ATK. Strong net record but the play-impact estimate is negative, so treat as situational. |
| Kinetic Soldier | 31% | 33 vs 32 | 4/9 | Even by record but high play-impact (+5.0): +2000 ATK/DEF against Warriors. |
| Gemini Elf, Jinzo, Wall of Illusion, Nobleman of Crossout, Slate Warrior, Giant Germ | - | - | - | Positive play-impact (+3.5 to +6.0 pts); small samples. |
Caution: Cannon Soldier is the only gem confirmed by all three signals (deck record, champion-deck presence, play impact). The others lean on one or two series.

## 4. What a position tells you about winning (position model)
Gradient-boosted win-probability model on 4,555 turn snapshots, grouped cross-validation.
- AUC only **0.62 overall** (0.51 in turns 1-3, 0.65-0.67 in turns 7-25). The board and life-point state at a given turn explains only part of the outcome; play quality and the opponent's skill decide the rest. Do not over-trust any single number below.
- **Life point difference** (side to move, turn 4+): behind by 4000+ -> 22% win; behind 2000-4000 -> 32%; within +/-500 -> 52%; ahead 2000-4000 -> 70%; ahead 4000+ -> 81%. A 2000 swing is worth about 15-20 points of win chance.
- **Monsters on board** (mine minus opponent's): -2 or worse -> 37% win, even -> 54%, +1 -> 63%, +2 -> 66%.
- **Direct attacks already made**: 0-1 -> 45%, 2 -> 60%, 5+ -> 69%.
- Importance ranking: LP ratio, LP difference, who moved first, monster difference, direct attacks made by each side.

## 5. How the champions play (behaviour model)
Compared with everyone else, champion pilots, per turn:
| | Champion | Others |
|---|---|---|
| LP dealt to the opponent | **789** | 431 |
| Direct attacks | **0.37** | 0.24 |
| Burn effects fired | **0.20** | 0.06 |
| Removal / steal cards played | **0.36** | 0.22 |
| Spell/trap plays | **1.15** | 0.95 |
| Effects fired | **1.06** | 0.86 |
| Monster attacks | 0.50 | 0.53 |
| LP lost by themselves | 159 | 172 |
| First monster set face-down | 65% | 74% |

They do not attack more with monsters; they **clear the way and then strike directly**: when the opponent has no monster they attack 83% of the time (others 60%) and hit directly 61% (others 44%). They spend more cards on removal and burn, and take about the same damage.
- Champion game length: median 16 turns. They went first in 50 of 98 games (no first-player edge for them).
- As the opponent's LP falls, burn use rises: when the opponent is at 2000 or less, burn fires on 21% of the champion's turns (7% when above 6500).
- Opening book of the champions (turn one): Magic Cylinder + a Set Morphing Jar; Swords of Revealing Light + Mystic Tomato; a Set Nimble Momonga with Torrential Tribute; MST + Mirror Force + Set Crass Clown. In general: **one Set monster plus one or two Set traps**, saving the spells.

## 6. Rules of thumb the assistant should apply
1. Win the LP race. Each 2000 LP lead is worth about +15-20% win chance; take cheap damage (direct hits, Magic Cylinder, burn) whenever it is safe.
2. Win the board by +1. Champions keep the monster count level or ahead and use removal (Dust Tornado, MST, Heavy Storm, Giant Trunade, Nobleman, Crass Clown bounce) to empty the opponent's side, then hit directly.
3. If the opponent has no monsters: attack, almost always (champions 83%).
4. If the opponent has monsters: do not feed attackers into Set monsters unless you have a Rush Recklessly/Kunai/backup. Prefer to remove or bounce first.
5. Finish with burn once the opponent is under about 3000: Cannon Soldier (500 per Tribute), Amazon Archer, Magic Cylinder, Ring of Destruction, Ceasefire.
6. First turn: Set one monster and one or two traps; keep MST/Heavy Storm for their traps.
7. Keep Kuriboh or a Scapegoat to stop a lethal swing while you finish.

## 7. Limits and next steps
- The models are advisory: they describe what winners did, not proven optimal play. Treat percentages as ±10 points.
- To improve: more replays (especially more distinct players and decks), which pilot is who, which tournament, and the player's hand. With hand data I could train a real "what to play from this hand" policy.
- A live advisor can be built on top: you enter LP, board and hand each turn, and it applies sections 4-6 plus the deck lists in `10_champion_decks.md`.

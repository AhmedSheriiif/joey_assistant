# Playbook: patterns for the assistant to suggest while you duel

Built from: the rules (01), AI tendencies (02), your 10 decks (04), and the two replays (05).
Status: first draft. Items tagged **(replay)** were seen in your replays; **(AI)** come from documented Joey behaviour;
**(card)** follow from card text. Nothing here is win-rate tested.

## 1. How your decks work (what the assistant should assume you want)
- Your core is a 60-card "grind" shell: Giant Germ x3, Nimble Momonga x3, The Rock Spirit, Giant Rat, Mystic Tomato, Dimensional Warrior (small bodies that replace themselves from the Deck), Scapegoat, Crush Card, Mystical Space Typhoon, plus single-copy staples (Pot of Greed, Graceful Charity, Raigeki, Dark Hole, Heavy Storm, Snatch Steal, Premature Burial, Monster Reborn, Imperial Order, Mirror Force, Ring of Destruction, Torrential Tribute).
- Win routes you actually use **(replay)**: damage race with set monsters + Ring of Destruction (anas1: Ring dealt 1900 to both), and a long attrition game (0cards_deck_win, 44 turns) closing with a 3-4 monster swing.
- Fusion deck: Alligator's Sword Dragon (direct hit if only EARTH/WATER/FIRE on the other side) or the Blue-Eyes Ultimate Dragon / Thousand-Eyes Restrict package in `!Ladder`/`40CardsNoBas`.

## 2. Opening checklist (turns 1-2)
1. Going first = you cannot attack; set a monster (prefer a flip/recur body: Giant Germ, Nimble Momonga, Man-Eater Bug, Mystic Tomato) and 1-2 Spell/Trap. **(replay: you opened Wall of Illusion + Mystical Space Typhoon set.)**
2. Keep one Normal Summon for Main 2 if holding Torrential Tribute-type threats: the AI waits to summon in Main 2 when it fears Torrential **(AI)**.
3. Do not over-commit 3+ monsters to the field before the opponent has shown a sweeper.

## 3. If/then patterns by situation
| Situation | Suggestion | Why |
|---|---|---|
| Opponent set 1 monster on turn 1-2 | Hit it with a mid-ATK monster, not your best. Be ready for Cyber Jar / Morphing Jar / Man-Eater Bug. | Flip effects punish your strongest attacker **(replay: OPP set Cyber Jar turn 2, flipped turn 4 and wiped the board and reset hands)**. |
| Cyber Jar flips | After the wipe, summon the biggest Level 4 or lower you revealed; both sides start fresh. Keep Heavy Storm/MST for their reset Traps. | Cyber Jar: destroy all, draw 5, summon Lv4-. |
| Opponent has 3+ Set Spell/Trap | Heavy Storm / Harpie's Feather Duster / MST before attacking, or bait with the weakest monster. | AI uses left-to-right Trap order **(AI)**. |
| Imperial Order out (theirs) | Don't rely on Spells; attack, use Traps/monsters. They pay 700 each Standby **(replay: LP loss 700 flag=self)**. Bait Dust Tornado/MST. | Imperial Order negates all Spells. |
| Your Imperial Order out | Play Traps and monsters only. Count their Spell-based outs. | Same card. |
| Opponent plays Needle Worm / mills | Count your Deck; keep Card Destruction/Pot of Greed out of the plan if close to deck-out. | Needle Worm = Deck mill. |
| Opponent has Solemn Wishes / Cure Mermaid style recovery | Use burn/direct damage; race instead of grinding. Mirror Force/Torrential Tribute + immediate swing. | LP gain outpaces slow attacks **(replay: 0cards game ran 44 turns).** |
| You hold Ring of Destruction | Set it; use when their monster has high ATK AND your LP > the damage. Beware it hits you too. | anas1: 1900 each. |
| Opponent attacks into your Set Scapegoat | Fine, it absorbs. Pair with Giant Germ/Nimble Momonga to refill. | Sheep Tokens cannot be Tributed. |
| Opponent at low LP, 3+ attackers on your side | Attack in ascending ATK so a Trap fires on the weakest **(AI)**. | Left-to-right Trap order. |
| Opponent has face-down monster, you have a strong attacker | Attack face-down monsters with your best attacker only if it has no important flip loss; the AI picks the "best leftmost" monster to destroy for flip effects **(AI)**. | Avoid losing the key card. |
| You are behind | Raigeki / Dark Hole / Torrential Tribute then swing; Snatch Steal / Change of Heart for lethal. | Board wipes + steal. |
| Opponent is Joey (AI) with Gravity Bind (Lv4+ cannot attack) | MST/Heavy Storm it; attack with Lv4-or-lower: Gemini Elf 1900, Axe Raider 1700, Goblin Attack Force 2300. | See 02. |
| Opponent is Joey with Exodia | Delinquent Duo, Ceremonial Bell, Cold Wave, Card Destruction. Count pieces. | Exodia deck (Set #3). |

## 4. Trap/Spell timing reminders for the assistant
- Trap needs a turn on the field. Quick-Play from hand any time. Counter Traps respond to Spells only.
- Jinzo (yours or theirs) shuts all Traps; Mirror Force/Magic Cylinder/Solemn Judgment are dead while it's up.
- Torrential Tribute triggers on any summon, including Flip Summon and Special Summon.
- Cold Wave / Anti-Spell Fragrance change when you can use Spells.

## 5. What to teach the assistant next (needs your input)
1. Confirm replay semantics (tell me 5 things you remember doing in `anas1.ydr` so I can verify the CE/CF argument bits).
2. Which deck is "yours" for the Joey games, and what is Joey's current star level.
3. Give the assistant a way to know the board: type it in, or read the game window with screenshots (computer use). I can't read the live game state yet.

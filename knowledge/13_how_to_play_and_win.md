# How to play and win: what 240 tournament replays teach

Data: 240 unique games (includes your six `no_bas` games, in which you won 5 and lost 1), 177 distinct matchups, 229 distinct decks. Card pool: the **771 playable cards** only.
Tags: **[stat]** counted from the replays, **[text]** from card text, **[idea]** unverified. Deck strength and pilot skill are mixed in this data (see section 8).

## 1. Did I learn how to play? What I know and what I don't
Learned (counted, not guessed):
- The shape of a winning game: small early lead, grow it with removal plus direct hits, finish with a burst or burn (sections 3-5).
- The recurring one-turn-kill (OTK) frame that ends most fast games (section 4).
- Which cards the winners actually use and which lose (section 7).
Not learned yet:
- **Hand decisions.** The logs contain what was played, not what was held back, so I can't tell why a player waited.
- **Matchup-specific play** (needs many more games per deck).
- I can describe and score positions, but I cannot yet play at the level of the strongest pilots. The same deck shell went **19-0** and **0-12** in these replays: pilot skill is bigger than card choice.

## 2. The decks that win
Four families (full lists in `10_champion_decks.md`, loadable `.ydc` files in `champion_decks/`):
1. **Good-stuff / recursion (28-0, 7-0, 6-0, 5-0).** Mystic Tomato, Nimble Momonga, Scapegoat x3, MST, Sangan, Witch, Man-Eater Bug, Morphing Jar, Jinzo, Penguin Soldier, Crass Clown, Cannon Soldier; Premature Burial, Monster Reborn, Call of the Haunted, Giant Trunade, Swords, Torrential Tribute, Mirror Force, Magic Cylinder, Ring of Destruction, United We Stand, Snatch Steal.
2. **Earth beatdown (19-0).** Giant Rat, The Rock Spirit, Kinetic Soldier, Bazoo, Dream Clown with Cannon Soldier, Amazon Archer, Fissure, Waboku. The same shell also went 0-12, 0-9 and 0-8 in other hands, and it is essentially your own `no_bas` deck, which went 5-1 (see section 6).
3. **Water tempo (11-0).** Mother Grizzly x3, Aqua Spirit, Cure Mermaid, Rush Recklessly x3, Seven Tools x3, Mirror Wall, Fairy Box, Raigeki, Change of Heart.
4. **Stall and burn (11-1, 6-0, 5-0).** Blast Sphere, Ekibyo Drakmord, Wall of Illusion with Cannon Soldier; Giant Germ/Kinetic Soldier warrior deck; a 63-card Fissure/Dust Tornado/Solemn Wishes pile.
Common to all: 40-48 cards, about 19 low-level monsters, 20+ spells/traps, and the same five fusion monsters in the fusion deck.
Fusion deck is not dead: **Cyber-Stein** (pay 5000 LP, Special Summon a fusion) was in 26 games (10 wins); see combo 5.

## 3. Game plan by phase
**Start (your turns 1-2)**
- Set one monster and one or two traps; hold spells. Winners play 0.96 monsters and 1.55 spell/trap cards on turn one. First monster is Set face-down 72% of the time. [stat]
- Good turn-one monsters: Mystic Tomato, Nimble Momonga, Man-Eater Bug, Giant Rat, Dimensional Warrior, Giant Germ, Penguin Soldier, Morphing Jar (replace themselves when they die or flip). [stat]
- Don't summon your own Jinzo while your Traps are Set: Jinzo shuts off **your** traps too. [text]
- The separation starts at your second turn: winners deal on average **712 LP on their 2nd turn vs 348** for losers, and attack directly in 45% of turns vs 20%. [stat]

**Middle (turns 3-15)**
- Winners lead on life points by about 270 (turns 3-4), 840 (5-8), 1050 (9-15), 1600 (16-30). [stat] 29% of winners (70/240) were behind by 2000+ at some point, and the last turn they were behind was a median of turn 8, so a deficit is recoverable. [stat]
- Per turn they use more removal (0.35 vs 0.2), more spell/trap cards (1.0 vs 0.9), and land direct hits 0.4 per turn vs 0.15. [stat]
- Turn pattern: remove/bounce/steal the blocker (MST/Dust Tornado/Heavy Storm/Giant Trunade/Man-Eater Bug/Penguin/Crass Clown/Change of Heart/Snatch Steal), then attack directly. 266 of 618 winner turns that included a direct hit also used removal or steal. [stat]
- Keep cards: trade bodies that replace themselves (Giant Germ, Nimble Momonga, Mystic Tomato, Giant Rat, Sangan, Witch).
- Value of a lead: 2000 LP ahead is worth about +18 points of win chance; being 4000 behind is 22% to win. [stat]

**End (finishing)**
- Median final-turn damage 2400; **40% of wins finish with a turn of 3000+; 17 games were won in one turn from 7000+ LP**. [stat]
- Count your burst every turn (section 4): attackers' ATK (with equips) + burn from Tributes + Magic Cylinder/Ring of Destruction.
- Use burn when the opponent is under about 3000: 21% of champion turns at that point include a burn effect. [stat]
- Don't throw your last defender away to attack for 500 if the opponent has 1+ burst cards visible.

## 4. The combos that actually appear (turns with 3000+ damage; 198 such turns, 56 of 5000+)
Lift = how much more often the card appears in a big-damage turn than in an average turn.
Cards: Snatch Steal 6.4, Amazon Archer 6.0, Cannon Soldier 5.6, Monster Reborn 5.5, United We Stand 5.0, Premature Burial 4.6, Giant Trunade 4.6, Jinzo 4.5. [stat]
Strongest pairs in the same turn: Cannon Soldier + Giant Trunade (13.7), Cannon Soldier + Premature Burial (13.2), Amazon Archer + Premature Burial (12.9), Cannon Soldier + MST (12.6), Amazon Archer + Monster Reborn (11.2), Giant Trunade + United We Stand (11.1), Jinzo + Monster Reborn (8.0). [stat]

The recurring frames:
1. **The Spell OTK** (your own wins in `no_bas_1` and `no_bas_4`, 8400 and 8000 damage in one turn from full life): clear the field and traps with **MST/Giant Trunade**, take the lone blocker with **Change of Heart/Snatch Steal**, refill with **Monster Reborn/Premature Burial/Call of the Haunted**, equip **United We Stand** (+800 per monster), swing directly with everything, then finish with **Amazon Archer** (1200 for 2 Tributes). 22% of big turns are "removal + direct hit"; 14% add a burn effect. [stat]
2. **Burn from bodies**: Cannon Soldier (500 per Tribute) fired 3+ times in a turn in 39 of its 78 uses. Pair with Scapegoat/tokens or Premature Burial/Reborn bodies. [stat, text]
3. **Equip stack on a double attacker**: Hayabusa Knight (attacks twice) + United We Stand + Megamorph = 4200 x 2 (the 8400 turn in `lol..`). [stat, text]
4. **Magic Cylinder / Mirror Force / Torrential Tribute**: reactive damage that also protects; trap decks leave them Set and bait with weak monsters.
5. **Cyber-Stein + Megamorph** (turn-3 kills of 8300-8400): Stein pays 5000 LP and Special Summons Blue-Eyes Ultimate Dragon (4505 ATK); because your LP is now lower than his, **Megamorph doubles the original ATK** (about 9000). If it fails you are at 3000 LP, which fits the 10-16 record of Stein decks. [stat, text]
6. **Recursion loops**: Premature Burial, Monster Reborn, Call of the Haunted bring back Jinzo/Archer/Cannon Soldier; Last Will, Sangan, Witch, Mystic Tomato fetch the next body.

## 5. OTK arithmetic the assistant should run each turn
- Opponent's burst on his next turn ~ sum of his attackers' ATK (+800 per extra monster if he has United We Stand, +1000 for Rush/Kunai) + 1200 per 2 monsters (Archer) + 500 per monster (Cannon Soldier). If that is at or above your LP and he has the removal to clear you, you are in range.
- Your own burst: same formula with your board; add Magic Cylinder = the attacker's ATK.

## 6. Your six games (`no_bas_1-6`): you won 5 and lost 1
(I first read these the wrong way round. In these files you are the **first** deck list, which the decoder labels "OPP"; your opponent changed his deck between games while yours stayed the same 40 cards.)
Your deck: 3x Giant Rat, 3x Nimble Momonga, 3x Scapegoat, 2x Man-Eater Bug, 2x MST, 2x The Rock Spirit, Amazon Archer, Call of the Haunted, Change of Heart, Dark Hole, Dimensional Warrior, Giant Trunade, Graceful Charity, Harpie's Feather Duster, Imperial Order, Jinzo, Kuriboh, Mage Power, Mirror Force, Monster Reborn, Mystic Box, Pot of Greed, Raigeki, Ring of Destruction, Sangan, Snatch Steal, Swords of Revealing Light, Torrential Tribute, United We Stand, Waboku, Witch of the Black Forest.
- **no_bas_1 (won on turn 4, 8400 damage from 8000 LP):** MST removes his Set trap, Sangan, United We Stand, Change of Heart steals his lone Jinzo, then direct hits of 3800 + 2400 + 1000, and Amazon Archer for the last 1200.
- **no_bas_2 (won on turn 9, 8300 in one turn):** Imperial Order, Harpie's Feather Duster, MST, Snatch Steal.
- **no_bas_4 (won on turn 7, 8000 in one turn):** Giant Trunade, MST, Amazon Archer, Change of Heart, Monster Reborn, four direct hits and two Archer bursts.
- **no_bas_5 (40 turns) and no_bas_6 (21 turns)** were longer wins.
- **The loss, no_bas_3:** you were actually ahead going into his last turn (about 6200 life against his 2300), but he played Snatch Steal, Nobleman of Crossout, Premature Burial, Monster Reborn, MST and United We Stand and hit you directly for 4100 + 2500 = 6600, just above your 6200. It is the same Spell OTK frame you use yourself.
- What your wins show: the frame works from full life in 4-9 turns. Your one loss shows that a life lead is not safety: add up his possible burst each turn (section 5) and keep Waboku, Kuriboh, Imperial Order or an extra blocker for that turn.

## 7. Meta and hidden-gem cards over the 771 pool
Tier A, proven core (champions 7+/9): MST, Sangan, Man-Eater Bug, Morphing Jar, Swords of Revealing Light, Magic Cylinder, Graceful Charity, Premature Burial, Giant Trunade, Call of the Haunted, Monster Reborn, Mirror Force, Torrential Tribute, Scapegoat, United We Stand, Witch of the Black Forest, Dimensional Warrior, Penguin Soldier.
Tier B, hidden gems with data support: **Cannon Soldier** (6/9 champions, lift 5.6), **Crass Clown**, **Rush Recklessly**, **Kuriboh**, **Mirror Wall**, **Crush Card**, **Kunai with Chain**, **Snatch Steal** (lift 6.4), **Amazon Archer** (lift 6.0, in half the decks), **Hayabusa Knight/Megamorph** (used in two 8400 turns).
Tier C, strong by card text but almost unused (untested): Cyber-Stein + Megamorph + fusion deck, Magic Thorn + Morphing Jar, Horn of Heaven, Catapult Turtle with a stolen monster, Scapegoat-fueled Cannon Soldier burn, Ameba/Griggle with Mystic Box. See `12_combo_ideas.md`.
Losers: Offerings to the Doomed, Mechanicalchaser, The Fiend Megacyber, Sinister Serpent, Tribute to the Doomed, 4-Starred Ladybug, Fissure (in mixed hands), Painful Choice.

## 8. Limits
- Skill and deck can't be separated; one pilot per champion series. Treat percentages as +/-10 points.
- The models explain who wins, they do not yet choose the best move from a hand.
- The most valuable new data: more distinct players, losses that show defense, and logs with hand information.

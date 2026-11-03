# Rulings: Yu-Gi-Oh! Power of Chaos: Joey the Passion (PC, 2004)

Sources: Lunion "How To Play" guide (GameFAQs #39621), CrispyMallow FAQ v1.15 (GameFAQs #30509),
Yugipedia game page, and the in-game card text from pongy's card list (GameFAQs #32648).
Items marked **[inferred]** are my reading of the card text, not stated by a source. Verify in play.

This game uses 2004-era rules and card wording. Do NOT assume modern (post-2008) rulings.

## 1. Win / lose
- Each player starts with 8000 Battle Points (BP, i.e. Life Points).
- You win by taking the opponent to 0 BP, or when they cannot draw (deck-out).
- Surrender = click your own deck during a Main Phase.

## 2. Setup
- Rock-paper-scissors decides who picks first turn. Going first is generally better (guide opinion).
- **The player who goes first cannot attack on turn 1.**
- Main deck: 40 min, 80 max. Side deck: max 15. Fusion deck: max 15 (does not count toward main deck).
- Max 3 copies of a card. Limited cards: 1 or 2 copies (the number shown in the deck editor).
  Forbidden cards: optional ban list, toggled in the options menu ("Forbidden Cards").
- Match duel = best of 3; you may swap main and side deck cards between games (same number out as in).
  Joey keeps the same deck for the whole match.

## 3. Field
- 5 monster zones, 5 spell/trap zones, 1 field spell zone (11 cards max on the field).
- Only one Field Spell at a time; a new one replaces the old one.
- Hand limit: at End Phase, discard down to 6 cards. (Infinite Cards removes this limit.)

## 4. Turn structure (6 phases)
1. Draw: draw 1 (compulsory). Traps can be activated.
2. Standby: nothing to do; "Standby Phase" card effects trigger (Cure Mermaid, Fairy Box upkeep, Messenger of Peace, etc.).
3. Main Phase 1: summon, set, activate spells and traps, change positions.
4. Battle Phase: attack with face-up Attack Position monsters. Traps and Quick-Play spells can be used.
5. Main Phase 2: as Main Phase 1 (if you haven't Normal Summoned yet).
6. End Phase: hand-size discard.

## 5. Summoning
- **Normal Summon**: once per turn, face-up Attack or face-down Defense ("Set"). Cannot summon face-down Attack or face-up Defense.
  - Level 1-4: no Tribute. Level 5-6: 1 Tribute. Level 7+: 2 Tributes. A Tribute Summon uses your Normal Summon.
- **Flip Summon**: flip a face-down Defense monster you controlled since a previous turn into face-up Attack. Unlimited per turn. FLIP effects activate.
- **Special Summon**: by card effect. Unlimited.
  The game does not recognise every kind of Special Summon as a trigger for traps (CrispyMallow FAQ).
- Summoned/Set/flipped monsters cannot change position the same turn (except by effect).
- **Fusion**: Polymerization (or Fusion Gate) + listed materials. Fusion monsters live in the Fusion Deck.
- **Ritual**: needs the matching Ritual Spell and Tribute monsters whose Levels total 8+ (only 2 rituals in this pool, see card pool).

## 6. Battle damage
| Attacker | Target | Result |
|---|---|---|
| ATK vs ATK | face-up Attack | Lower ATK is destroyed; difference is damage to its controller. Equal ATK: both destroyed, no damage. |
| ATK vs DEF | Defense (face-up) | ATK > DEF: defender destroyed, no damage. ATK < DEF: attacker takes the difference, nothing destroyed. Equal: nothing happens. |
| ATK vs face-down | Defense (face-down) | Flipped first (FLIP effect triggers), then as ATK vs DEF. |
| Defense monsters | - | Cannot attack. |
- No direct attack while the opponent has a monster (except cards that say so: Mystic Lamp, Alligator's Sword Dragon, etc.).

## 7. Spell / Trap rules
- **Normal Spell**: play from hand during your own Main Phase. Or Set it and activate in a later turn.
- **Quick-Play Spell** (lightning icon): can be played from hand at any time, including the opponent's turn (e.g. Graceful Dice, Scapegoat, De-Fusion, Offerings to the Doomed, Limiter Removal, Sebek's Blessing).
  Per the guide: a Quick-Play Spell Set face-down can only be activated from the *next* turn. [guide wording: "unless quick play"; treat Set Quick-Play as needing a turn]
- **Equip / Continuous / Field**: stay on the field.
- **Trap**: must be Set and wait at least one turn before activation. Some need a trigger condition.
- **Counter Trap** (Magic Drain, Magic Jammer, Riryoku Field): respond to Spells.
- Spells can be activated "right away" on your own turn; Set Spells activate on your next turn.
- Chaining is supported (Joey uses it; "CHAIN!" is one of his lines).

## 8. Positions and abbreviations
FUAP = face-up Attack, FDDP = face-down Defense, FUDP = face-up Defense.

## 9. Game-specific engine behaviours
- Joey's difficulty: 1 to 9 stars. Wins raise it and he swaps to a stronger deck; consecutive losses lower it. Up to level 7 uses Joey-the-Passion cards only; 8-9 add cards from the previous games (CrispyMallow: "up to 7 & 9 for Joey the Passion cards and cards from all games"). There is an option to stop Joey using prior-game cards.
- Rewards: a single duel gives 1 card, a match gives 3 (350 cards equally likely, no duplicates within one match reward). At >=80% collection you may re-roll the reward if all are duplicates; at >=90% a second re-roll.
- Forced-reveal effects (e.g. Cyber Jar-style) shuffle the revealed player's hand, so card positions aren't traceable.
- Cards animate along their real path: a keen player can infer hidden information (CrispyMallow). Joey's AI can "see" face-down monsters.

## 10. Rulings implied by card text in this pool (2004 wording) [inferred]
- **Jinzo** (6 stars, 2400/1500): while face-up, no Trap can be activated and face-up Traps are negated. Joey runs Jinzo #7 in the full-power set.
- **Imperial Order / Royal Command / Anti-Spell Fragrance**: lock cards; pay upkeep in Standby Phase.
- **Torrential Tribute** triggers on ANY summon (Normal, Flip, Special) and destroys ALL monsters on the field, including yours.
- **Trap Hole is not in this pool**, but the opponent-tendency note says it does not discriminate on ATK.
- **Magic Cylinder**: negates attack and deals the attacker's ATK as direct damage.
- **Time Wizard**: coin call; right = destroy opponent's monsters, wrong = destroy yours and lose half their total ATK.
- **Toon cards** need Toon World face-up on the field; they pay 500 BP to attack.
- **Graverobber** here is a *Trap*: take a Spell from the opponent's Graveyard, use it this turn, take 2000 damage if you do.
- **Premature Burial / Monster Reborn / Call of the Haunted** are the Special Summon from Graveyard core. Card of Safe Return draws on those.
- **Messenger of Peace**: monsters with ATK 1500+ cannot attack; 100 BP upkeep.
- **The Dark Door**: both players can attack with only one monster per Battle Phase.
- **Scapegoat**: 4 Sheep Tokens in Defense; you cannot summon any monster that turn.
- **Cold Wave / Prohibition / Nightmare's Steelcage / Gravity Bind (Lv4+ cannot attack)** are the tempo and lock tools.
- **Limiter Removal** doubles Machine ATK; Machines are destroyed at end of turn.
- Card text typos are original and deliberate in the source list.

## 11. Forbidden / Limited (read from the game itself)
The full list is a 38-entry table inside `joey_pc.exe` (pairs of deck id and level), saved as `joey_web_game/data/banlist.json`. It agrees with every card seen in the CrispyMallow deck data.
- Level 0, Forbidden when the "Forbidden Cards" option is on (the in-game tutorial says there are none by default; with the option off they are most likely Limited): Cyber Jar, Delinquent Duo, Painful Choice, Change of Heart, Raigeki, Harpie's Feather Duster, Imperial Order.
- Level 1, Limited (1 copy): Sinister Serpent, Sangan, Witch of the Black Forest, Jinzo, Exodia the Forbidden One and its 4 pieces, Confiscation, Heavy Storm, The Forceful Sentry, Snatch Steal, Pot of Greed, Monster Reborn, United We Stand, Card Destruction, Graceful Charity, Upstart Goblin, Premature Burial, Swords of Revealing Light, Dark Hole, Mage Power, Mirror Force, Ceasefire, Ring of Destruction, Magic Cylinder, Call Of The Haunted.
- Level 2, Semi-limited (2 copies): Morphing Jar, Morphing Jar #2, Nobleman of Crossout.
- Every other card: up to 3 copies.

## Counter Traps and the Damage Step (added for the web game; sources: Yugipedia, Konami)
- **Spell Speed 3.** Counter Traps are Spell Speed 3. A Spell Speed 2 card (normal Trap, Quick-Play Spell) cannot be chained to a Counter Trap; only another Counter Trap can. ([Yugipedia: Seven Tools of the Bandit rulings](https://yugipedia.com/wiki/Card_Rulings:Seven_Tools_of_the_Bandit))
- **What they do in this game's card pool.** Seven Tools of the Bandit negates a Trap activation (pay 1000 LP) and destroys it. Solemn Judgment (pay half LP) negates a Spell/Trap activation or a summon and destroys it. Magic Jammer / Magic Drain / Riryoku Field are the Spell-only Counter Traps. When an activation is negated, the card is destroyed and its effect does not happen.
- **Damage Step.** Only Spell/Trap cards that directly change a monster's ATK/DEF, and Counter Traps, may be activated, and only until damage calculation. Other Quick effects (e.g. Waboku, Ring of Destruction) may not. ([Yugipedia Damage Step reference](https://yugipedia.com/wiki/Special:MobileDiff/3979117), [Counter Trap Cards](https://ycm.fandom.com/wiki/Counter_Trap_Cards))
- Web game: `tests/chains.test.mjs` scenario 13 checks these (Solemn Judgment may answer Rush Recklessly in the Damage Step, Waboku may not, nothing but a Counter Trap answers a Counter Trap).

## Ritual monsters (added for the web game)
- A Ritual Monster can only be summoned with its own Ritual Spell (e.g. Commencement Dance -> Performance of Sword, Dark Magic Ritual -> Magician of Black Chaos). It cannot be Normal Summoned or Set.
- The Spell is played from the hand; the Ritual Monster must be in the hand. You offer Tribute monsters from the field or hand whose Level Stars add up to the number on the Spell (or more); Tributes are added one at a time and you stop once the number is reached. The Ritual Monster is Special Summoned face-up. Sources: [Yugipedia: Ritual Summon](https://yugipedia.com/wiki/Ritual_Summon), [YGOPRODeck rules guide](https://ygoprodeck.com/confusing-yu-gi-oh-rules-part-1/).
- Pool: 8 Ritual Spells (Black Illusion Ritual, Commencement Dance, Dark Magic Ritual, Turtle Oath, Curse of the Masked Beast, Revival of Dokurorider, Hamburger Recipe, Novox's Prayer) and their monsters (Relinquished, Performance of Sword, Magician of Black Chaos, Crab Turtle, The Masked Beast, Dokurorider, Hungry Burger, Skull Guardian).

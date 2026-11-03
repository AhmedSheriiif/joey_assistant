# Combo ideas from reading the real 771-card pool

Pool: only the **771 playable cards** (155 Yugi + 315 Kaiba + 350 Joey, flagged in `data/cards_all.csv`; `data/cards_game.csv` is the filtered list). Earlier I wrongly treated all 1,114 database entries as the pool: the extra entries are the card back, tokens and unused cards (for example Wetha and Weather Control are not playable).
Evidence tags: **[text]** derived from the card text only (not seen in the replays), **[replay]** seen in the replay data, **[stat]** a number from the replays. Card usage in the 227 tournament decks is given where it matters: most of these combos are used by almost nobody, which is why they may be hidden gems and also why they are untested.

## A. Mystic Box and giving things away
Mystic Box: destroy 1 opponent monster, then give 1 of your own monsters to the opponent. In the replays it appears in 50 distinct decks (51 wins in 90 games) and is played 69 times; players mostly give away cheap flip monsters (Man-Eater Bug, Morphing Jar, Amazon Archer, Giant Germ).
- **Destroys a Set monster without its FLIP effect [text]**: the guide says flip effects don't trigger when a card is destroyed by a card effect. So Mystic Box answers Man-Eater Bug, Penguin Soldier, Morphing Jar, Cyber Jar and Spear Cretin when they are face-down. (Nobleman of Crossout also does this and removes the other copies from the deck.)
- **The sheep idea (Scapegoat + Mystic Box) [text]**: Scapegoat gives 4 Sheep Tokens (0/0, Defense). Giving one to the opponent turns his Set monster into a 0-ATK body. Whether a given monster arrives in Attack or Defense Position is not shown in the card text. Standard rules keep the position, so a Defense-Position sheep would be destroyed with no damage; a sheep in Attack Position would take your full ATK as damage. **I could not confirm the position from the replays** (only one replay combines the two cards). Test it once in a practice duel and save the replay; I will read the position from it.
- **Risk of giving a body [text]**: any monster you give is fuel for his Cannon Soldier (in 32% of decks), Amazon Archer (50%) and United We Stand (59% of decks, +800 per monster). Sheep tokens cannot be used for a Tribute Summon, but the text of those burn effects only excludes monsters used for a Tribute Summon, so a sheep can still pay for them. Do not give a sheep to a deck showing Cannon Soldier/Archer.
- **Give something that hurts instead [text]**, all playable:
  - **Ameba** (L1, Kaiba): when control shifts to the opponent, he takes 2000 direct damage (once). Mystic Box + Ameba = remove a monster and deal 2000. Used in only 2 tournament decks.
  - **Griggle** (L1, Kaiba): when control shifts to the opponent, you gain 3000 LP. Mystic Box + Griggle = remove a monster and gain 3000. Used in 0 decks.
  - **Mushroom Man #2** (L3, Kaiba): its controller loses 300 LP each of his Standby Phases; control can be passed back for 500 LP. Hot potato.
  - **The Unfriendly Amazon** (L4 2000/1000): its controller must Tribute a monster every Standby or it is destroyed. Give it to a player with few monsters.
  - **Insect Queen / Panther Warrior**: cannot attack unless their controller Tributes a monster.
  - Invader of the Throne (FLIP) and Snatch Steal are the reverse: they take a monster from him.
- **Swap trick [text]**: Mystic Box with a monster that is already weak or cursed is cheap removal for a single card.

## B. Scapegoat / token engines for burn
Cannon Soldier (500 per Tribute, no limit per turn) and Amazon Archer (1200 per 2 Tributes) turn bodies into damage. **[stat]** Cannon Soldier fired 3 or more times in the same turn in 39 of the 78 turns it was used (max 7 times = 3500).
- **Scapegoat + Cannon Soldier**: 4 sheep = 2000 direct damage the turn Scapegoat is played (you cannot summon that turn, so Cannon Soldier must already be face-up). With Amazon Archer: 4 sheep = 2 activations = 2400. **[stat]** Scapegoat and a burn monster were used in the same turn only 11 times in 236 games, so this is under-used.
- **Multiply** (needs a face-up Kuriboh): puts a Kuriboh Token on each open zone (up to 4), more fuel without the "no summon" restriction. Used in 0 decks.
- **Jam Breeding Machine**: a Slime Token (500/500 Attack) each Standby; one body per turn but you cannot summon other monsters.
- Lethal check for the assistant: burn available = (number of monsters you control other than Cannon Soldier) x 500 with Cannon Soldier, or floor(monsters/2) x 1200 with Archer.
- **Catapult Turtle**: Tribute a monster for damage equal to half its ATK. With **Change of Heart** (control until end of turn) or **Snatch Steal**: take his biggest monster (for example 2800) and Tribute it for 1400 direct damage, removing it permanently. Snatch Steal's 1000 LP/turn gift to him ends when the monster is gone. 12 tournament decks, 31% win rate (small sample from weaker decks).

## C. Discard and draw burn (almost nobody plays it)
- **Magic Thorn** (Continuous Trap): 500 damage for each card of the opponent's that is discarded by a Spell, Trap or Effect Monster. With **Morphing Jar** (both players discard their hands; in 69% of decks!), **Delinquent Duo**, **Graceful Charity**/Card Destruction effects and Rigras Leever, a full hand discard is 1500-2500 damage. 0 tournament decks use it.
- **Forced Requisition** (Continuous Trap): whenever you discard from your hand, he discards the same number. Pair with Graceful Charity (discard 2) and Magic Thorn.
- **Type Zero Magic Crusher**: 500 per Spell you discard from hand (Graceful Charity discard).
- **Skull Invitation**: 300 to the owner of every card sent to the Graveyard (symmetrical, so use it when you are ahead).
- **Princess of Tsurugi** (FLIP): 500 per Spell/Trap on his field. Strong against trap decks.

## D. Life-point engines
- **Fire Princess**: 500 damage every time you gain life. Gains: Solemn Wishes (+500 per draw), Cure Mermaid (+800 each Standby), Spirit of the Breeze/Dancing Fairy (+1000), Nimble Momonga (+1000), Marie the Fallen One (+200), Hysteric Fairy (+1000), Sebek's Blessing (gain equal to the direct damage you just dealt). **[stat]** Fire Princess was in only 4 decks and went 0-6, so treat it as unproven.
- **Sebek's Blessing + Cannon Soldier/Magic Cylinder**: burn that heals you.
- **Kuriboh / Waboku / Mirror Wall** protect your life points while the engine runs.

## E. Counters and tempo tricks
- **Horn of Heaven** (Trap, Kaiba): Tribute one of your monsters to negate any summon, including Special Summons, and destroy the monster. A sheep token is a free cost. It stops the meta's recursion (Monster Reborn 64%, Call of the Haunted 63%, Premature Burial 59% of decks) at the summon. 0 decks use it.
- **Spiritualism**: bounce a Spell/Trap that cannot be negated; **Gryphon Wing**: turns his Harpie's Feather Duster against him.
- **Share the Pain** (Kaiba): you Tribute one monster (a sheep), he must Tribute one of his. He chooses, so use it when he has only one monster.
- **Invader of the Throne** (FLIP): trade it for his best monster.
- **Blast Juggler**: destroys 2 face-up monsters with ATK 1000 or less (tokens, Giant Germs).
- **Jigen Bakudan**: board-wipe-and-burn on your own side (use when you are losing anyway).

## F. What to test first
1. Scapegoat + Cannon Soldier lethal turns: this is already the champions' best finisher, only used on purpose 11 times.
2. Mystic Box + Ameba (2000) and Mystic Box + Griggle (+3000 LP).
3. Magic Thorn + Morphing Jar.
4. Horn of Heaven with sheep as the cost.
5. Mystic Box + sheep: confirm the position of the given sheep in a practice duel first.

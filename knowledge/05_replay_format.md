# Replay (.ydr) format, reverse-engineered

Tools: `tools/replay_decode.py <file.ydr>` prints a readable story. Outputs for your two replays are in `data/replays/`.
Validated only by reading the stories against the card database; **not yet confirmed by you**. Confidence marked below.

## File layout (confirmed)
| Offset | Content |
|---|---|
| 0 | `YGR\0` |
| 4-11 | version/signature (same as deck files: `01 f3 12 00 57 54 cb 3f`) |
| 12 | 0x514 (constant), then flag (1 in anas1 = YOU moved first; 0 in 0cards = OPP moved first), then a seed (u32) |
| 28 | Deck of player 1, then deck of player 2. Each = main, fusion, side lists (u16 count + u16 card IDs; same IDs as .ydc / `cards_all.csv` `deck_id`) |
| then | u32 N, then N events of 8 bytes: `op` (u32), `arg` (u32) |

Bit 15 of the event word means the **second** deck list in the file (labelled "YOU" in the decoder) and clear means the first list ("OPP"). **This is not "the user":** the user is the second list in `anas1` and `0cards_deck_win` but the first list in `no_bas_1-6`, so the side that is you has to be given per replay (`data/user_sides.json`). Winner/loser analysis does not depend on it.

**Hand slot (new):** for `0xCE`/`0xCF` the low byte of the argument is the 0-based position of the played card in the hand (slot 0 = first card). The log does not reveal drawn cards, so the decoder tracks hand size from draws, plays, hand limit and known effects (Graceful Charity, Morphing Jar, Cyber Jar, Sangan/Witch searches) and corrects upwards when a slot proves the hand is larger. It reports "card k of N in hand" for every play and the library size.

## Event word
`op` = `[hi16][bit15 = YOU?][low15 = event code]`. Bit 15 set = YOU (second deck), clear = OPP.
`hi16` is a card ID for card events, or a small number (slot, count, LP amount) otherwise.

## Event codes
| Code | Meaning | Confidence |
|---|---|---|
| 0x61 | draw (arg = number of cards; initial draw arg=5 each) | high |
| 0x01 | turn start (marker). 0x02/0x03 turn end | high |
| 0x50 draw phase, 0x51 standby, 0x52 main 1, 0x53 battle, 0x54 main 2, 0x55 end phase | high (by order within turn) |
| 0x04 | duel end | high |
| 0xCE (card) | monster summon/set. arg bits: 24 = set face-down (else face-up Attack summon), bits 8-15 = monster zone (0-4), bits 0-7 = hand slot. **Confirmed by you on anas1 turns 1-3 and 5.** | high |
| 0xCF (card) | Spell/Trap: bit 16 = activated (else set), bits 8-11 = S/T zone (5-9), bits 0-7 = hand slot. Matches your Ring of Destruction set on turn 5 and Pot of Greed activation. | high |
| 0xE6 (card) | select / flip a card (precedes CE for Flip Summon) | medium |
| 0x72 (card) | card effect resolving | medium |
| 0x75 + 0x20 (card) | card enters a hand (draws, Cyber Jar reveal, search) | medium |
| 0x79 | monsters destroyed / sent to Graveyard (hi = count) | medium |
| 0x34 | attack declared; hi = attacker slot | medium-high |
| 0x31 (hi>0) | battle damage popup, hi = damage | medium-high |
| 0x42/0x43 | life point change; hi = amount; arg 0x10000 = damage to opponent of the active player, arg 0 = paid by the active player (e.g. Imperial Order upkeep, Fairy Box) | medium |
| 0x0D, 0x0C, 0x0E, 0x56, 0x8F, 0x92, 0x88, 0xF1 ... | engine bookkeeping (zones, selection prompts, animation sync). Unmapped. | unknown |

Verified against your account of anas1.ydr: T1 Wall of Illusion set, opp set Cyber Jar, T3 Momonga set, opp flipped Cyber Jar, T5 Bazoo summoned, Ring of Destruction set then triggered on Slate Warrior (1900 to both sides). Still open: Flip Summon vs Special Summon encoding, and the Defense/Attack choice for Summons from effects.


## Battle and board events (decoded from your anas1 replay; verified by the stories below)
| Code | Meaning |
|---|---|
| 0x33 | attack on a monster: hi = attacker zone, arg low byte = target zone on the other side |
| 0x34 | direct attack: hi = attacker zone |
| 0x3C | monster at (side, zone hi) destroyed in battle |
| 0x7C | monster at (side, zone hi) leaves the field to the Graveyard |
| 0x43 | LP **loss** for the flagged side (hi = amount). arg 0 = self-inflicted cost (Imperial Order upkeep), 0x10000 = damage taken, 1 = Ring of Destruction style |
| 0x42 | LP **gain** for the flagged side (hi = amount; Nimble Momonga +1000, Solemn Wishes +500) |
| 0x70 | special summon: hi = (zone << 8) | 1 for YOU, 0 for OPP |
| 0x80 then 0x75 | flip/reveal: 0x80 hi = zone, the next 0x75 names the card now face-up |
| 0x72 (Wall of Illusion) | Wall triggered: the attacker returns to its owner's hand and damage is still dealt normally |
Verified: anas1 LP totals reproduce exactly (OPP 8000 -> -150 on your 3-attack finish, YOU 8100) and your final attack is Wall of Illusion (zone 2).
The identity of Cyber Jar summons is not in the log; the decoder fills it in when a card is revealed, attacked or destroyed.

## Replay stats
| File | Turns | Result | Notes |
|---|---|---|---|
| `anas1.ydr` | 7 | YOU won on turn 7 with a 3-attack finish (1400+1000+1000) | YOU played a Wall of Illusion / Bazoo / Dream Clown / Ring of Destruction style deck; OPP opened Cyber Jar then Heavy Storm, Imperial Order |
| `0cards_deck_win.ydr` | 44 | YOU won (last events are your damage 3100 + 1000 then DUEL END) | long stall game: OPP deck has Solemn Wishes x3, Needle Worm, Gravekeeper's Servant, Magic Drain x3; YOU used Fairy Box, Mirror Force, Heavy Storm, Robbin' Goblin |


## Header fields (decoded)
| Offset | Meaning |
|---|---|
| 12 | 0x514 constant |
| 16 | **Recorder**: 1 = the player who saved the replay is the *second* deck list, 0 = the first. Matches your own games 8 of 8 (anas1 and 0cards = 1, no_bas_1-6 = 0). |
| 20 | **Who moves first**: 1 = the second deck list moves first, 0 = the first list |
| 24 | Shuffle seed (a Unix timestamp: C `srand(time(0))`) |

## Shuffle (reverse-engineered), so hands can be reconstructed
The log never lists drawn cards, but the game's shuffle is deterministic:
1. generator: MSVC `rand()` seeded with the header seed (state = state*214013+2531011; value = bits 16-30)
2. the deck of the player who moves first is shuffled first, then one `rand()` value is discarded, then the other deck is shuffled
3. shuffle: for i = n-1 down to 1: j = (rand() * (i+1)) >> 15; swap(d[i], d[j])
4. the top of the library is index 0; the opening hand is the top 5, then one card per draw
Implemented in `tools/hands.py`; `tools/validate_hands.py` checks it: in 437 of 490 player-sides (89%) every card played on the first turn is inside the reconstructed opening hand plus first draw. A random order would pass in a tiny fraction of cases.
Limits: the hand is exact until a card shuffles or searches that player's deck (Sangan, Witch, Giant Rat, Mystic Tomato, Giant Germ, Nimble Momonga, Last Will ...), because the player's choice and the extra shuffle are not in the log. After that the decoder lists the known cards plus "+N unknown". Discards by Graceful Charity or the hand limit are marked "up to N already discarded". About 13% of sides disagree with the reconstruction (reason not yet found); those are flagged "partly unknown" from the first inconsistent play.

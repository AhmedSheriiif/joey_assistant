# Audit of your lost duel: no_bas_3 (the one game you lost in the `no_bas` series)

Tool: `python tools/audit_replay.py "%APPDATA%\Yu-Gi-Oh! Power of Chaos Common\no_bas_3.ydr"`
Hands come from the reconstructed shuffle (exact until a search effect), fields from the log (can be off after complex effects). Everything below is an estimate.

## Did you have a kill?
No. On none of your turns did a visible line reach his life points. At turn 12 (the last chance) the best line with the cards we can see
(Monster Reborn + Call of the Haunted + United We Stand, then attacks) dealt 3500 against his 4900 LP; you actually dealt 2600 (1400 battle + 1200 Amazon Archer burn... his burn).
Your hand beyond the visible cards is unknown after the first search effect, so a hidden lethal cannot be ruled out, but nothing in the log suggests one.

## Did the danger check warn you? Yes, at the turn that mattered
| End of your turn | Your LP | His worst-case estimate | What he did next turn |
|---|---|---|---|
| 2 | 8000 | 1450 (ok) | 0 |
| 4 | 8000 | 3300 (caution) | 0 |
| 8 | 6600 | 3950 (caution) | 0 |
| 10 | 6600 | 5200 (danger) | 0 |
| **12** | **6200** | **6700 (LETHAL)** | **6600** |

His real kill on turn 13: Snatch Steal, Nobleman of Crossout, Premature Burial, Monster Reborn, MST and United We Stand, then 4100 + 2500 direct. The "Spell OTK package" tier (steal one monster, destroy one, revive two from his Graveyard, United We Stand) predicted 6700; he dealt 6600.
The reconstruction also shows what he held: from turn 11 his hand contained Monster Reborn, MST, Snatch Steal and Torrential Tribute (plus cards not visible) — exactly the pieces of that kill.

## Could you have survived? Probably, by a small margin
You needed more than 6600 life at the end of turn 12 and had 6200.
In turn 12 you lost 500 LP when Man-Eater Bug attacked into Bazoo (1600) and 900 when Nimble Momonga attacked into Bazoo (you gained 1000 back from Momonga's effect), net -400, before the third attacker (the one with United We Stand) destroyed Bazoo for free.
- Attacking with the boosted monster first would have killed Bazoo without the 500-LP loss: you end at about 6700, which survives his 6600 by 100.
- Not trading the extra bodies, or keeping a defensive card for the turn (Waboku, Kuriboh, Swords of Revealing Light, Imperial Order against his Spell package), would have changed the margin more.
It was close: one attack order, 500 life points. This is a counterfactual from the log; the real game could differ if his unseen cards were different.

## What to take from it
1. Before ending your turn, add up his possible kill (the package tier). If it is at or above your life points, keep life points and blockers instead of attacking with weak monsters.
2. Attack with the strongest or boosted monster first when a stronger blocker is the only target; each weak attack into a bigger monster costs life.
3. Hold Waboku / Kuriboh for the turn he has Snatch Steal + Monster Reborn + equip in hand.

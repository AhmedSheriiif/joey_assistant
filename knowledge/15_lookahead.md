# Lookahead: one-turn-kill check and danger check

Script: `tools/lookahead.py` (also built into `tools/advisor.py` when you describe the boards).
It models the patterns that ended games in the replays: clear or steal the blockers, summon or revive a body, equip, hit directly, then burn with
Cannon Soldier / Amazon Archer / Catapult Turtle. It is a planner for those patterns, not a full rules engine.

## Describe the board
```
python tools/advisor.py --hand "Mystical Space Typhoon, Sangan, United We Stand, Change of Heart" \
   --my-monsters "Giant Rat, Amazon Archer/s" --opp-monsters "Jinzo" --lp-me 8000 --lp-opp 8000 --opp-st 1
```
Monsters: `Name` face-up Attack, `Name/d` Defense, `Name/s` Set face-down, `?` an unknown Set monster (assumed 1400/1200), `Name@2200` current ATK.
`--opp-st` is the number of Set Spell/Trap cards he has; `--my-st` your own (for Mage Power); `--gy-best` the best monster in a Graveyard (Monster Reborn).

## 1. Can you kill this turn?
The planner tries every combination of the playable cards in your hand (removal, steals, one summon, revive, equips, Scapegoat tokens, flat burn) and
reports the best line, plus the lethal lines ordered by how few of his Set cards remain. It prints the damage of each step. Rules it knows:
- you cannot attack directly while he has a monster; blockers are removed by Raigeki, Dark Hole, Change of Heart / Snatch Steal, Mystic Box, Nobleman (Set monsters) or your flip monsters
- United We Stand (+800 per monster you control), Mage Power (+500 per Spell/Trap), Rush Recklessly, Kunai, Axe of Despair, Megamorph (doubles the original ATK only if your LP are lower), Limiter Removal (Machines)
- Hayabusa Knight attacks twice; Zombyra cannot attack directly
- burn after battle: Cannon Soldier 500 per other monster, Amazon Archer 1200 per two, Catapult Turtle half the ATK of a Tributed monster; Scapegoat makes four tokens for that burn
- his Set cards: the planner says whether the line also survives a trap (if the burn alone is lethal) or tells you to clear them first.
It does not model chains, his hand, Jinzo, Imperial Order or monster effects it was not told about.

Checked on the turn-4 kill from your `no_bas_1` game: it finds Change of Heart on his Jinzo, Sangan, United We Stand on Giant Rat, direct hits and an Amazon Archer burn.

## 2. Is he about to kill you?
Three tiers of his damage next turn against your current field: board only, one typical boost (United We Stand / Rush Recklessly), and "he takes your best monster with Change of Heart and boosts". Each is labelled ok / caution / danger / LETHAL against your life points, together with the
share of turns in the replays in which a player with that many monsters reached that much damage. If a tier is lethal it lists defensive ideas (extra blockers, Scapegoat, Waboku / Kuriboh / Swords, Imperial Order against Spell-based plans).
Replays say how real the threat is: 73 turns dealt 3000+ damage and 17 games were won from 7000+ life in one turn.

## Limits
Assumes his hand is empty beyond the tiers above; unknown Set monsters use a default; a Set trap can break any line. Use it as a checklist before ending a turn, not as a proof.

## Audit a finished duel
`python tools/audit_replay.py REPLAY.ydr [--me YOU|OPP]` goes through every turn of one side: did a kill exist, and what did the danger check say at the end of each turn compared with what the opponent really dealt.
The danger check has a fourth tier since the audit of your lost duel: the Spell OTK package (steal one monster, destroy one, revive two from his Graveyard, United We Stand).
Example: `knowledge/16_audit_no_bas_3.md`.

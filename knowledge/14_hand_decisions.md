# What the hands show: opening hands, holding cards, and a play-choice model

Built from the 241 replays with reconstructed hands (see `05_replay_format.md`). Only decisions whose hand is exact are used:
482 opening hands, 4,860 plays/end-of-turn decisions (2,347 by winners). Script: `tools/train_policy.py`. Advisor: `tools/advisor.py`.
Caution: the replay set is dominated by a few series (see `11_model_findings.md`), so card-level numbers mix card strength with pilot skill.

## 1. Opening hands (the first 5 cards)
- The shape of the opener barely matters: win rate by number of monsters in the opening 5 was 43% (0), 50% (1), 49% (2), 51% (3), 54% (4), 40% (5). Level 4 or lower monsters: 46% (0) to 54% (4). **There is no clear "good hand" signature, so there is nothing to gain from worrying about opener composition.**
- Cards in the opener whose owners won more (n in brackets, base rate 50%): Cannon Soldier 78% (27), Morphing Jar 68% (63), Torrential Tribute 59% (37), Man-Eater Bug 59% (51), Magic Cylinder 59% (34), Scapegoat 57% (74), MST 56% (68).
- Below base: United We Stand 37% (41), Amazon Archer 43% (28), Pot of Greed 47% (34). Interpretation: United We Stand and Archer are finishers, they do little in a 5-card hand without bodies; most other results are within noise.

## 2. Hold or play
Share of times a card that is in the hand at the start of the turn is still in the hand at the end of the turn (exact hands only):
- **Played at once:** MST 39% held, Nimble Momonga 42%, Man-Eater Bug 43%, Sangan 51%, Mystic Tomato 52%, Giant Rat 56%, Swords of Revealing Light 57%, Nobleman 59%, Scapegoat 59%, Dimensional Warrior 59%.
- **Held for later:** Jinzo 86%, Monster Reborn 81%, Morphing Jar 81%, Premature Burial 80%, Fissure 79%, Dark Hole 79%, Giant Trunade 78%, United We Stand 77%, Amazon Archer 73%. (The Rock Spirit shows 99% because it cannot be played from the hand.)
- **Winners hold power cards slightly longer than losers:** Jinzo 91% vs 81%, Monster Reborn 86% vs 78%, Premature Burial 86% vs 75%, Dark Hole 82% vs 76%, Fissure 84% vs 74%. Losers spend them sooner.
- So: cheap searchers and bodies are put down immediately; recursion, board wipes and finishers are saved until they have a target or a lethal use.

## 3. Play-choice model (hand + board -> next action)
For each decision, the candidates are the distinct cards in the hand plus "end the turn". An XGBoost ranker is trained on the winners' choices and tested on decks it has not seen (grouped cross-validation).
- It ranks the action the winner actually took first 58% of the time and within the top 3 in 92% of decisions. A popularity baseline (most commonly played card) gets 41% and 83%.
- What it learned: mostly the rules (monsters unavailable after the Normal Summon), then hand size and board counts. Graveyard and Set-card counts did not add accuracy.
- Winners end the turn without playing the rest of the hand in 795 of 2,347 decisions (34%): holding cards is normal.
- **Limits:** it imitates; it does not look ahead and does not know the opponent's hand. It needs the legal-move filter below, because as a pure imitation it will suggest cards with no target.

## 4. The advisor
```
python tools/advisor.py --hand "Change of Heart, Giant Trunade, Jinzo, Monster Reborn, The Rock Spirit, Man-Eater Bug" --turn 1 --my-st 0 --opp-st 0
```
Inputs: your hand (card names), life points, monsters on each side, turn number, whether you already used your Normal Summon (`--normal-used`), and optionally graveyard and Spell/Trap counts. It prints the actions ranked by how often winners did them in a similar state, after removing cards that have no target (for example Change of Heart with no opposing monster).
It is a first version: use it as "what winners usually do here", not as a solver.

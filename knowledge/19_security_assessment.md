# What the game exposes, and how to defend a tournament (design-level assessment)

Scope: I analysed the game's files and the replays. I did **not** build, and will not build, a tool that reads an opponent's hidden information (hand, Set cards, Rock-Paper-Scissors choice) from a live game against another person: that is a cheat for use against real opponents. Below is what is exposed in principle and what an organiser can do about it.

## What I found in `joey_pc.exe` (read-only analysis, `tools/pe_info.py`)
- 32-bit Windows program from 2004, fixed load address (no ASLR), no DEP.
- It imports no anti-debug, anti-tamper or integrity functions. Its networking is not in its imports (no Winsock): LAN/online play goes through DirectPlay-style components and the external Battle.LAN / GameRanger tools.
- Our own edits to `data.dat` and `Voice.dat` (the quiet patch) ran without any complaint: the game does not check its data files.
- Consequence: nothing in the client stops another program from reading its memory, and nothing detects modified game data. Every player's client is also fully trusted by the other.

## The design leak (this needs no memory reading at all)
- Each replay stores both decks, in full, plus a seed, and the game's shuffle is a plain C random generator.
  I reconstructed both players' opening hands and draws from those two things alone: 89% of player-sides matched on their first turn.
- A live game has to exchange the same ingredients (both decks and the seed) when it starts. Anyone who can read them from the process or the network can compute the opponent's hand until a search effect changes it. This is a property of the protocol, so a patch to one client cannot fix it.
- Set cards, the opponent's hand size and card positions are in the same shared state. The log is omniscient (the replays show every Set card), which suggests the clients keep it too.
- The Rock-Paper-Scissors choice is the same kind of exposure if each client sends its choice to the other before both are revealed. I did not test this.

## Defences that work
1. **Verify the installation.** `python tools/verify_install.py` prints the size and SHA-256 of `joey_pc.exe`, `data.dat` and `Voice.dat`. Organisers publish the expected values (take them from an unpatched installation: the copy on this PC currently has the quiet patch applied, so its `data.dat` and `Voice.dat` hashes are not the originals); players run it before a match. (My quiet patch changes `data.dat` and `Voice.dat`: restore the originals with `python tools/quiet_joey.py --restore` before any event that checks hashes.)
2. **Play on organiser-controlled machines or with screen sharing**, and run no other programs. Memory readers cannot be detected reliably from inside the game.
3. **Replay audit.** Every game saves a replay. Hidden-information abuse leaves statistical traces:
   - attacking into Set traps: a player who cannot see Set cards attacks at the same rate whether or not a punishing trap is Set. In the 240 replays the population rate is 56.9% with a punishing trap Set vs 57.3% without. A player who knows the cards shows a large gap.
   - a player's play against hidden Set monsters (attacking face-down Flip monsters, Man-Eater Bug) and against Mirror Force / Torrential / Magic Cylinder.
   Per-deck gaps in the current data are noisy (sd 0.24 with 8+ samples each), so this needs 60+ opportunities per player for a z-score, and is a screening tool, not proof.
4. **First-turn choice** by an organiser coin toss or a commit-reveal message in chat instead of the in-game Rock-Paper-Scissors.
5. **Best-of-three consistency:** compare a player's results against his own history.

## Ideas for our own web game (the protocol cannot leak)
- Server-authoritative state: each player only receives his own hand and the public board.
- Shuffle by commit-reveal: both players commit to a seed hash, then reveal; or a trusted server shuffles and never sends the opponent's order.
- Rock-Paper-Scissors as simultaneous commit/reveal handled by the server.
- Replays store only public information plus each player's own hand.

## Practice helpers that are fine
Hotkeys for our advisor (read my own hand and the public board from the screen, show lethal/danger checks) and speed-ups like `-speedy`. They use only what you can see.

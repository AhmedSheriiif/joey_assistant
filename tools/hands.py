"""Recreate each player's shuffled deck from a replay's seed.

Reverse-engineered from the replays (see knowledge/05_replay_format.md):
  * header seed = C runtime srand() value, generator = MSVC rand() (LCG 214013/2531011, bits 16-30)
  * the player who moves first has his deck shuffled first, then one rand() call is discarded, then the other deck is shuffled
  * shuffle: for i = n-1 down to 1: j = (rand() * (i+1)) >> 15; swap(d[i], d[j])
  * the top of the library is index 0 (5 cards in the opening hand, then one per draw)
Exact until a card effect reshuffles or searches that player's deck, because those depend on the player's choices.
"""

M32 = 0xFFFFFFFF


def rand_stream(seed):
    s = [seed & M32]

    def f():
        s[0] = (s[0] * 214013 + 2531011) & M32
        return (s[0] >> 16) & 0x7FFF
    return f


def shuffle(deck, f):
    d = list(deck)
    for i in range(len(d) - 1, 0, -1):
        j = (f() * (i + 1)) >> 15
        d[i], d[j] = d[j], d[i]
    return d


def initial_libraries(decks, seed, first_list):
    """decks = [first list, second list] (main decks); first_list = index (0/1) of the list that moves first.
    Returns {'OPP': library of the first list, 'YOU': library of the second list} (decoder labels)."""
    f = rand_stream(seed)
    libs = {}
    libs[first_list] = shuffle(decks[first_list][0], f)
    f()
    libs[1 - first_list] = shuffle(decks[1 - first_list][0], f)
    return {"OPP": libs[0], "YOU": libs[1]}

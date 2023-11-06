import itertools

from typing import Iterable

def get_combos(
    l: Iterable,
    max_group: int,
) -> Iterable:

    # Get sets of combos (len 1, 2, ..., max_group)
    results = [itertools.combinations(l, r=i) for i in range(1, max_group + 1)]

    # Flatten list
    results = [y for x in results for y in x]
    
    return results
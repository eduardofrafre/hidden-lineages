"""List southern species whose barcodes fall in more than one BIN, in four sections.

A BIN belongs to the name holding most of its records. For each split species:
- its own BINs are the ones it holds the majority of;
- records in a BIN another name owns are probable misidentifications, not a lineage;
- a BIN with no majority name is mixed, a naming problem shared by every name in it.

Sections, each species in one only:
1. Candidates: 2 or more own BINs, the second with 2 or more sequences. Ranked by
   second own BIN size, then n.
2. Naming problems: species with a mixed BIN, one entry per group of names linked
   through mixed BINs (so one bad BIN is counted once, not once per name).
3. Probable misidentifications: the extra BINs are owned by other names.
4. Single-sequence splits: the second own BIN holds one sequence. Ranked last.
"""
import sys
from collections import Counter, defaultdict

from bold import barcodes, download

cls = sys.argv[1] if len(sys.argv) > 1 else "Teleostei"
species = defaultdict(Counter)
bin_names = defaultdict(Counter)
lats = defaultdict(list)
order = {}
for row in barcodes(download("geo:country/ocean:Brazil", "brazil")):
    if row["class"] == cls:
        species[row["species"]][row["bin_uri"]] += 1
        bin_names[row["bin_uri"]][row["species"]] += 1
        lats[row["species"], row["bin_uri"]].append(row["_coord"][0])
        order[row["species"]] = row["order"]


def owner(b):
    (name, n), = bin_names[b].most_common(1)
    return name if n * 2 > sum(bin_names[b].values()) else None


def describe(name):
    bins = species[name]
    parts = []
    for b, c in bins.most_common():
        lat = sum(lats[name, b]) / c
        o = owner(b)
        tag = "" if o == name else f" [{o}'s]" if o else " [mixed]"
        parts.append(f"{b} n={c} lat={lat:.1f}{tag}")
    return f"{name:30} {order[name]:20} n={sum(bins.values()):<4} {', '.join(parts)}"


splits = {name: bins for name, bins in species.items() if sum(bins.values()) >= 5 and len(bins) >= 2}
mixed = {name for name, bins in splits.items() if any(owner(b) is None for b in bins)}

candidates, misids, singles = [], [], []
for name, bins in splits.items():
    own = sorted(c for b, c in bins.items() if owner(b) == name)
    key = (own[-2] if len(own) > 1 else 0, sum(bins.values()), name)
    if len(own) > 1 and own[-2] >= 2:
        candidates.append(key)
    elif name in mixed:
        continue
    elif len(own) > 1:
        singles.append(key)
    else:
        misids.append(key)

# Link the remaining mixed-BIN species through their mixed BINs, transitively.
placed = {name for _, _, name in candidates}
groups, seen = [], set()
for name in sorted(mixed - placed):
    if name in seen:
        continue
    group, todo = set(), [name]
    while todo:
        n = todo.pop()
        if n not in group:
            group.add(n)
            todo += [m for b in species[n] if owner(b) is None for m in bin_names[b]]
    seen |= group
    groups.append(group)
groups.sort(key=lambda g: -sum(sum(species[n].values()) for n in g))

print(f"Candidates ({len(candidates)})")
for _, _, name in sorted(candidates, reverse=True):
    print("  " + describe(name))

print(f"\nNaming problems ({len(groups)} groups)")
for g in groups:
    bins = sorted({b for n in g for b in species[n] if owner(b) is None})
    others = sorted(g - splits.keys())
    print(f"  mixed {', '.join(bins)}" + (f"; also {', '.join(others)}" if others else ""))
    for name in sorted(g & splits.keys() - placed):
        print("    " + describe(name))

print(f"\nProbable misidentifications ({len(misids)})")
for _, _, name in sorted(misids, reverse=True):
    print("  " + describe(name))

print(f"\nSingle-sequence splits ({len(singles)})")
for _, _, name in sorted(singles, reverse=True):
    print("  " + describe(name))

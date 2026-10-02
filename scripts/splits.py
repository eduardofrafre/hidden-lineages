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


def load(cls):
    """Per species BIN counts, per BIN name counts, mean latitudes and orders for one class."""
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
    return species, bin_names, lats, order


def owner(bin_names, b):
    (name, n), = bin_names[b].most_common(1)
    return name if n * 2 > sum(bin_names[b].values()) else None


def classify(species, bin_names):
    """Return the four ranked sections: candidates, naming-problem groups, misidentifications, singles."""
    owner_ = lambda b: owner(bin_names, b)
    splits = {name: bins for name, bins in species.items() if sum(bins.values()) >= 5 and len(bins) >= 2}
    mixed = {name for name, bins in splits.items() if any(owner_(b) is None for b in bins)}

    candidates, misids, singles = [], [], []
    for name, bins in splits.items():
        own = sorted(c for b, c in bins.items() if owner_(b) == name)
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
                todo += [m for b in species[n] if owner_(b) is None for m in bin_names[b]]
        seen |= group
        groups.append(group)
    groups.sort(key=lambda g: -sum(sum(species[n].values()) for n in g))
    return ([n for _, _, n in sorted(candidates, reverse=True)], groups,
            [n for _, _, n in sorted(misids, reverse=True)], [n for _, _, n in sorted(singles, reverse=True)])


def section(species, bin_names):
    """Map each split species to the section it lands in."""
    candidates, groups, misids, singles = classify(species, bin_names)
    out = {n: "candidate" for n in candidates}
    out.update({n: "naming problem" for g in groups for n in g if n not in out})
    out.update({n: "misidentification" for n in misids})
    out.update({n: "single-sequence" for n in singles})
    return out


if __name__ == "__main__":
    species, bin_names, lats, order = load(sys.argv[1] if len(sys.argv) > 1 else "Teleostei")
    splits = {name: bins for name, bins in species.items() if sum(bins.values()) >= 5 and len(bins) >= 2}

    def describe(name):
        parts = []
        for b, c in species[name].most_common():
            o = owner(bin_names, b)
            tag = "" if o == name else f" [{o}'s]" if o else " [mixed]"
            parts.append(f"{b} n={c} lat={sum(lats[name, b]) / c:.1f}{tag}")
        return f"{name:30} {order[name]:20} n={sum(species[name].values()):<4} {', '.join(parts)}"

    candidates, groups, misids, singles = classify(species, bin_names)
    print(f"Candidates ({len(candidates)})")
    for name in candidates:
        print("  " + describe(name))

    print(f"\nNaming problems ({len(groups)} groups)")
    for g in groups:
        bins = sorted({b for n in g for b in species[n] if owner(bin_names, b) is None})
        others = sorted(g - splits.keys())
        print(f"  mixed {', '.join(bins)}" + (f"; also {', '.join(others)}" if others else ""))
        for name in sorted(g & splits.keys() - set(candidates)):
            print("    " + describe(name))

    print(f"\nProbable misidentifications ({len(misids)})")
    for name in misids:
        print("  " + describe(name))

    print(f"\nSingle-sequence splits ({len(singles)})")
    for name in singles:
        print("  " + describe(name))

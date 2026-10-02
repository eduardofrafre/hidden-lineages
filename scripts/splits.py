"""List southern species whose barcodes fall in more than one BIN, in four sections.

A BIN belongs to the name holding most of its records. For each split species:
- its own BINs are the ones it holds the majority of;
- records in a BIN another name owns are probable misidentifications, not a lineage;
- a BIN with no majority name is mixed, a naming problem shared by every name in it.

Sections, each species in one only:
1. Candidates: 2 or more own BINs, the second with 2 or more sequences. Ranked by
   ASAP support first (see support()), then second own BIN size, then n.
2. Naming problems: species with a mixed BIN, one entry per group of names linked
   through mixed BINs (so one bad BIN is counted once, not once per name).
3. Probable misidentifications: the extra BINs are owned by other names.
4. Single-sequence splits: the second own BIN holds one sequence. Ranked last.
"""
import csv
import sys
from collections import Counter, defaultdict

from bold import DATA, barcodes, download



def support(row):
    """How strongly ASAP backs the BIN split, from its p-value for the partition that
    matches the BINs (scripts/asap.py), wherever ASAP ranked that partition.
    3: listed, p < 0.05. 2: listed, p >= 0.05. 1: not listed, but ASAP's best
    partition still separates some BINs. 0: no support, or ASAP not run."""
    if not row:
        return 0
    if int(row["bin_rank"]):
        return 3 if float(row["bin_p"]) < 0.05 else 2
    return 1 if row["vs_bins"] in ("merges", "splits", "conflicts", "agrees") else 0


def asap_results():
    """species -> row of data/asap/results.tsv, empty if ASAP has not been run."""
    path = DATA / "asap" / "results.tsv"
    if not path.exists():
        return {}
    return {r["species"]: r for r in csv.DictReader(open(path), delimiter="\t")}


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


def classify(species, bin_names, asap=None):
    """Return the four ranked sections: candidates, naming-problem groups, misidentifications, singles."""
    asap = asap_results() if asap is None else asap
    owner_ = lambda b: owner(bin_names, b)
    splits = {name: bins for name, bins in species.items() if sum(bins.values()) >= 5 and len(bins) >= 2}
    mixed = {name for name, bins in splits.items() if any(owner_(b) is None for b in bins)}

    candidates, misids, singles = [], [], []
    for name, bins in splits.items():
        own = sorted(c for b, c in bins.items() if owner_(b) == name)
        key = (support(asap.get(name)), own[-2] if len(own) > 1 else 0, sum(bins.values()), name)
        if len(own) > 1 and own[-2] >= 2:
            candidates.append(key)
        elif name in mixed:
            continue
        elif len(own) > 1:
            singles.append(key)
        else:
            misids.append(key)

    # Link the remaining mixed-BIN species through their mixed BINs, transitively.
    placed = {key[-1] for key in candidates}
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
    ranked = lambda keys: [key[-1] for key in sorted(keys, reverse=True)]
    return ranked(candidates), groups, ranked(misids), ranked(singles)


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
    asap = asap_results()
    splits = {name: bins for name, bins in species.items() if sum(bins.values()) >= 5 and len(bins) >= 2}

    def describe(name):
        parts = []
        for b, c in species[name].most_common():
            o = owner(bin_names, b)
            tag = "" if o == name else f" [{o}'s]" if o else " [mixed]"
            parts.append(f"{b} n={c} lat={sum(lats[name, b]) / c:.1f}{tag}")
        a = asap.get(name)
        note = ""
        if a:
            gap = f"BIN split rank {a['bin_rank']}, p={float(a['bin_p']):.0e}" if int(a["bin_rank"]) else "BIN split not listed"
            note = f"  ASAP: {gap}; best {a['asap_groups']} groups at {float(a['threshold']) * 100:.1f}%"
        return f"{name:30} {order[name]:20} n={sum(species[name].values()):<4} {', '.join(parts)}{note}"

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

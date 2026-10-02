"""Score the fish BIN splits against benchmark.tsv. Criteria in TEST.md."""
import csv
from collections import Counter, defaultdict
from pathlib import Path

from bold import barcodes, download

ROOT = Path(__file__).resolve().parent.parent
DEEP = {"Ancistrus cirrhosus", "Astyanax altiparanae", "Hoplias intermedius", "Iheringichthys labrosus",
        "Piabina argentea", "Pseudoplatystoma reticulatum", "Rineloricaria latirostris",
        "Synbranchus marmoratus", "Cetopsorhamdia iheringi", "Rhamdia quelen"}

species = defaultdict(list)
bin_names = defaultdict(set)
for row in barcodes(download("geo:country/ocean:Brazil", "brazil")):
    bin_names[row["bin_uri"]].add(row["species"])
    if row["class"] == "Teleostei":
        species[row["species"]].append(row["bin_uri"])

bench = list(csv.DictReader(open(ROOT / "benchmark.tsv"), delimiter="\t"))
scored = {"deep": [0, 0], "all": [0, 0]}
names_in_bench = set()
print(f"{'species':30}{'n':>4}{'bins':>5}  result")
for b in bench:
    names = b["bold_names"].split(",")
    names_in_bench.update(names)
    bins = [x for n in names for x in species.get(n, [])]
    n, k = len(bins), len(set(bins))
    if n < 5:
        print(f"{b['species']:30}{n:4}{k:5}  not testable")
        continue
    hit = k >= 2
    for key in ["all"] + (["deep"] if b["species"] in DEEP else []):
        scored[key][0] += hit
        scored[key][1] += 1
    print(f"{b['species']:30}{n:4}{k:5}  {'FLAGGED' if hit else 'missed'}")

for key, (hit, total) in scored.items():
    print(f"recall {key}: {hit}/{total}")

print("\nStrongest non-benchmark flags (second-largest BIN size, then n):")
others = []
for name, bins in species.items():
    c = Counter(bins)
    if name in names_in_bench or len(bins) < 5 or len(c) < 2:
        continue
    shared = [b for b in c if len(bin_names[b]) > 1]
    others.append((sorted(c.values())[-2], len(bins), name, c.most_common(), shared))
for second, n, name, c, shared in sorted(others, reverse=True)[:10]:
    note = "; ".join(f"{b} also holds {', '.join(sorted(bin_names[b] - {name}))}" for b in shared)
    print(f"  {name:28} n={n:<3} bins={[v for _, v in c]}  {note}")

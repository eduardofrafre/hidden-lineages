"""Score the insect BIN splits against benchmark-insects.tsv. Criteria in TEST.md."""
import csv
from collections import Counter
from pathlib import Path

from splits import load, section

ROOT = Path(__file__).resolve().parent.parent

species, bin_names, _, _ = load("Insecta")
where = section(species, bin_names)

bench = list(csv.DictReader(open(ROOT / "benchmark-insects.tsv"), delimiter="\t"))
scored = {k: [0, 0] for k in ("deep", "positive", "control", "ranking")}
names_in_bench = set()
print(f"{'species':28}{'kind':>10}{'n':>5}{'bins':>5}  result")
for b in bench:
    names = b["bold_names"].split(",")
    names_in_bench.update(names)
    bins = Counter()
    for n in names:
        bins.update(species.get(n, {}))
    n, k = sum(bins.values()), len(bins)
    if n < 5:
        print(f"{b['species']:28}{b['kind']:>10}{n:5}{k:5}  not testable")
        continue
    hit = k >= 2
    keys = {"deep": ["deep", "positive"], "shallow": ["positive"], "control": ["control"]}.get(b["kind"], [])
    for key in keys:
        scored[key][0] += hit
        scored[key][1] += 1
    sect = ", ".join(sorted({where[x] for x in names if x in where})) or "-"
    if hit and "positive" in keys:
        scored["ranking"][0] += "candidate" in sect
        scored["ranking"][1] += 1
    print(f"{b['species']:28}{b['kind']:>10}{n:5}{k:5}  {'FLAGGED' if hit else 'not flagged'}  section: {sect}")

print()
for key, (hit, total) in scored.items():
    label = {"deep": "deep recall", "positive": "overall recall", "control": "controls flagged",
             "ranking": "flagged positives in Candidates"}[key]
    print(f"{label}: {hit}/{total}")

print("\nStrongest non-benchmark candidates (second own BIN size, then n):")
others = [n for n, s in where.items() if s == "candidate" and n not in names_in_bench]
for name in others[:10]:
    print(f"  {name:30} n={sum(species[name].values()):<4} bins={sorted(species[name].values(), reverse=True)}")

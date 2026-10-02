"""List southern species whose barcodes fall in more than one BIN, largest second BIN first."""
import sys
from collections import Counter, defaultdict

from bold import barcodes, download

cls = sys.argv[1] if len(sys.argv) > 1 else "Teleostei"
species = defaultdict(list)
for row in barcodes(download("geo:country/ocean:Brazil", "brazil")):
    if row["class"] == cls:
        species[row["species"]].append(row)

rows = []
for name, recs in species.items():
    bins = Counter(r["bin_uri"] for r in recs)
    if len(recs) < 5 or len(bins) < 2:
        continue
    lat = {b: sum(r["_coord"][0] for r in recs if r["bin_uri"] == b) / n for b, n in bins.items()}
    rows.append((sorted(bins.values())[-2], len(recs), name, recs[0]["order"], bins.most_common(), lat))

for second, n, name, order, bins, lat in sorted(rows, reverse=True):
    detail = ", ".join(f"{b} n={c} lat={lat[b]:.1f}" for b, c in bins)
    print(f"{name:30} {order:20} n={n:<4} {detail}")

"""Coverage check: per class, how many southern species have enough barcodes to test."""
from collections import defaultdict

from bold import barcodes, download

MIN_RECORDS = 5
MIN_SPECIES = 50  # a class with fewer testable species is out of scope

by_class = defaultdict(lambda: defaultdict(list))
for row in barcodes(download("geo:country/ocean:Brazil", "brazil")):
    by_class[row["class"]][row["species"]].append(row["bin_uri"])

print(f"{'class':20}{'records':>8}{'species':>8}{'>=5':>6}{'split':>6}  in scope")
for cls, species in sorted(by_class.items(), key=lambda kv: -sum(map(len, kv[1].values()))):
    testable = [bins for bins in species.values() if len(bins) >= MIN_RECORDS]
    split = sum(1 for bins in testable if len(set(bins)) > 1)
    total = sum(map(len, species.values()))
    print(f"{cls or '?':20}{total:8}{len(species):8}{len(testable):6}{split:6}  {'yes' if len(testable) >= MIN_SPECIES else ''}")

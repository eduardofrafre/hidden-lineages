"""Write one aligned FASTA per split species, the input for ASAP.

Every southern species with 5+ barcodes in 2+ BINs, fish and insects, goes to
data/asap/<Genus_species>.fas. Headers are processid|BIN so ASAP's partitions map
back to BINs. Prints the alignment summary per species: kept, dropped, and the
median p-distance within and between BINs.
"""
from collections import defaultdict
from itertools import combinations
from statistics import median

from align import align, p_distance
from bold import DATA, barcodes, download

out = DATA / "asap"
out.mkdir(exist_ok=True)
recs = defaultdict(dict)
bin_of = {}
for row in barcodes(download("geo:country/ocean:Brazil", "brazil")):
    if row["class"] in ("Teleostei", "Insecta"):
        recs[row["class"], row["species"]][row["processid"]] = row["nuc"]
        bin_of[row["processid"]] = row["bin_uri"]

print(f"{'class':10} {'species':32} {'kept':>7}  within  between")
for (cls, name), seqs in sorted(recs.items()):
    if len(seqs) < 5 or len({bin_of[p] for p in seqs}) < 2:
        continue
    aligned, dropped = align(seqs)
    within, between = [], []
    for a, b in combinations(aligned, 2):
        d = p_distance(aligned[a], aligned[b])
        if d is not None:
            (within if bin_of[a] == bin_of[b] else between).append(d)
    with open(out / f"{name.replace(' ', '_')}.fas", "w") as f:
        for pid, s in aligned.items():
            f.write(f">{pid}|{bin_of[pid]}\n{s}\n")
    fmt = lambda v: f"{median(v) * 100:5.1f}%" if v else "     -"
    print(f"{cls:10} {name:32} {len(aligned):>3}/{len(seqs):<3}  {fmt(within)}  {fmt(between)}")

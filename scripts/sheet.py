"""Write the candidate sheet for one class: candidates-<class>.md at the repository root.

Every number comes from the pipeline: BINs and sites from the BOLD download,
distances from align.py, ASAP support from data/asap/results.tsv. The published
source next to a candidate comes from candidate-notes.tsv, kept by hand.
"""
import csv
import sys
from datetime import date
from itertools import product
from pathlib import Path
from statistics import median

from align import align, p_distance
from bold import DATA, barcodes, download
from geography import pattern
from splits import asap_results, classify, load, owner

ROOT = Path(__file__).resolve().parent.parent
cls = sys.argv[1] if len(sys.argv) > 1 else "Teleostei"

species, bin_names, coords, order = load(cls)
asap = asap_results()
candidates, groups, misids, _ = classify(species, bin_names, asap)
notes = {r["species"]: r for r in csv.DictReader(open(ROOT / "candidate-notes.tsv"), delimiter="\t")}
seqs = {}
for row in barcodes(download("geo:country/ocean:Brazil", "brazil")):
    if row["class"] == cls:
        seqs[row["processid"]] = (row["species"], row["bin_uri"], row["nuc"])


def gap(name, b1, b2):
    """Median and range of p-distance between the two BINs, in percent."""
    recs = {pid: nuc for pid, (sp, b, nuc) in seqs.items() if sp == name and b in (b1, b2)}
    aligned, _ = align(recs)
    side = {pid: seqs[pid][1] for pid in aligned}
    d = [p_distance(aligned[x], aligned[y]) for x, y in product(aligned, aligned)
         if side[x] == b1 and side[y] == b2]
    d = [v * 100 for v in d if v is not None]
    return median(d), min(d), max(d)


def strength(row):
    if not row or not int(row["bin_rank"]):
        return "ASAP does not separate these BINs"
    p = float(row["bin_p"])
    word = "supports" if p < 0.05 else "weakly supports"
    rank = "its first choice" if row["bin_rank"] == "1" else f"ranked {row['bin_rank']} among its partitions"
    return f"ASAP {word} the BIN split (p = {p:.0e}, {rank})"


def where(label, sa, sb, km):
    return {"together": f"collected together at a shared site (first BIN at {sa} sites, second at {sb})",
            "one shared site": "both BINs come from a single site",
            "apart": f"collected apart: {sa} and {sb} sites, closest {km:.0f} km",
            "too few sites": f"second BIN known from {sb} site{'s' if sb > 1 else ''}, {km:.0f} km from the nearest site of the first"}[label]


out = [f"# Candidate cryptic species: {cls}, southern Atlantic Forest", "",
       f"Generated {date.today().isoformat()} from public BOLD records for Paraná, Santa Catarina and Rio Grande do Sul "
       f"(downloaded {date.fromtimestamp((DATA / 'brazil.tsv').stat().st_mtime).isoformat()}).", "",
       "Each entry is a **candidate**: a named species whose southern COI barcodes fall in two or more BINs "
       "the species itself dominates. It is a lead for a specialist, not a claim that a species is new. "
       "COI alone cannot tell a cryptic species from introgression, incomplete lineage sorting, a pseudogene "
       "or a misidentified voucher; nuclear markers and morphology can.", "",
       "For each: the BINs with record counts, the COI distance between the two largest BINs the species "
       "dominates (uncorrected p-distance), "
       "whether ASAP (Puillandre et al. 2021) finds a barcode gap at the BIN boundary, where the BINs were "
       "collected, and what is already published.", ""]

for i, name in enumerate(candidates, 1):
    b1, b2 = [b for b, _ in species[name].most_common() if owner(bin_names, b) == name][:2]
    med, lo, hi = gap(name, b1, b2)
    label, sa, sb, km = pattern(coords[name, b1], coords[name, b2])
    bins = ", ".join(f"{b} ({c})" for b, c in species[name].most_common())
    note = notes.get(name, {})
    out += [f"## {i}. *{name}* ({order[name]}, {sum(species[name].values())} barcodes)", "",
            f"- BINs: {bins}",
            f"- Distance between the two largest: {med:.1f}% (range {lo:.1f} to {hi:.1f}%)"
            + (". A distance this large is more usual between genera than within one; check the vouchers"
               " before reading it as a cryptic species" if med > 10 else ""),
            f"- {strength(asap.get(name))}",
            f"- Sites: {where(label, sa, sb, km)}"]
    stray = [f"{c} in {b}, " + (f"a BIN mostly *{owner(bin_names, b)}*" if owner(bin_names, b) else "a BIN shared by several names")
             for b, c in species[name].items()
             if owner(bin_names, b) != name]
    if stray:
        out.append(f"- Also: {'; '.join(stray)}")
    if note.get("source"):
        out.append(f"- Published: {note['source']}. {note['note']}")
    else:
        out.append(f"- Published: nothing found. {note.get('note', '')}".rstrip())
    out.append("")

if misids:
    out += ["## Possible misidentifications", "",
            "Records under these names sit in BINs that another name dominates. Worth checking the vouchers "
            "before reading them as lineages.", ""]
    for name in misids:
        stray = ", ".join(f"{c} in {b} (mostly *{owner(bin_names, b)}*)" for b, c in species[name].items()
                          if owner(bin_names, b) not in (name, None))
        line = f"- *{name}*: {stray}."
        if name in notes:
            line += f" {notes[name]['note']} ({notes[name]['source']})"
        out.append(line)
    out.append("")

if groups:
    out += ["## Names that share BINs", "",
            "BINs with no majority name, listed once per group. These point at the names, not at a lineage.", ""]
    for g in groups:
        mixed = sorted({b for n in g for b in species[n] if owner(bin_names, b) is None})
        out.append(f"- {', '.join(mixed)}: {', '.join(f'*{n}*' for n in sorted(g))}")
    out.append("")

path = ROOT / f"candidates-{cls.lower()}.md"
path.write_text("\n".join(out))
print(f"wrote {path.name}: {len(candidates)} candidates")

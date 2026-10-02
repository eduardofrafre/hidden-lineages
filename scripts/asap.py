"""Run ASAP on every file in data/asap and compare its partitions with the BINs.

Needs tools/asap (scripts/build_asap.sh). K2P distances, seed 1. Writes
data/asap/results.tsv and prints it. For each species:
- asap_groups, threshold, p: ASAP's best partition (lowest ASAP score), the distance
  where it cuts (? when outside ASAP's 0.5-5% barcode-gap window) and its p-value;
- vs_bins: how that best partition relates to the BINs: "agrees" (same groups),
  "merges" (whole BINs joined), "splits" (BINs cut further), "conflicts" (neither),
  "one group", or "no gap" (cut under 0.5%: ASAP is splitting noise);
- bin_rank, bin_p: where the partition identical to the BINs sits in ASAP's ranked
  list (1 is best, 0 if absent) and its p-value. ASAP's top pick can miss a real gap
  when one side holds one or two sequences; its authors leave the final cut to the
  user, so the rank of the BIN partition is kept alongside.
"""
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from bold import DATA

ROOT = Path(__file__).resolve().parent.parent
ASAP = ROOT / "tools" / "asap"
ROW = re.compile(r"^([ *])\s*([\d.]+)\s+(\d+)\s+\d+\s+([\d.e+-]+)\s+\S+\s+([\d.]+)")


def run(fasta):
    """ASAP's ranked partitions as dicts: threshold, groups, p, in_window, assign.

    ASAP prints its ranked table to stderr, best first. A star on a row only says its
    cut falls in the 0.5-5% window. The spart file holds the assignments, one column
    per partition in its own order; each partition has a distinct number of groups,
    which is how the two are matched.
    """
    with tempfile.TemporaryDirectory() as out:
        log = subprocess.run([ASAP, "-d", "0", "-x", "1", "-o", out + "/", fasta],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        spart = Path(out, fasta.name + ".spart").read_text()
    sizes = [int(x.split(":")[0]) for x in re.search(r"N_subsets = ([^;]*);", spart).group(1).split("/")]
    columns = defaultdict(dict)
    body = spart.split("Individual_assignment =", 1)[1].split(";", 1)[0]
    for line in body.strip().splitlines():
        name, groups = line.split(":")
        for k, g in zip(sizes, groups.split("/")):
            columns[k][name.strip()] = g.strip()
    ranked = []
    for line in log.splitlines():
        m = ROW.match(line)
        if m and int(m.group(3)) in columns:
            ranked.append({"threshold": float(m.group(2)), "groups": int(m.group(3)), "p": float(m.group(4)),
                           "in_window": m.group(1) == "*", "assign": columns[int(m.group(3))]})
    return ranked


def compare(part):
    """How one ASAP partition relates to the BINs (read back from the sequence names)."""
    if part["threshold"] < 0.005:
        return "no gap"
    bins, groups = defaultdict(set), defaultdict(set)
    for name, g in part["assign"].items():
        b = "BOLD:" + name.rsplit("_BOLD_", 1)[1]
        bins[b].add(g)
        groups[g].add(b)
    if len(groups) == 1:
        return "one group"
    whole_bins = all(len(gs) == 1 for gs in bins.values())
    whole_groups = all(len(bs) == 1 for bs in groups.values())
    if whole_bins and whole_groups:
        return "agrees"
    return "merges" if whole_bins else "splits" if whole_groups else "conflicts"


if __name__ == "__main__":
    if not ASAP.exists():
        sys.exit("tools/asap missing: run scripts/build_asap.sh")
    rows = []
    for fasta in sorted((DATA / "asap").glob("*.fas")):
        ranked = run(fasta)
        best = ranked[0]
        bins = len({n.rsplit("_BOLD_", 1)[1] for n in best["assign"]})
        match = next(((i + 1, p) for i, p in enumerate(ranked) if compare(p) == "agrees"), (0, None))
        rows.append((fasta.stem.replace("_", " "), len(best["assign"]), bins, best["groups"], best["threshold"],
                     best["p"], best["in_window"], compare(best), match[0], match[1]["p"] if match[1] else ""))
    with open(DATA / "asap" / "results.tsv", "w") as f:
        f.write("species\tn\tbins\tasap_groups\tthreshold\tp\tin_window\tvs_bins\tbin_rank\tbin_p\n")
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")
    print(f"{'species':32}{'n':>4}{'bins':>5}{'asap':>5}{'cut':>8}{'p':>10}  {'vs BINs':10} BIN partition")
    for name, n, bins, k, t, p, window, rel, rank, bp in rows:
        where = f"rank {rank}, p={bp:.0e}" if rank else "not listed"
        print(f"{name:32}{n:4}{bins:5}{k:5}{t * 100:7.2f}%{'' if window else '?'}{p:10.1e}  {rel:10} {where}")

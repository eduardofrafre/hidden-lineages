# Rediscovery test

Written 2026-10-01, before running the test against the benchmark.

**Benchmark** (`benchmark.tsv`): 20 fish species published as holding deep COI
divergence or cryptic lineages, taken from three papers that predate this tool:
Pereira et al. 2013 (Upper Paraná, Table 3), Rosso et al. 2012 (Pampa) and
Ribolli et al. 2021 (*Rhamdia*). The first read of `splits.py` had already shown
*Rhamdia quelen*, *Synbranchus marmoratus*, *Piabina argentea* and *Salminus
brasiliensis* as splits, so these are not blind. The other 16 are.

**Testable**: the species has 5 or more georeferenced COI barcodes in PR, SC or RS.
Species below that are reported, not scored.

**Flagged**: the species' southern barcodes fall in 2 or more BINs.

**Pass**, all three:
1. Recall on testable species with published divergence of 2.5% or more: at least 2 in 3.
2. Recall on all testable species: at least 1 in 2. Shallow cases (under 2.2%) are
   expected misses, because a BIN merges sequences closer than about 2.2%. Rosso's
   divergences are between Argentina and the rest of the range, so they may not show
   inside southern Brazil.
3. Of the 10 strongest non-benchmark flags, a reader can explain at least 7 as a
   plausible cryptic complex or a naming problem, with a source for each.

**Known circularity**: Pereira's sequences are in BOLD and some come from northern
Paraná, so part of this checks that the pipeline sees what is in the data rather
than independent discovery. Criterion 3 is the part that is not circular.

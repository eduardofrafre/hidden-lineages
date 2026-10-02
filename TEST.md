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

## Result, 2026-10-01: pass, with a small sample

Output of `scripts/rediscovery.py` against the criteria above.

1. Deep recall **3/3** (*Piabina argentea*, *Synbranchus marmoratus*, *Rhamdia quelen*).
   All three were in the non-blind set.
2. Overall recall **6/7**. Blind cases: *Phalloceros harpagos* and *Corydoras paleatus*
   flagged, *Bryconamericus iheringii* missed (published at 1.8%, under the BIN
   threshold, as expected). 13 of the 20 benchmark species have fewer than 5 southern
   barcodes and were not scored, so the test rests on 7 species.
3. **8 of 10** strongest non-benchmark flags explained:
   - *Pimelodus maculatus*: several MOTUs across basins (Biology 2024, 13:162, doi:10.3390/biology13030162).
   - *Apareiodon affinis*: two genetic groups and an undescribed species (PMC6726146). Its two BINs sit at 27.4 S and 22.8 S.
   - *Astyanax laticeps*, *Psalidodon bifasciatus*, *P. bockmanni*, *P. gymnodontus*,
     *Astyanax dissimilis*: naming problem. BOLD:AAC5910 holds ten
     *Astyanax*/*Psalidodon* names; the BIN is named as a sharing case in Rossini et
     al. 2016 (PLOS ONE, doi:10.1371/journal.pone.0167203), and southern
     *P. scabripinnis* complex barcodes support splitting *P. laticeps* (Neotropical
     Ichthyology, integrative diagnosis of the *P. scabripinnis* complex).
   - *Phalloceros titthos*: its smaller BIN is the main *P. harpagos* BIN, a naming
     problem visible in the data itself. Counted, with no paper behind it.
   - Not explained: *Diapoma itaimbe* (41 + 1) and *Astyanax ribeirae* (13 + 1). The
     second BIN is a single sequence each.

What the test teaches about ranking, more than the pass:
- Five of the top ten are one problem, BOLD:AAC5910, counted five times. Splits that
  share a BIN with other names must collapse into one entry per BIN group.
- A second BIN of one sequence is not a lineage. Rank those last.

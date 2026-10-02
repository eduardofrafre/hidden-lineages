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

## Ranking applied after the test, 2026-10-02

`scripts/splits.py` now applies the two lessons above, refined after a first try.
Collapsing every split that shares a BIN with another name, as first written, also
removed *Rhamdia quelen*, *Phalloceros harpagos* and *Corydoras paleatus*. Their shared
BINs are not mixed: each is clearly owned by another name. So a BIN now belongs to the
name holding most of its records, and a split counts only the BINs the species owns.
Records in a BIN another name owns are listed as probable misidentifications. BINs with
no majority name form the naming-problem groups.

This refinement was designed after seeing which benchmark hits the first version
dropped, so the fish benchmark cannot test it. The insect benchmark, written before
its run, is the first fair check.

Fish result: 8 candidates, 1 naming-problem group (BOLD:AAC5910 and BOLD:ACJ1542, four
split names), 2 probable misidentifications, 4 single-sequence splits.
- *Rhamdia quelen* is no longer a lineage candidate. Its 5 and 4 extra records sit in
  BINs that hold mostly *R. voulezi* (14) and *R. branneri* (13). Same for
  *C. paleatus*: 2 records in a BIN that is mostly *C. ehrhardti*.
- Correction to criterion 3 above: *Phalloceros titthos*'s second BIN (BOLD:AGE7052,
  n=3) holds only *P. titthos*. It is the reverse case that holds a stray name:
  titthos's main BIN, BOLD:AAB5570, holds one *P. harpagos* record. Titthos is now a
  clean candidate, and the "explained" count for criterion 3 has no source for it.

# Insect rediscovery test

Written 2026-10-02, before running the test against the benchmark.

**Benchmark** (`benchmark-insects.tsv`): 27 species from 12 papers, collected from
the literature without looking at our data. Unlike the fish test it has controls.
Each row has a `kind`:
- `deep`, 9: published COI divergence of 2.5% or more between lineages.
- `shallow`, 7: a published split under 2.5%, or one with no figure.
- `threshold`, 3: 2 or more BINs, but a single MOTU at 2% and in ABGD. Reported, not scored.
- `control`, 8: published as a single COI lineage in the region.

Not blind: *Simulium hirtipupa* and *Hermeuptychia hermes* (both genera were seen
splitting in the first read), and *Melese chozeba* (seen in the ASAP input summary).
None of the other insect splits was looked at.

**Known circularity**: the Zenker et al. 2016 rows come from the LEMMZ Serra do Mar
project in Paraná, which holds most Brazilian Arctiinae barcodes. For those rows
this is a consistency check on the same records. The Lavinia et al. 2017 rows
(Misiones, Argentina) and the controls are independent of our records.

**Interim names**, decided before the run: BOLD holds the Zenker lineages under names
like `Cosmosoma auge sp. MMZ01`. `bold.py` will read `Genus species sp. TAG` as
`Genus species`, everywhere and not only in this test, because the tag marks a
provisional lineage of that species. `Genus sp. TAG` stays out. The fish result is
re-run after the change, and any difference is recorded.

**Testable**: 5 or more southern COI barcodes across the row's `bold_names`. Same as fish.

**Flagged**: those barcodes fall in 2 or more BINs. Same as fish.

**Pass**, all four:
1. Deep recall: at least 2 in 3 testable `deep` species flagged.
2. Overall recall: at least 1 in 2 testable `deep` and `shallow` species flagged.
3. Controls: at most 1 in 3 testable controls flagged. With fewer than 3 testable
   controls, reported and not scored.
4. Ranking, the first fair check of the BIN-ownership rule: at least half of the
   flagged testable positives land in Candidates in `splits.py`, not in naming
   problems, misidentifications or single-sequence splits.

Also reported, as for fish: of the 10 strongest non-benchmark insect candidates,
how many a reader can explain as a plausible cryptic complex or a naming problem,
with a source.

## Result, 2026-10-02: pass on three criteria, controls not scored, thin sample

Output of `scripts/rediscovery_insects.py` against the criteria above.

1. Deep recall **2/2** (*Pintomyia monticola*, *Mycodrosophila projectans*). Both blind.
   Seven of the nine deep species have no southern barcodes at all: the Misiones
   butterflies, *P. misionensis*, and the two non-blind cases, so those added nothing.
2. Overall recall **4/6**. Flagged: the two deep cases, *Melese castrena*, *Eucereon rosa*.
   Missed: *Lonomia parobliqua* (25 records, all in one BIN; the published second BIN
   has no southern record) and *Spodoptera frugiperda* (7 records, one BIN; the strains
   differ by 2.13%, under the BIN threshold, an expected miss).
3. Controls: **not scored**. No control has 5 southern barcodes; the best has 3.
   The tool's false-positive rate is still unmeasured.
4. Ranking: **3 of 4** flagged positives land in Candidates. *Eucereon rosa* (6
   records) went to single-sequence splits. *Melese chozeba*, a threshold case that is
   one MOTU in print, also went there, which is the right place for it.

So the BIN-ownership ranking held on its first out-of-sample check, but on four
species. The pass says the pipeline is not broken on insects; it does not say much
more. More testable controls would need either a wider region or controls picked
from well-barcoded southern genera.

Strongest non-benchmark candidates, not yet explained: *Simulium itaunense*,
*Eacles ducalis*, *Simulium subnigrum*, *Virbia divisa*, *Correbidia elegans*,
*Scolesa viettei*, *Hermeuptychia atalanta*, *Periga circumstans*, *Simulium
spinibranchium*, *Paracles fusca*. *Paracles fusca* is one of the Zenker et al. 2016
splits left out of the benchmark, so it has a source already. The rest need the
same reading the fish list got.

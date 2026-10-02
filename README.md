# Hidden Lineages

Candidate cryptic species in the southern Atlantic Forest (Paraná, Santa Catarina,
Rio Grande do Sul), flagged from public DNA barcodes in BOLD. The output is a list of
candidates for a taxonomist to look at, never a claim that a species is new.

Exploration stage: scripts only.

```sh
cd scripts
python3 coverage.py          # per class: species with 5+ georeferenced COI barcodes
python3 splits.py Teleostei  # species whose barcodes fall in more than one BIN
```

The first run downloads every public BOLD record from Brazil (about 190 MB, under a
minute) to `data/brazil.tsv`. Delete it to refresh.

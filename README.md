# Hidden Lineages

Candidate cryptic species in the southern Atlantic Forest (Paraná, Santa Catarina,
Rio Grande do Sul), flagged from public DNA barcodes in BOLD. The output is a list of
candidates for a taxonomist to look at, never a claim that a species is new.

Exploration stage. The candidates are also published as a page at
[hidden-lineages.lab.eduardofrafre.com](https://hidden-lineages.lab.eduardofrafre.com).

```sh
cd scripts
python3 coverage.py          # per class: species with 5+ georeferenced COI barcodes
python3 splits.py Teleostei  # split species: candidates, naming problems, misidentifications
```

ASAP (Puillandre et al. 2021) is the second opinion on each split. Build it once, then
align the split species and run it; `splits.py` picks the results up and ranks the
candidates ASAP backs first.

```sh
scripts/build_asap.sh        # clones the MNHN C source via iTaxoTools/ASAPy, builds tools/asap
cd scripts
python3 asap_input.py        # one aligned FASTA per split species, in data/asap
python3 asap.py              # ASAP on each; where the BIN partition ranks and its p-value
python3 sheet.py Teleostei   # the candidate sheet, in English and pt-BR
python3 site.py              # the showcase page in site/, deployed with npx wrangler deploy
```

ASAP's top-ranked partition is not always the real one: with one or two sequences on
one side of a gap it can prefer a partition that only splits noise. `asap.py` therefore
also reports where the partition matching the BINs sits in ASAP's list, and its p-value.

Each candidate in `splits.py` also shows where its two largest BINs were collected
(`scripts/geography.py`): together at a shared site, apart, or too few sites to say.
It is shown as evidence, not used to rank: lineages apart can be one structured
species, and lineages together can be two species or a contaminated sample.

The first run downloads every public BOLD record from Brazil (about 190 MB, under a
minute) to `data/brazil.tsv`. Delete it to refresh.

## Support

The work is free and the results will be public. If you want to help pay for it, you can
[donate by PayPal](https://www.paypal.com/donate/?hosted_button_id=N2T3FKPS2Z7DQ)
or, from Brazil, [by Pix](https://eduardofrafre.com/pt-br/?pay=pix#support).

## Licence

The code is MIT, see [LICENSE](LICENSE). The candidate lists are derived from public
BOLD records, and each record keeps the terms its submitter set in BOLD; check those
before reusing the data. The iA Writer fonts in `site/assets/fonts` are under the SIL
Open Font License, see the `LICENSE.md` next to them.

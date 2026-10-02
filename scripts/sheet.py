"""Write the candidate sheet for one class, in English and Brazilian Portuguese.

candidates-<class>.md and candidates-<class>.pt-BR.md at the repository root. Every
number comes from the pipeline: BINs and sites from the BOLD download, distances from
align.py, ASAP support from data/asap/results.tsv. The published source next to a
candidate comes from candidate-notes.tsv, kept by hand, with a note in each language.
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

TEXT = {
    "en": {
        "title": "# Candidate cryptic species: {cls}, southern Atlantic Forest",
        "generated": "Generated {today} from public BOLD records for Paraná, Santa Catarina and Rio Grande do Sul "
                     "(downloaded {downloaded}).",
        "intro": "Each entry is a **candidate**: a named species whose southern COI barcodes fall in two or more "
                 "BINs the species itself dominates. It is a lead for a specialist, not a claim that a species is "
                 "new. COI alone cannot tell a cryptic species from introgression, incomplete lineage sorting, a "
                 "pseudogene or a misidentified voucher; nuclear markers and morphology can.",
        "fields": "For each: the BINs with record counts, the COI distance between the two largest BINs the "
                  "species dominates (uncorrected p-distance), whether ASAP (Puillandre et al. 2021) finds a "
                  "barcode gap at the BIN boundary, where the BINs were collected, and what is already published.",
        "heading": "## {i}. *{name}* ({order}, {n} barcodes)",
        "bins": "- BINs: {bins}",
        "distance": "- Distance between the two largest: {med}% (range {lo} to {hi}%)",
        "deep": ". A distance this large is more usual between genera, though cryptic species this deep are "
                "published in some groups",
        "no_asap": "ASAP does not separate these BINs",
        "asap": "ASAP {word} the BIN split (p = {p:.0e}, {rank})",
        "supports": "supports", "weakly": "weakly supports",
        "first": "its first choice", "ranked": "ranked {r} among its partitions",
        "sites": "- Sites: {where}",
        "together": "collected together at a shared site (first BIN at {sa} sites, second at {sb})",
        "one shared site": "both BINs come from a single site",
        "apart": "collected apart: {sa} and {sb} sites, closest {km:.0f} km",
        "too few sites": "second BIN known from {sb} site(s), {km:.0f} km from the nearest site of the first",
        "also": "- Also: {stray}",
        "stray_owned": "{c} in {b}, a BIN mostly *{o}*", "stray_mixed": "{c} in {b}, a BIN shared by several names",
        "published": "- Published: {source}. {note}", "unpublished": "- Published: nothing found. {note}",
        "misid_title": "## Possible misidentifications",
        "misid_intro": "Records under these names sit in BINs that another name dominates, or split at a distance "
                       "usual between genera with another genus in the same BIN. Worth checking the vouchers before "
                       "reading them as lineages.",
        "demoted": "- *{name}*: its own BINs {b1} and {b2} are {med}% apart, and {b2} also holds {others}.",
        "misid": "- *{name}*: {stray}.", "misid_part": "{c} in {b} (mostly *{o}*)",
        "groups_title": "## Names that share BINs",
        "groups_intro": "BINs with no majority name, listed once per group. These point at the names, not at a "
                        "lineage.",
        "suffix": "",
    },
    "pt": {
        "title": "# Espécies crípticas candidatas: {cls}, Mata Atlântica do Sul",
        "generated": "Gerado em {today} a partir dos registros públicos do BOLD para Paraná, Santa Catarina e Rio "
                     "Grande do Sul (baixados em {downloaded}).",
        "intro": "Cada item é uma **candidata**: uma espécie nomeada cujos códigos de barras COI do Sul caem em dois "
                 "ou mais BINs dominados pela própria espécie. É uma pista para um especialista, não a afirmação de "
                 "que existe uma espécie nova. O COI sozinho não distingue uma espécie críptica de introgressão, "
                 "separação incompleta de linhagens, pseudogene ou voucher mal identificado; marcadores nucleares e "
                 "morfologia distinguem.",
        "fields": "Para cada uma: os BINs com o número de registros, a distância de COI entre os dois maiores BINs "
                  "dominados pela espécie (distância p sem correção), se o ASAP (Puillandre et al. 2021) encontra "
                  "uma lacuna de código de barras na fronteira entre os BINs, onde os BINs foram coletados e o que "
                  "já foi publicado.",
        "heading": "## {i}. *{name}* ({order}, {n} códigos de barras)",
        "bins": "- BINs: {bins}",
        "distance": "- Distância entre os dois maiores: {med}% (de {lo} a {hi}%)",
        "deep": ". Uma distância desse tamanho é mais comum entre gêneros, embora espécies crípticas tão "
                "divergentes estejam publicadas em alguns grupos",
        "no_asap": "O ASAP não separa estes BINs",
        "asap": "O ASAP {word} a divisão em BINs (p = {p:.0e}, {rank})",
        "supports": "apoia", "weakly": "apoia com pouca força",
        "first": "sua primeira escolha", "ranked": "na posição {r} entre as partições",
        "sites": "- Pontos de coleta: {where}",
        "together": "coletados juntos num ponto em comum (primeiro BIN em {sa} pontos, segundo em {sb})",
        "one shared site": "os dois BINs vêm de um único ponto",
        "apart": "coletados separados: {sa} e {sb} pontos, os mais próximos a {km:.0f} km",
        "too few sites": "segundo BIN conhecido de {sb} ponto(s), a {km:.0f} km do ponto mais próximo do primeiro",
        "also": "- Além disso: {stray}",
        "stray_owned": "{c} em {b}, um BIN quase todo de *{o}*",
        "stray_mixed": "{c} em {b}, um BIN dividido entre vários nomes",
        "published": "- Publicado: {source}. {note}", "unpublished": "- Publicado: nada encontrado. {note}",
        "misid_title": "## Possíveis erros de identificação",
        "misid_intro": "Registros com estes nomes estão em BINs dominados por outro nome, ou se dividem a uma "
                       "distância comum entre gêneros com outro gênero no mesmo BIN. Vale conferir os vouchers antes "
                       "de lê-los como linhagens.",
        "demoted": "- *{name}*: seus BINs {b1} e {b2} estão a {med}% de distância, e {b2} também tem {others}.",
        "misid": "- *{name}*: {stray}.", "misid_part": "{c} em {b} (quase todo de *{o}*)",
        "groups_title": "## Nomes que dividem BINs",
        "groups_intro": "BINs sem nome majoritário, listados uma vez por grupo. Apontam para os nomes, não para uma "
                        "linhagem.",
        "suffix": ".pt-BR",
    },
}


def gap(seqs, name, b1, b2):
    """Median and range of p-distance between the two BINs, in percent."""
    recs = {pid: nuc for pid, (sp, b, nuc) in seqs.items() if sp == name and b in (b1, b2)}
    aligned, _ = align(recs)
    d = [p_distance(aligned[x], aligned[y]) for x, y in product(aligned, aligned)
         if seqs[x][1] == b1 and seqs[y][1] == b2]
    d = [v * 100 for v in d if v is not None]
    return median(d), min(d), max(d)


def write(lang, cls, species, bin_names, coords, order, asap, kept, demoted, misids, groups, notes):
    t = TEXT[lang]
    pct = lambda x: f"{x:.1f}" if lang == "en" else f"{x:.1f}".replace(".", ",")
    note_of = lambda name: notes.get(name, {}).get("note" if lang == "en" else "note_pt", "")
    downloaded = date.fromtimestamp((DATA / "brazil.tsv").stat().st_mtime).isoformat()
    out = [t["title"].format(cls=cls), "", t["generated"].format(today=date.today().isoformat(), downloaded=downloaded),
           "", t["intro"], "", t["fields"], ""]

    for i, (name, b1, b2, med, lo, hi, _) in enumerate(kept, 1):
        label, sa, sb, km = pattern(coords[name, b1], coords[name, b2])
        row = asap.get(name)
        if not row or not int(row["bin_rank"]):
            support = t["no_asap"]
        else:
            p = float(row["bin_p"])
            rank = t["first"] if row["bin_rank"] == "1" else t["ranked"].format(r=row["bin_rank"])
            support = t["asap"].format(word=t["supports"] if p < 0.05 else t["weakly"], p=p, rank=rank)
        out += [t["heading"].format(i=i, name=name, order=order[name], n=sum(species[name].values())), "",
                t["bins"].format(bins=", ".join(f"{b} ({c})" for b, c in species[name].most_common())),
                t["distance"].format(med=pct(med), lo=pct(lo), hi=pct(hi)) + (t["deep"] if med > 10 else ""),
                f"- {support}",
                t["sites"].format(where=t[label].format(sa=sa, sb=sb, km=km))]
        stray = [t["stray_owned"].format(c=c, b=b, o=owner(bin_names, b)) if owner(bin_names, b)
                 else t["stray_mixed"].format(c=c, b=b)
                 for b, c in species[name].items() if owner(bin_names, b) != name]
        if stray:
            out.append(t["also"].format(stray="; ".join(stray)))
        source = notes.get(name, {}).get("source")
        out.append((t["published"].format(source=source, note=note_of(name)) if source
                    else t["unpublished"].format(note=note_of(name))).rstrip())
        out.append("")

    if misids or demoted:
        out += [t["misid_title"], "", t["misid_intro"], ""]
        for name, b1, b2, med, _, _, others in demoted:
            line = t["demoted"].format(name=name, b1=b1, b2=b2, med=pct(med), others=", ".join(f"*{n}*" for n in others))
            if name in notes:
                line += f" {note_of(name)} ({notes[name]['source']})"
            out.append(line)
        for name in misids:
            parts = ", ".join(t["misid_part"].format(c=c, b=b, o=owner(bin_names, b))
                              for b, c in species[name].items() if owner(bin_names, b) not in (name, None))
            line = t["misid"].format(name=name, stray=parts)
            if name in notes:
                line += f" {note_of(name)} ({notes[name]['source']})"
            out.append(line)
        out.append("")

    if groups:
        out += [t["groups_title"], "", t["groups_intro"], ""]
        for g in groups:
            mixed = sorted({b for n in g for b in species[n] if owner(bin_names, b) is None})
            out.append(f"- {', '.join(mixed)}: {', '.join(f'*{n}*' for n in sorted(g))}")
        out.append("")

    path = ROOT / f"candidates-{cls.lower()}{t['suffix']}.md"
    path.write_text("\n".join(out))
    return path


if __name__ == "__main__":
    cls = sys.argv[1] if len(sys.argv) > 1 else "Teleostei"
    species, bin_names, coords, order = load(cls)
    asap = asap_results()
    candidates, groups, misids, _ = classify(species, bin_names, asap)
    notes = {r["species"]: r for r in csv.DictReader(open(ROOT / "candidate-notes.tsv"), delimiter="\t")}
    seqs = {row["processid"]: (row["species"], row["bin_uri"], row["nuc"])
            for row in barcodes(download("geo:country/ocean:Brazil", "brazil")) if row["class"] == cls}

    # A genus-level distance alone is not enough to doubt a candidate: cryptic drosophilids
    # are published at 12%. With a record of another genus in the second BIN as well, the
    # split more likely comes from misidentified vouchers, and the candidate moves down.
    kept, demoted = [], []
    for name in candidates:
        b1, b2 = [b for b, _ in species[name].most_common() if owner(bin_names, b) == name][:2]
        med, lo, hi = gap(seqs, name, b1, b2)
        others = sorted(n for n in bin_names[b2] if n.split()[0] != name.split()[0])
        (demoted if med > 10 and others else kept).append((name, b1, b2, med, lo, hi, others))

    for lang in TEXT:
        path = write(lang, cls, species, bin_names, coords, order, asap, kept, demoted, misids, groups, notes)
        print(f"wrote {path.name}: {len(kept)} candidates, {len(demoted)} moved to misidentifications")

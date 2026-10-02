"""Build the showcase page: site/index.html (English) and site/pt-br/index.html.

A static page for hidden-lineages.lab.eduardofrafre.com, generated from the same data
as the candidate sheet (sheet.build), so the page cannot drift from the analysis. It
is written for two readers: someone with no biology, who gets what a barcode is and
what each fish is, and a specialist, who gets the BINs, distances, ASAP support and
sources on each specimen label. Design follows the lab site (Rei tokens, iA Writer).

    python3 site.py && npx wrangler deploy     # from the repository root for the deploy
"""
import json
import shutil
from datetime import date
from html import escape
from pathlib import Path

from bold import DATA, barcodes, south_records
from geography import pattern, site
from sheet import build
from splits import load, owner

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
LAB = ROOT.parent / "lab" / "site" / "assets" / "fonts"
STATES = {"41": "PR", "42": "SC", "43": "RS"}

# Map frame: the three southern states, equirectangular with longitude shrunk by cos(28 S).
LON0, LON1, LAT0, LAT1 = -57.8, -47.9, -33.9, -22.4
KX = 0.883
MAP_W = 220


def projector(width):
    scale = width / ((LON1 - LON0) * KX)
    height = (LAT1 - LAT0) * scale
    return (lambda lat, lon: ((lon - LON0) * KX * scale, (LAT1 - lat) * scale)), width, height


def outlines(width):
    """SVG paths of PR, SC and RS from IBGE's simplified mesh (data/geo, fetched once)."""
    xy, _, _ = projector(width)
    paths = []
    for code in STATES:
        g = json.load(open(DATA / "geo" / f"{code}.json"))["features"][0]["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        d = ""
        for poly in polys:
            for ring in poly:
                pts = [xy(lat, lon) for lon, lat in ring]
                d += "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
        paths.append(f'<path d="{d}"/>')
    return "".join(paths)


TEXT = {
    "en": {
        "lang": "en", "root": "", "other": "pt-br/", "other_label": "PT", "here_label": "EN",
        "other_title": "Versão em português",
        "title": "Hidden Lineages · Lab · Eduardo Freitas",
        "description": "Fish of southern Brazil whose public DNA barcodes suggest more than one species under a "
                       "single name: seven candidates, with the evidence behind each.",
        "kicker": "Lab notebook · ECO-02 · Southern Atlantic Forest",
        "h1": "Some fish may be <em>two species</em> under one name.",
        "lede": "A DNA barcode is a short stretch of one gene that works like a species fingerprint. When animals "
                "carrying the same name turn out to have two clearly different fingerprints, the name may be "
                "hiding a species nobody has described. This project reads every public barcode from Paraná, "
                "Santa Catarina and Rio Grande do Sul and lists the names most likely to be hiding one.",
        "facts": [("records from the three states", "south"), ("usable DNA barcodes", "usable"),
                  ("names split across groups", "split"), ("fish candidates", "cands")],
        "status": "exploration",
        "plate1": "<b>Plate 1.</b> Every site in PR, SC and RS where a usable barcode was collected. "
                  "Sites of the seven candidates are marked in blue.",
        "how_k": "How it works",
        "how_h": "From public records to a short list",
        "how": [("Barcodes", "BOLD Systems", "Public DNA barcodes, each with a name, a place and a sequence."),
                ("Groups", "BINs", "BOLD clusters near-identical barcodes into groups that roughly match species."),
                ("Splits", "one name, two groups", "Names whose barcodes fall into two or more groups the name "
                 "itself dominates. Mislabelled records are set aside."),
                ("Second opinion", "ASAP", "An independent method checks whether there is a real gap between "
                 "the groups, or only noise."),
                ("Candidates", "for a specialist", "What survives, with the evidence next to it.")],
        "fig2": "<b>Fig. 2.</b> Each step removes a kind of false alarm.",
        "cands_k": "The candidates",
        "cands_h": "Seven fish worth a second look",
        "cands_p": "Ordered by how strongly the second method backs the split. None of these is a new species "
                   "yet: each is a question for someone who can examine the fish.",
        "groups_n": {2: "two", 3: "three", 4: "four"},
        "split": "Its barcodes fall into {k} groups that differ by {med}%.",
        "tier_deep": "That is larger than the difference between many pairs of fish already recognised as "
                     "separate species.",
        "tier_edge": "That sits at the edge where biologists start to suspect two species.",
        "tier_shallow": "That is small: it may be ordinary variation inside one species, so the case is weaker.",
        "lbl_catno": "Cat. no.", "lbl_barcodes": "Barcodes", "lbl_groups": "Groups (BINs)",
        "lbl_distance": "Distance", "lbl_asap": "Second opinion", "lbl_sites": "Sites",
        "asap_strong": "strong (p = {p})", "asap_weak": "weak (p = {p})", "asap_none": "no gap found",
        "sites": {"together": "share a site", "one shared site": "one shared site", "apart": "apart",
                  "too few sites": "too few to tell"},
        "for_specialists": "For specialists",
        "bins": "BINs: {bins}.",
        "asap_line_strong": "ASAP finds a gap at the BIN boundary (p = {p}{rank}).",
        "asap_line_weak": "ASAP's gap at the BIN boundary is weak (p = {p}{rank}).",
        "asap_line_none": "ASAP does not separate these BINs.",
        "rank": ", ranked {r} among its partitions",
        "where": {"together": "The two largest groups were collected at a shared site ({sa} and {sb} sites).",
                  "one shared site": "Both groups come from a single site.",
                  "apart": "The two largest groups were collected apart ({sa} and {sb} sites, closest {km} km).",
                  "too few sites": "The second group is known from {sb} site, {km} km from the first."},
        "published": "Published: {source}. {note}", "unpublished": "Nothing published found. {note}",
        "map_alt": "Map of Paraná, Santa Catarina and Rio Grande do Sul with the collecting sites of the two "
                   "barcode groups of {name}.",
        "legend_a": "largest group", "legend_b": "second group",
        "limits_k": "Read this first",
        "limits_h": "What this is not",
        "limits": ["<b>These are candidates, not new species.</b> One gene can be misleading: hybridisation, "
                   "old shared ancestry or a mislabelled specimen can all produce two groups. Naming a species "
                   "takes more genes and a close look at the animals.",
                   "<b>The data are thin.</b> Only fish and insects have enough barcodes in the south, and most "
                   "species have fewer than five. Frogs, where the idea started, have none that qualify.",
                   "<b>It finds what is already known.</b> Tested against published cases written down before "
                   "the run, it found them. How often it raises a false alarm is not yet measured.",
                   "<b>Insects are not reviewed yet.</b> {ins} insect names pass the same checks and wait for "
                   "the same reading the fish got."],
        "misid_h": "Set aside",
        "misid_p": "Names whose extra barcodes sit in another species' group, or split by a distance usual "
                   "between genera with another genus in the same group. These look more like labelling "
                   "problems than hidden species, and are listed for whoever holds the specimens.",
        "wanted_b": "Wanted", "wanted_s": "taxonomists who know southern fish",
        "wanted_p": "<b>Which of these are worth a look?</b> If you work on any of these groups, a one-line "
                    "answer helps decide what to examine next. A candidate that holds up could become a "
                    "co-authored description.",
        "wanted_mail": "Write about Hidden Lineages",
        "data": "Data: public records from <a class=\"ln\" href=\"https://boldsystems.org\" target=\"_blank\" "
                "rel=\"noopener\">BOLD Systems</a>, downloaded {downloaded}. Species delimitation with ASAP "
                "(Puillandre et al. 2021). State outlines from IBGE. Generated {today}.",
        "back": "Back to the lab", "back_h": "More questions about living things, worked out in software.",
        "colophon": "Set in iA Writer Quattro and Mono, in the colours of Rei.",
    },
    "pt": {
        "lang": "pt-BR", "root": "../", "other": "../", "other_label": "EN", "here_label": "PT",
        "other_title": "English version",
        "title": "Linhagens Ocultas · Lab · Eduardo Freitas",
        "description": "Peixes do Sul do Brasil cujos códigos de barras de DNA públicos sugerem mais de uma espécie "
                       "sob um único nome: sete candidatas, com as evidências de cada uma.",
        "kicker": "Caderno do lab · ECO-02 · Mata Atlântica do Sul",
        "h1": "Alguns peixes podem ser <em>duas espécies</em> com um só nome.",
        "lede": "Um código de barras de DNA é um trecho curto de um gene que funciona como a impressão digital de "
                "uma espécie. Quando animais com o mesmo nome mostram duas impressões claramente diferentes, o "
                "nome pode estar escondendo uma espécie que ninguém descreveu. Este projeto lê todos os códigos "
                "de barras públicos do Paraná, de Santa Catarina e do Rio Grande do Sul e lista os nomes com mais "
                "chance de esconder uma.",
        "facts": [("registros dos três estados", "south"), ("códigos de barras utilizáveis", "usable"),
                  ("nomes divididos em grupos", "split"), ("peixes candidatos", "cands")],
        "status": "exploração",
        "plate1": "<b>Prancha 1.</b> Todos os pontos no PR, em SC e no RS onde foi coletado um código de barras "
                  "utilizável. Os pontos das sete candidatas estão em azul.",
        "how_k": "Como funciona",
        "how_h": "Dos registros públicos a uma lista curta",
        "how": [("Códigos de barras", "BOLD Systems", "Códigos de barras de DNA públicos, cada um com nome, "
                 "lugar e sequência."),
                ("Grupos", "BINs", "O BOLD agrupa códigos quase idênticos em grupos que correspondem mais ou "
                 "menos a espécies."),
                ("Divisões", "um nome, dois grupos", "Nomes cujos códigos caem em dois ou mais grupos dominados "
                 "pelo próprio nome. Registros mal rotulados ficam de fora."),
                ("Segunda opinião", "ASAP", "Um método independente verifica se há uma lacuna real entre os "
                 "grupos ou só ruído."),
                ("Candidatas", "para um especialista", "O que sobra, com a evidência ao lado.")],
        "fig2": "<b>Fig. 2.</b> Cada etapa tira um tipo de alarme falso.",
        "cands_k": "As candidatas",
        "cands_h": "Sete peixes que merecem um segundo olhar",
        "cands_p": "Em ordem de quanto o segundo método apoia a divisão. Nenhuma delas é espécie nova ainda: cada "
                   "uma é uma pergunta para quem pode examinar os peixes.",
        "groups_n": {2: "dois", 3: "três", 4: "quatro"},
        "split": "Os códigos de barras caem em {k} grupos que diferem {med}%.",
        "tier_deep": "É mais do que a diferença entre muitos pares de peixes já reconhecidos como espécies "
                     "separadas.",
        "tier_edge": "Fica no limite em que biólogos começam a suspeitar de duas espécies.",
        "tier_shallow": "É pouco: pode ser variação comum dentro de uma espécie, então o caso é mais fraco.",
        "lbl_catno": "N.º", "lbl_barcodes": "Códigos", "lbl_groups": "Grupos (BINs)",
        "lbl_distance": "Distância", "lbl_asap": "Segunda opinião", "lbl_sites": "Pontos",
        "asap_strong": "forte (p = {p})", "asap_weak": "fraca (p = {p})", "asap_none": "sem lacuna",
        "sites": {"together": "dividem um ponto", "one shared site": "um só ponto", "apart": "separados",
                  "too few sites": "poucos para dizer"},
        "for_specialists": "Para especialistas",
        "bins": "BINs: {bins}.",
        "asap_line_strong": "O ASAP encontra uma lacuna na fronteira entre os BINs (p = {p}{rank}).",
        "asap_line_weak": "A lacuna do ASAP na fronteira entre os BINs é fraca (p = {p}{rank}).",
        "asap_line_none": "O ASAP não separa estes BINs.",
        "rank": ", na posição {r} entre as partições",
        "where": {"together": "Os dois maiores grupos foram coletados num ponto em comum ({sa} e {sb} pontos).",
                  "one shared site": "Os dois grupos vêm de um único ponto.",
                  "apart": "Os dois maiores grupos foram coletados separados ({sa} e {sb} pontos, os mais "
                           "próximos a {km} km).",
                  "too few sites": "O segundo grupo é conhecido de {sb} ponto, a {km} km do primeiro."},
        "published": "Publicado: {source}. {note}", "unpublished": "Nada publicado encontrado. {note}",
        "map_alt": "Mapa do Paraná, de Santa Catarina e do Rio Grande do Sul com os pontos de coleta dos dois "
                   "grupos de códigos de barras de {name}.",
        "legend_a": "maior grupo", "legend_b": "segundo grupo",
        "limits_k": "Leia antes",
        "limits_h": "O que isto não é",
        "limits": ["<b>São candidatas, não espécies novas.</b> Um gene só pode enganar: hibridação, ancestralidade "
                   "antiga em comum ou um exemplar mal rotulado podem produzir dois grupos. Nomear uma espécie "
                   "exige mais genes e um olhar atento sobre os animais.",
                   "<b>Os dados são poucos.</b> Só peixes e insetos têm códigos de barras suficientes no Sul, e "
                   "a maioria das espécies tem menos de cinco. Os sapos, onde a ideia começou, não têm nenhuma "
                   "que se qualifique.",
                   "<b>Encontra o que já se sabe.</b> Testado contra casos publicados, anotados antes da rodada, "
                   "encontrou-os. Com que frequência dá alarme falso ainda não foi medido.",
                   "<b>Os insetos ainda não foram revisados.</b> {ins} nomes de insetos passam pelas mesmas "
                   "verificações e esperam a mesma leitura que os peixes tiveram."],
        "misid_h": "Postos de lado",
        "misid_p": "Nomes cujos códigos extras estão no grupo de outra espécie, ou que se dividem a uma distância "
                   "comum entre gêneros com outro gênero no mesmo grupo. Parecem mais problemas de rótulo do que "
                   "espécies ocultas, e ficam listados para quem guarda os exemplares.",
        "wanted_b": "Procura-se", "wanted_s": "taxonomistas de peixes do Sul",
        "wanted_p": "<b>Quais destas valem um olhar?</b> Se você trabalha com algum destes grupos, uma resposta "
                    "de uma linha ajuda a decidir o que examinar primeiro. Uma candidata que se sustente pode "
                    "virar uma descrição em coautoria.",
        "wanted_mail": "Escrever sobre Linhagens Ocultas",
        "data": "Dados: registros públicos do <a class=\"ln\" href=\"https://boldsystems.org\" target=\"_blank\" "
                "rel=\"noopener\">BOLD Systems</a>, baixados em {downloaded}. Delimitação de espécies com o ASAP "
                "(Puillandre et al. 2021). Contornos dos estados do IBGE. Gerado em {today}.",
        "back": "Voltar ao lab", "back_h": "Mais perguntas sobre seres vivos, resolvidas em software.",
        "colophon": "Composto em iA Writer Quattro e Mono, nas cores do Rei.",
    },
}

CSS = """
@font-face { font-family: Quattro; src: url(/assets/fonts/iAWriterQuattroS-Regular.woff2) format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: Quattro; src: url(/assets/fonts/iAWriterQuattroS-Italic.woff2) format("woff2"); font-weight: 400; font-style: italic; font-display: swap; }
@font-face { font-family: Quattro; src: url(/assets/fonts/iAWriterQuattroS-Bold.woff2) format("woff2"); font-weight: 700; font-display: swap; }
@font-face { font-family: Mono; src: url(/assets/fonts/iAWriterMonoS-Regular.woff2) format("woff2"); font-weight: 400; font-display: swap; }
/* Tokens: Rei, as on the lab. One voice (blue), true black, hairlines instead of panels. */
:root {
  --ground: #000; --raised: #0b0b0c; --line: #1f2024; --line-strong: #34363d; --grid: #0e1016;
  --ink: #e2e8e9; --ink-2: #aaaeaf; --ink-3: #7c7879; --voice: #617bb9; --voice-ink: #8ea3d6; --signal: #87deff;
  --sans: Quattro, ui-sans-serif, system-ui, sans-serif; --mono: Mono, ui-monospace, monospace;
  --gutter: clamp(16px, 5vw, 72px); --measure: 36rem;
}
* { box-sizing: border-box; margin: 0; }
html { background: var(--ground); color: var(--ink); -webkit-text-size-adjust: 100%; }
body { font: 400 17px/1.6 var(--sans); background: var(--ground); overflow-wrap: break-word; }
::selection { background: var(--voice); color: #fff; }
a { color: inherit; text-decoration: none; }
svg { display: block; max-width: 100%; height: auto; }
:focus-visible { outline: 1px solid var(--signal); outline-offset: 4px; }
.mono { font-family: var(--mono); font-size: 12.5px; letter-spacing: .02em; line-height: 1.7; }
.dim { color: var(--ink-3); }
.wrap { padding-inline: var(--gutter); max-width: 1440px; margin-inline: auto; }
.paper { background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px); background-size: 24px 24px; background-position: -1px -1px; }
.ln { background: linear-gradient(currentColor, currentColor) 0 100% / 100% 1px no-repeat; color: var(--voice-ink); transition: color .2s; padding-bottom: 1px; }
.ln:hover { color: var(--signal); }
.arrow::after { content: " ->"; font-family: var(--mono); font-size: .85em; }
.top { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px 24px; padding-block: 22px; border-bottom: 1px solid var(--line); }
.brand { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.name { font-weight: 700; }
.name:hover, .crumb:hover { color: var(--voice-ink); }
.crumb { color: var(--ink-2); transition: color .2s; }
.here { color: var(--voice-ink); }
.lang { color: var(--ink-3); }
.lang a:hover { color: var(--ink); }
.lang [aria-current] { color: var(--ink); }
.open { border-bottom: 1px solid var(--line); }
.open .wrap { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 26rem); gap: 48px; align-items: end; padding-block: clamp(56px, 10vh, 120px) clamp(40px, 7vh, 80px); }
.kicker { color: var(--ink-3); margin-bottom: 22px; }
h1 { font-weight: 400; font-size: clamp(34px, 5vw, 68px); line-height: 1.06; letter-spacing: -.028em; max-width: 15ch; text-wrap: balance; }
h1 em { font-style: italic; color: var(--voice-ink); }
.lede { color: var(--ink-2); font-size: 19px; line-height: 1.55; max-width: var(--measure); margin-top: 28px; text-wrap: pretty; }
.facts { display: grid; grid-template-columns: repeat(4, auto); justify-content: start; column-gap: 32px; row-gap: 14px; margin-top: 32px; padding-block: 16px; border-block: 1px solid var(--line); }
.facts div { display: flex; flex-direction: column; }
.facts dt { order: 2; color: var(--ink-3); }
.facts dd { order: 1; margin: 0; font-family: var(--sans); font-size: 26px; letter-spacing: -.02em; line-height: 1.2; }
.plate { border: 1px solid var(--line); padding: clamp(12px, 2vw, 20px); background: var(--ground); }
.plate figcaption { margin-top: 12px; color: var(--ink-3); }
.plate figcaption b { font-weight: 400; color: var(--ink-2); }
.states path { fill: none; stroke: var(--line-strong); stroke-width: 1; vector-effect: non-scaling-stroke; }
.dots circle { fill: #2c3b66; }
.dots .hit { fill: var(--voice-ink); }
.section { border-bottom: 1px solid var(--line); }
.head { display: grid; grid-template-columns: 15rem minmax(0, 1fr); gap: 48px; align-items: baseline; padding-top: clamp(56px, 9vh, 104px); }
.k { display: block; color: var(--voice-ink); text-transform: uppercase; letter-spacing: .14em; font-size: 11px; }
.head h2 { font-weight: 400; font-size: clamp(28px, 3.4vw, 46px); line-height: 1.1; letter-spacing: -.02em; }
.head p { color: var(--ink-2); margin-top: 10px; max-width: var(--measure); }
.body { padding-block: 40px clamp(56px, 9vh, 104px); }
.pipeline { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--line-strong); background: var(--ground); }
.pipeline li { padding: 18px 16px 20px; border-right: 1px solid var(--line-strong); position: relative; }
.pipeline li:last-child { border-right: 0; }
.pipeline li:not(:last-child)::after { content: "->"; font-family: var(--mono); font-size: 12px; color: var(--voice-ink); position: absolute; right: -10px; top: 18px; background: var(--ground); padding-inline: 2px; z-index: 1; }
.pipeline .n { color: var(--ink-3); display: block; }
.pipeline h3 { font-weight: 700; font-size: 16px; margin: 2px 0 4px; }
.pipeline .tech { color: var(--voice-ink); display: block; margin-bottom: 10px; }
.pipeline p { font-size: 14.5px; color: var(--ink-2); line-height: 1.5; }
.entry { display: grid; grid-template-columns: 15rem minmax(0, 1fr) 15rem; gap: 0 48px; padding-block: 40px; }
.entry + .entry { border-top: 1px dashed var(--line-strong); }
.label { border: 1px solid var(--line-strong); align-self: start; }
.label .catno { display: flex; justify-content: space-between; gap: 8px; padding: 9px 12px; border-bottom: 1px solid var(--line-strong); color: var(--ink-3); }
.label .catno b { font-weight: 400; color: var(--ink); }
.label dl { padding: 4px 12px 8px; }
.label dl div { padding: 7px 0; }
.label dl div + div { border-top: 1px dashed var(--line); }
.label dt { color: var(--ink-3); font-size: 10.5px; text-transform: uppercase; letter-spacing: .12em; line-height: 1.5; }
.label dd { margin: 0; }
.strong { color: var(--voice-ink); }
.text h3 { font-weight: 400; font-style: italic; font-size: clamp(24px, 2.4vw, 32px); letter-spacing: -.012em; line-height: 1.2; }
.text .common { color: var(--ink-2); margin-top: 10px; max-width: var(--measure); }
.text .plain { font-size: 19px; line-height: 1.55; margin-top: 14px; max-width: var(--measure); text-wrap: pretty; }
.spec { margin-top: 22px; padding-left: 14px; border-left: 2px solid var(--voice); max-width: var(--measure); color: var(--ink-2); }
.spec p + p { margin-top: 6px; }
.spec .k { margin-bottom: 6px; }
.mini figcaption { margin-top: 8px; display: flex; gap: 6px 14px; flex-wrap: wrap; color: var(--ink-3); }
.sw { display: inline-flex; align-items: center; gap: 6px; }
.sw::before { content: ""; width: 8px; height: 8px; border-radius: 50%; }
.sw.a::before { background: var(--voice-ink); }
.sw.b::before { border: 1.5px solid var(--ink); }
.pa { fill: var(--voice-ink); }
.pb { fill: none; stroke: var(--ink); stroke-width: 1.5; }
.limits { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.limits li { border: 1px dashed var(--line-strong); padding: 16px 18px; color: var(--ink-2); }
.limits b { color: var(--ink); font-weight: 700; }
.misid { list-style: none; padding: 0; max-width: 52rem; }
.misid li { padding: 12px 0; color: var(--ink-2); }
.misid li + li { border-top: 1px dashed var(--line); }
.misid i { color: var(--ink); }
.wanted { margin-top: 32px; border: 1px dashed var(--line-strong); max-width: var(--measure); }
.wanted .catno { display: flex; justify-content: space-between; gap: 8px; padding: 9px 14px; border-bottom: 1px dashed var(--line-strong); color: var(--ink-3); }
.wanted .catno b { font-weight: 400; color: var(--voice-ink); text-transform: uppercase; letter-spacing: .12em; font-size: 11px; }
.wanted p { padding: 14px; color: var(--ink-2); }
.wanted p b { color: var(--ink); }
.wanted .links { padding: 0 14px 16px; }
.links { display: flex; flex-wrap: wrap; gap: 8px 28px; margin-top: 20px; }
.source { color: var(--ink-3); max-width: 52rem; margin-top: 28px; }
.hub { display: grid; grid-template-columns: 15rem minmax(0, 1fr); gap: 48px; padding-block: clamp(56px, 9vh, 96px); border-bottom: 1px solid var(--line); }
.hub h2 { font-weight: 400; font-size: clamp(26px, 3vw, 40px); line-height: 1.15; letter-spacing: -.02em; max-width: 22ch; }
.colophon { display: flex; justify-content: space-between; gap: 12px 24px; padding-block: 24px 40px; flex-wrap: wrap; }
@media (max-width: 1100px) {
  .entry { grid-template-columns: 15rem minmax(0, 1fr); }
  .mini { grid-column: 2; margin-top: 24px; max-width: 15rem; }
}
@media (max-width: 960px) {
  .open .wrap, .head, .hub { grid-template-columns: 1fr; gap: 24px; }
  .entry { grid-template-columns: 1fr; gap: 20px; }
  .text { order: 1; } .label { order: 2; } .mini { order: 3; grid-column: 1; margin-top: 0; }
  .pipeline { grid-template-columns: 1fr; }
  .pipeline li { border-right: 0; border-bottom: 1px solid var(--line-strong); }
  .pipeline li:last-child { border-bottom: 0; }
  .pipeline li:not(:last-child)::after { content: "v"; right: auto; left: 16px; top: auto; bottom: -11px; }
  .limits { grid-template-columns: 1fr; }
  .label dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(8rem, 1fr)); column-gap: 20px; }
}
@media (max-width: 560px) {
  body { font-size: 16px; }
  .lede, .text .plain { font-size: 17px; }
  .facts { grid-template-columns: repeat(2, auto); }
  .facts dd { font-size: 22px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""


def num(x, lang):
    return f"{x:,}".replace(",", "." if lang == "pt" else ",")


def pct(x, lang):
    s = f"{x:.1f}"
    return s.replace(".", ",") if lang == "pt" else s


def pval(p, lang):
    s = f"{p:.0e}" if p < 0.01 else f"{p:.2f}"
    return s.replace(".", ",") if lang == "pt" else s


def states_symbol():
    """The three state outlines, drawn once per page and reused by every map."""
    _, w, h = projector(MAP_W)
    return (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="states" '
            f'viewBox="0 0 {w:.0f} {h:.0f}"><g class="states">{outlines(MAP_W)}</g></symbol></svg>')


def overview(all_sites, hit_sites):
    xy, w, h = projector(MAP_W)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.9"/>' for x, y in (xy(*s) for s in sorted(all_sites - hit_sites)))
    hits = "".join(f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="1.5"/>' for x, y in (xy(*s) for s in sorted(hit_sites)))
    return (f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="420" height="{420 * h / w:.0f}" aria-hidden="true">'
            f'<use href="#states"/><g class="dots">{dots}{hits}</g></svg>')


def mini(coords_a, coords_b, alt):
    xy, w, h = projector(MAP_W)
    a = "".join(f'<circle class="pa" cx="{x:.1f}" cy="{y:.1f}" r="4"/>' for x, y in (xy(*s) for s in sorted({site(c) for c in coords_a})))
    b = "".join(f'<circle class="pb" cx="{x:.1f}" cy="{y:.1f}" r="5.5"/>' for x, y in (xy(*s) for s in sorted({site(c) for c in coords_b})))
    return (f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{escape(alt)}">'
            f'<use href="#states"/>{a}{b}</svg>')


def page(lang, d, counts, all_sites, insect_candidates):
    t = TEXT[lang]
    downloaded = date.fromtimestamp((DATA / "brazil.tsv").stat().st_mtime).isoformat()
    species, bin_names, coords, asap, notes = d["species"], d["bin_names"], d["coords"], d["asap"], d["notes"]
    note_key, plain_key = ("note", "plain") if lang == "en" else ("note_pt", "plain_pt")
    hit_sites = {site(c) for name, b1, b2, *_ in d["kept"] for b in (b1, b2) for c in coords[name, b]}
    base = "https://hidden-lineages.lab.eduardofrafre.com/"

    entries = []
    for i, (name, b1, b2, med, lo, hi, _) in enumerate(d["kept"], 1):
        own = [b for b in species[name] if owner(bin_names, b) == name]
        label, sa, sb, km = pattern(coords[name, b1], coords[name, b2])
        row = asap.get(name)
        rank = int(row["bin_rank"]) if row else 0
        p = float(row["bin_p"]) if rank else None
        if not rank:
            asap_short, asap_line = t["asap_none"], t["asap_line_none"]
        else:
            r = "" if rank == 1 else t["rank"].format(r=rank)
            strong = p < 0.05
            asap_short = t["asap_strong" if strong else "asap_weak"].format(p=pval(p, lang))
            asap_line = t["asap_line_strong" if strong else "asap_line_weak"].format(p=pval(p, lang), rank=r)
        tier = t["tier_deep"] if med >= 3 else t["tier_edge"] if med >= 2 else t["tier_shallow"]
        note = notes.get(name, {})
        published = (t["published"].format(source=escape(note["source"]), note=escape(note.get(note_key, "")))
                     if note.get("source") else t["unpublished"].format(note=escape(note.get(note_key, ""))))
        bins = ", ".join(f"{b} ({c})" for b, c in species[name].most_common())
        n = sum(species[name].values())
        entries.append(f"""
    <article class="wrap entry" id="hl-{i:02d}">
      <aside class="label mono" aria-label="Specimen label">
        <div class="catno"><span>{t['lbl_catno']}</span><b>HL-{i:02d}</b></div>
        <dl>
          <div><dt>{t['lbl_barcodes']}</dt><dd>{n}</dd></div>
          <div><dt>{t['lbl_groups']}</dt><dd>{len(own)}</dd></div>
          <div><dt>{t['lbl_distance']}</dt><dd>{pct(med, lang)}%</dd></div>
          <div><dt>{t['lbl_asap']}</dt><dd{' class="strong"' if p is not None and p < 0.05 else ''}>{asap_short}</dd></div>
          <div><dt>{t['lbl_sites']}</dt><dd>{t['sites'][label]}</dd></div>
        </dl>
      </aside>
      <div class="text">
        <h3>{escape(name)}</h3>
        <p class="common">{escape(note.get(plain_key, ''))}</p>
        <p class="plain">{t['split'].format(k=t['groups_n'].get(len(own), len(own)), med=pct(med, lang))} {tier}</p>
        <div class="spec mono">
          <span class="k">{t['for_specialists']}</span>
          <p>{t['bins'].format(bins=bins)} {asap_line}</p>
          <p>{t['where'][label].format(sa=sa, sb=sb, km=f"{km:.0f}")}</p>
          <p>{published}</p>
        </div>
      </div>
      <figure class="mini plate paper">
        {mini(coords[name, b1], coords[name, b2], t['map_alt'].format(name=name))}
        <figcaption class="mono"><span class="sw a">{t['legend_a']}</span><span class="sw b">{t['legend_b']}</span></figcaption>
      </figure>
    </article>""")

    misid_items = []
    for name, b1, b2, med, _, _, others in d["demoted"]:
        misid_items.append(f"<li><i>{escape(name)}</i>: {b1} / {b2}, {pct(med, lang)}%, "
                           f"{', '.join(f'<i>{escape(o)}</i>' for o in others)}. {escape(notes.get(name, {}).get(note_key, ''))}</li>")
    for name in d["misids"]:
        parts = ", ".join(f"{c} &rarr; {b} (<i>{escape(owner(bin_names, b))}</i>)" for b, c in species[name].items()
                          if owner(bin_names, b) not in (name, None))
        misid_items.append(f"<li><i>{escape(name)}</i>: {parts}. {escape(notes.get(name, {}).get(note_key, ''))}</li>")

    facts = "".join(f"<div><dd>{num(counts[key], lang)}</dd><dt>{label}</dt></div>" for label, key in t["facts"])
    how = "".join(f'<li><span class="n mono">{i:02d}</span><h3>{h}</h3><span class="tech mono">{tech}</span><p>{p}</p></li>'
                  for i, (h, tech, p) in enumerate(t["how"], 1))
    limits = "".join(f"<li>{x.format(ins=insect_candidates)}</li>" for x in t["limits"])
    lab = "https://lab.eduardofrafre.com/" + ("" if lang == "en" else "pt-br/")

    return f"""<!doctype html>
<html lang="{t['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['title']}</title>
<meta name="description" content="{escape(t['description'])}">
<meta name="theme-color" content="#000000">
<link rel="canonical" href="{base}{'' if lang == 'en' else 'pt-br/'}">
<link rel="alternate" hreflang="en" href="{base}">
<link rel="alternate" hreflang="pt-BR" href="{base}pt-br/">
<link rel="alternate" hreflang="x-default" href="{base}">
<link rel="preload" href="/assets/fonts/iAWriterQuattroS-Regular.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
</head>
<body>
{states_symbol()}
<header class="wrap top">
  <div class="brand">
    <a class="name" href="https://eduardofrafre.com" target="_blank" rel="noopener">Eduardo Freitas</a>
    <a class="mono crumb" href="{lab}">/ Lab</a>
    <span class="mono here">/ {'Hidden Lineages' if lang == 'en' else 'Linhagens Ocultas'}</span>
  </div>
  <nav class="mono" aria-label="Language">
    <span class="lang"><span aria-current="true">{t['here_label']}</span> / <a href="{t['other']}" hreflang="{'pt-BR' if lang == 'en' else 'en'}" title="{t['other_title']}">{t['other_label']}</a></span>
  </nav>
</header>
<main>
  <div class="open paper">
    <div class="wrap">
      <div>
        <p class="kicker mono">{t['kicker']}</p>
        <h1>{t['h1']}</h1>
        <p class="lede">{t['lede']}</p>
        <dl class="facts mono">{facts}</dl>
      </div>
      <figure class="plate">
        {overview(all_sites, hit_sites)}
        <figcaption class="mono">{t['plate1']}</figcaption>
      </figure>
    </div>
  </div>

  <section class="section" aria-labelledby="how-h">
    <div class="wrap head"><span class="k mono">{t['how_k']}</span><h2 id="how-h">{t['how_h']}</h2></div>
    <div class="wrap body">
      <figure><ol class="pipeline">{how}</ol>
      <figcaption class="mono dim" style="margin-top:12px">{t['fig2']}</figcaption></figure>
    </div>
  </section>

  <section class="section" aria-labelledby="cands-h">
    <div class="wrap head">
      <span class="k mono">{t['cands_k']}</span>
      <div><h2 id="cands-h">{t['cands_h']}</h2><p>{t['cands_p']}</p></div>
    </div>
    {''.join(entries)}
  </section>

  <section class="section" aria-labelledby="limits-h">
    <div class="wrap head"><span class="k mono">{t['limits_k']}</span><h2 id="limits-h">{t['limits_h']}</h2></div>
    <div class="wrap body">
      <ul class="limits">{limits}</ul>
    </div>
  </section>

  <section class="section" aria-labelledby="misid-h">
    <div class="wrap head"><span class="k mono">{t['misid_h']}</span><div><h2 id="misid-h">{t['misid_h']}</h2><p>{t['misid_p']}</p></div></div>
    <div class="wrap body">
      <ul class="misid mono">{''.join(misid_items)}</ul>
      <div class="wanted mono">
        <div class="catno"><b>{t['wanted_b']}</b><span>{t['wanted_s']}</span></div>
        <p>{t['wanted_p']}</p>
        <div class="links"><a class="ln" href="mailto:contact@eduardofrafre.com?subject=Hidden%20Lineages">{t['wanted_mail']}</a></div>
      </div>
      <p class="source mono">{t['data'].format(downloaded=downloaded, today=date.today().isoformat())}</p>
    </div>
  </section>
</main>
<footer>
  <div class="wrap hub">
    <div class="mono dim">Lab</div>
    <div>
      <h2>{t['back_h']}</h2>
      <div class="links mono"><a class="ln arrow" href="{lab}">{t['back']}</a><a class="ln" href="mailto:contact@eduardofrafre.com">contact@eduardofrafre.com</a></div>
    </div>
  </div>
  <div class="wrap colophon mono dim"><p>{t['colophon']}</p><p>© 2026 Eduardo Freitas</p></div>
</footer>
</body>
</html>
"""


if __name__ == "__main__":
    d = build("Teleostei")
    usable = list(barcodes(DATA / "brazil.tsv"))
    split = 0
    for cls in ("Teleostei", "Insecta"):
        sp = load(cls)[0]
        split += sum(1 for v in sp.values() if sum(v.values()) >= 5 and len(v) >= 2)
    insects = build("Insecta")
    counts = {"south": sum(1 for _ in south_records(DATA / "brazil.tsv")), "usable": len(usable),
              "split": split, "cands": len(d["kept"])}
    all_sites = {site(r["_coord"]) for r in usable}
    (OUT / "pt-br").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    for f in LAB.glob("*.woff2"):
        shutil.copy(f, OUT / "assets" / "fonts" / f.name)
    (OUT / "index.html").write_text(page("en", d, counts, all_sites, len(insects["kept"])))
    (OUT / "pt-br" / "index.html").write_text(page("pt", d, counts, all_sites, len(insects["kept"])))
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    print(f"wrote site/: {counts}, {len(all_sites)} sites, {len(insects['kept'])} insect candidates")

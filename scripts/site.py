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
        "nav_label": "Sites and sections", "tools": "Tools",
        "sections": [("candidates", "Candidates"), ("limits", "Limits"), ("support", "Support")],
        "crumb": "hidden lineages", "theme": "Light theme", "og_locale": ("en_US", "pt_BR"), "og_image": "og.png",
        "other_title": "Versão em português",
        "title": "Hidden Lineages · Lab · Eduardo Freitas",
        "description": "Fish of southern Brazil whose public DNA barcodes suggest more than one species under a "
                       "single name: seven candidates, with the evidence behind each.",
        "kicker": "Lab notebook · ECO-02 · Southern Atlantic Forest",
        "h1": "Some fish may be <em>two species</em> under one name.",
        "lede": "A DNA barcode works like a species fingerprint. Where one name carries two clearly different "
                "fingerprints, it may be hiding a species nobody has described. This reads every public barcode "
                "from Paraná, Santa Catarina and Rio Grande do Sul and lists the names most likely to.",
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
        "fig2": "<b>Fig. 1.</b> Each step removes a kind of false alarm.",
        "cands_k": "The candidates",
        "cands_h": "Seven fish worth a second look",
        "cands_p": "None is a new species yet: each is a question for someone who can examine the fish.",
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
        "limits": ["<b>These are candidates, not new species.</b> One gene can mislead; naming a species takes more.",
                   "<b>The data are thin.</b> Most species have fewer than five barcodes here.",
                   "<b>Tested on known cases, it found them.</b> Its false-alarm rate is not measured yet.",
                   "<b>Insects are not reviewed yet.</b> {ins} names wait for the same reading."],
        "misid_h": "Set aside",
        "misid_p": "Three names that look more like labelling problems than hidden species.",
        "misid_fold": "The three names",
        "wanted_b": "Wanted", "wanted_s": "taxonomists who know southern fish",
        "wanted_p": "<b>Which of these are worth a look?</b> If you work on southern fish, a one-line answer "
                    "helps. A candidate that holds up could become a co-authored description.",
        "mail": "contact@eduardofrafre.com",
        "wanted_mail": "Write about Hidden Lineages",
        "give_k": "Support", "give_h": "Free, and staying free.",
        "give_p": "This page and the candidate list are free and stay free. A donation pays for hosting, "
                  "data and the hours the insect review still needs.",
        "give_link": "Donate by PayPal", "give_qr": "scan to donate",
        "give_alt": "QR code for the PayPal donation page",
        "pay_default": "paypal", "pay_group": "Payment method",
        "pix_copy": "Copy the Pix code", "pix_done": "Copied, paste it in your bank app",
        "pix_key": "Pix key", "pix_qr": "scan with your bank app",
        "pix_alt": "Pix QR code for a donation of any amount",
        "data": "Data: public records from <a class=\"ln\" href=\"https://boldsystems.org\" target=\"_blank\" "
                "rel=\"noopener\">BOLD Systems</a>, downloaded {downloaded}. Species delimitation with ASAP "
                "(Puillandre et al. 2021). State outlines from IBGE. Generated {today}.",
        "back": "Back to the lab", "back_h": "More questions about living things, worked out in software.",
        "colophon": "Set in iA Writer Quattro and Mono, in the colours of Rei.",
    },
    "pt": {
        "lang": "pt-BR", "root": "../", "other": "../", "other_label": "EN", "here_label": "PT",
        "nav_label": "Sites e seções", "tools": "Ferramentas",
        "sections": [("candidates", "Candidatos"), ("limits", "Limites"), ("support", "Apoio")],
        "crumb": "linhagens ocultas", "theme": "Tema claro", "og_locale": ("pt_BR", "en_US"), "og_image": "og-pt.png",
        "other_title": "English version",
        "title": "Linhagens Ocultas · Lab · Eduardo Freitas",
        "description": "Peixes do Sul do Brasil cujos códigos de barras de DNA públicos sugerem mais de uma espécie "
                       "sob um único nome: sete candidatas, com as evidências de cada uma.",
        "kicker": "Caderno do lab · ECO-02 · Mata Atlântica do Sul",
        "h1": "Alguns peixes podem ser <em>duas espécies</em> com um só nome.",
        "lede": "Um código de barras de DNA funciona como a impressão digital de uma espécie. Quando um nome "
                "carrega duas impressões claramente diferentes, ele pode estar escondendo uma espécie que ninguém "
                "descreveu. Este projeto lê todos os códigos de barras públicos do Paraná, de Santa Catarina e do "
                "Rio Grande do Sul e lista os nomes com mais chance de esconder uma.",
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
        "fig2": "<b>Fig. 1.</b> Cada etapa tira um tipo de alarme falso.",
        "cands_k": "As candidatas",
        "cands_h": "Sete peixes que merecem um segundo olhar",
        "cands_p": "Nenhuma é espécie nova ainda: cada uma é uma pergunta para quem pode examinar os peixes.",
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
        "limits": ["<b>São candidatas, não espécies novas.</b> Um gene só pode enganar; nomear uma espécie exige mais.",
                   "<b>Os dados são poucos.</b> A maioria das espécies tem menos de cinco códigos aqui.",
                   "<b>Testado em casos conhecidos, encontrou-os.</b> A taxa de alarme falso ainda não foi medida.",
                   "<b>Os insetos ainda não foram revisados.</b> {ins} nomes esperam a mesma leitura."],
        "misid_h": "Postos de lado",
        "misid_p": "Três nomes que parecem mais problemas de rótulo do que espécies ocultas.",
        "misid_fold": "Os três nomes",
        "wanted_b": "Procura-se", "wanted_s": "taxonomistas de peixes do Sul",
        "wanted_p": "<b>Quais destas valem um olhar?</b> Se você trabalha com peixes do Sul, uma resposta de uma "
                    "linha ajuda. Uma candidata que se sustente pode virar uma descrição em coautoria.",
        "mail": "contato@eduardofrafre.com",
        "wanted_mail": "Escrever sobre Linhagens Ocultas",
        "give_k": "Apoiar", "give_h": "Gratuito, e continua assim.",
        "give_p": "Esta página e a lista de candidatas são gratuitas e continuam gratuitas. Uma doação paga "
                  "hospedagem, dados e as horas que a revisão dos insetos ainda pede.",
        "give_link": "Doar pelo PayPal", "give_qr": "aponte a câmera para doar",
        "give_alt": "QR code da página de doação no PayPal",
        "pay_default": "pix", "pay_group": "Forma de pagamento",
        "pix_copy": "Copiar o código Pix", "pix_done": "Copiado, cole no app do banco",
        "pix_key": "Chave Pix", "pix_qr": "leia no app do banco",
        "pix_alt": "QR code Pix para doar qualquer valor",
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
/* Tokens: Rei, as on the lab. One voice (blue), true black, hairlines instead
   of panels. Light is warm paper and a deeper blue; the maps are drawn with
   these tokens, so they follow the theme. */
:root {
  --ground: #000; --raised: #0b0b0c; --line: #1f2024; --line-strong: #34363d;
  --ink: #e2e8e9; --ink-2: #aaaeaf; --ink-3: #7c7879; --voice: #617bb9; --voice-ink: #8ea3d6;
  --signal: #87deff; --signal-fill: #87deff; --violet: #9987c3; --dot: #3a3e48;
  --sans: Quattro, ui-sans-serif, system-ui, sans-serif; --mono: Mono, ui-monospace, monospace;
  --gutter: clamp(16px, 5vw, 72px); --measure: 36rem;
  color-scheme: dark;
}
:root[data-theme="light"] {
  --ground: #f3f3f0; --raised: #e8e8e3; --line: #dcdcd5; --line-strong: #c3c3bb;
  --ink: #121315; --ink-2: #45474d; --ink-3: #63656c; --voice: #2a48d4; --voice-ink: #2a48d4;
  --signal: #086a98; --signal-fill: #5bbfe8; --violet: #5d4a9c; --dot: #c2c2b9;
  color-scheme: light;
}
* { box-sizing: border-box; margin: 0; }
html { background: var(--ground); color: var(--ink); -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body { font: 400 17px/1.6 var(--sans); background: var(--ground); overflow-wrap: break-word; }
::selection { background: var(--voice); color: #fff; }
a { color: inherit; text-decoration: none; }
p { text-wrap: pretty; }
svg { display: block; max-width: 100%; height: auto; }
:focus-visible { outline: 1px solid var(--signal); outline-offset: 4px; }
.mono { font-family: var(--mono); font-size: 12.5px; letter-spacing: .02em; line-height: 1.7; }
.dim { color: var(--ink-3); }
.wrap { padding-inline: var(--gutter); max-width: 1440px; margin-inline: auto; }
.ln { color: var(--voice-ink); text-decoration: underline 1px; text-underline-offset: 4px; transition: color .2s; }
.ln:hover { color: var(--signal); }
.arrow::after { content: " ->"; font-family: var(--mono); font-size: .85em; }

/* ── Masthead: the same on every family site ─────────────────────
   The domain goes home, the crumbs say where you are, the three sites
   come first, then this page's sections, the language and the theme.
   On a phone the menu is one row under the domain. */
.top { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px 24px; padding-block: 22px; border-bottom: 1px solid var(--line); }
.brand { display: flex; align-items: baseline; flex-wrap: wrap; gap: 10px; }
.name { color: var(--ink); transition: color .2s; }
.name:hover, .crumb:hover { color: var(--voice-ink); }
.crumb { color: var(--ink-2); transition: color .2s; }
.here { color: var(--voice-ink); }
.top nav { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 28px; }
.top nav .out { display: flex; gap: 28px; padding-right: 28px; border-right: 1px solid var(--line-strong); }
.top nav a { color: var(--ink-2); transition: color .2s; }
.top nav a:hover { color: var(--ink); }
.top nav .out [aria-current] { color: var(--voice-ink); }
.lang { color: var(--ink-3); white-space: nowrap; }
.lang a { color: var(--ink-3) !important; }
.lang a:hover { color: var(--ink) !important; }
.lang [aria-current] { color: var(--ink); }
.theme { align-self: center; display: grid; place-items: center; width: 24px; height: 24px; margin: -4px -4px -4px -12px; padding: 0; border: 0; background: none; color: var(--ink-3); cursor: pointer; transition: color .2s; }
.theme:hover { color: var(--ink); }
.theme svg { width: 14px; height: 14px; transition: transform .4s cubic-bezier(.2,.7,.2,1); }
[data-theme="light"] .theme svg { transform: rotate(180deg); }

/* ── Opening: the title page and the map of every site ───────── */
.open .wrap { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 26rem); gap: 48px; align-items: end; padding-block: clamp(72px, 12vh, 128px) clamp(56px, 9vh, 96px); }
.kicker { color: var(--ink-3); margin-bottom: 20px; }
h1 { font-weight: 400; font-size: clamp(34px, 4vw, 56px); line-height: 1.1; letter-spacing: -.024em; max-width: 14em; }
h1 em { font-style: normal; color: var(--voice-ink); }
.lede { color: var(--ink-2); font-size: 19px; line-height: 1.55; max-width: var(--measure); margin-top: 24px; }
.facts { display: flex; flex-wrap: wrap; gap: 14px 40px; margin-top: 32px; }
.facts div { display: flex; flex-direction: column; }
.facts dt { order: 2; color: var(--ink-3); }
.facts dd { margin: 0; font-family: var(--sans); font-size: 30px; letter-spacing: -.02em; line-height: 1.2; color: var(--ink); font-variant-numeric: tabular-nums; }
.plate { margin: 0; }
.plate svg { width: 100%; padding: clamp(12px, 2vw, 24px); background: var(--raised); border: 1px solid var(--line); }
.plate figcaption { margin-top: 12px; color: var(--ink-3); }
.plate figcaption b { font-weight: 400; color: var(--ink-2); }
.states path { fill: none; stroke: var(--line-strong); stroke-width: 1; vector-effect: non-scaling-stroke; }
.dots circle { fill: var(--dot); }
.dots .hit { fill: var(--voice-ink); }

/* ── Sections: a quiet label, then the heading ───────────────── */
.section { border-top: 1px solid var(--line); }
.head { padding-top: clamp(64px, 10vh, 112px); }
.k { display: block; font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 14px; }
.head h2 { font-weight: 400; font-size: 28px; line-height: 1.3; letter-spacing: -.01em; text-wrap: balance; }
.head p { color: var(--ink-2); margin-top: 6px; max-width: var(--measure); }
.body { padding-block: 36px clamp(64px, 10vh, 112px); }
.pipeline { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border-block: 1px solid var(--line-strong); }
.pipeline li { padding: 20px 20px 22px 0; }
.pipeline li + li { padding-left: 20px; border-left: 1px solid var(--line); }
.pipeline .n { color: var(--ink-3); display: block; }
.pipeline h3 { font-weight: 400; font-size: 19px; margin: 4px 0 2px; }
.pipeline .tech { color: var(--voice-ink); display: block; }
figure > figcaption.dim { margin-top: 12px; }

/* ── A candidate: the catalogue line, the fish, the map beside ── */
.entry { display: grid; grid-template-columns: minmax(0, 1fr) 15rem; grid-template-rows: auto 1fr; column-gap: clamp(32px, 5vw, 72px); padding-block: 40px; }
.entry + .entry { border-top: 1px solid var(--line); }
.entry > .label, .entry > .text { grid-column: 1; }
.entry > .mini { grid-column: 2; grid-row: 1 / -1; }
.label { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 20px; color: var(--ink-3); }
.label .catno span { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.label .catno b { font-weight: 400; color: var(--voice-ink); }
.label dl { display: contents; }
.label dl div { display: inline-flex; gap: 6px; }
.label dt { text-transform: lowercase; }
.label dd { margin: 0; color: var(--ink-2); }
.label .strong { color: var(--signal); }
.text h3 { font-weight: 400; font-style: italic; font-size: clamp(26px, 2.6vw, 32px); letter-spacing: -.015em; line-height: 1.2; margin-top: 14px; }
.text .common { color: var(--ink-2); margin-top: 8px; max-width: var(--measure); }
.spec { margin-top: 20px; max-width: var(--measure); color: var(--ink-2); }
.spec p + p { margin-top: 6px; }
.spec summary, .misid-fold summary { display: inline-flex; gap: 6px; cursor: pointer; list-style: none; color: var(--ink-2); text-transform: none; letter-spacing: .02em; font-size: 12.5px; margin: 0; transition: color .2s; }
.spec summary::-webkit-details-marker, .misid-fold summary::-webkit-details-marker { display: none; }
.spec summary::after, .misid-fold summary::after { content: "+"; color: var(--voice-ink); }
.spec[open] summary::after, .misid-fold[open] summary::after { content: "\2013"; }
.spec summary:hover, .misid-fold summary:hover { color: var(--ink); }
.spec[open] summary { margin-bottom: 8px; }
.misid-fold[open] summary { margin-bottom: 14px; }
.mini svg { width: 100%; }
.mini figcaption { margin-top: 8px; display: flex; gap: 6px 14px; flex-wrap: wrap; color: var(--ink-3); }
.sw { display: inline-flex; align-items: center; gap: 6px; }
.sw::before { content: ""; width: 8px; height: 8px; border-radius: 50%; }
.sw.a::before { background: var(--voice-ink); }
.sw.b::before { border: 1.5px solid var(--ink); }
.pa { fill: var(--voice-ink); }
.pb { fill: none; stroke: var(--ink); stroke-width: 1.5; }

/* ── Limits, the names set aside, and the call ───────────────── */
.limits { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 48px; border-top: 1px solid var(--line-strong); }
.limits li { padding-block: 16px; border-bottom: 1px solid var(--line); color: var(--ink-2); }
.limits b { color: var(--ink); font-weight: 400; }
.misid { list-style: none; padding: 0; max-width: 52rem; }
.misid li { padding: 12px 0; color: var(--ink-2); }
.misid li + li { border-top: 1px solid var(--line); }
.misid i { color: var(--ink); }
.wanted { margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--line); max-width: var(--measure); }
.wanted .catno { display: flex; flex-wrap: wrap; gap: 4px 12px; color: var(--ink-3); }
.wanted .catno b { font-weight: 400; color: var(--voice-ink); }
.wanted p { color: var(--ink-2); margin-top: 6px; }
.wanted p b { color: var(--ink); font-weight: 400; }
.links { display: flex; flex-wrap: wrap; gap: 8px 28px; margin-top: 16px; }
.source { color: var(--ink-3); max-width: 52rem; margin-top: 32px; }

/* ── Small screens ───────────────────────────────────────────── */
@media (max-width: 960px) {
  .open .wrap { grid-template-columns: 1fr; }
  .entry { grid-template-columns: minmax(0, 1fr); grid-template-rows: none; }
  .entry > .mini { grid-column: 1; grid-row: auto; max-width: 28rem; margin-top: 24px; }
  .pipeline { grid-template-columns: 1fr; }
  .pipeline li { padding-right: 0; }
  .pipeline li + li { padding-left: 0; border-left: 0; border-top: 1px solid var(--line); }
  .limits { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  body { font-size: 16px; }
  .top { padding-block: 18px 0; row-gap: 12px; }
  .top nav { width: 100%; flex-wrap: nowrap; align-items: center; gap: 0; padding-block: 12px; border-top: 1px solid var(--line); }
  .top nav .out { gap: 20px; padding-right: 0; border-right: 0; }
  .top nav > a { display: none; }
  .lang { margin-left: auto; }
  .theme { margin: -4px -4px -4px 16px; }
  .open .wrap { padding-block: 48px 40px; gap: 36px; }
  h1 { font-size: 34px; text-wrap: balance; }
  .lede { font-size: 17px; }
  .facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 16px; }
  .facts dd { font-size: 24px; }
  .head { padding-top: 56px; }
  .head h2 { font-size: 24px; }
  .body { padding-block: 28px 56px; }
  .entry { padding-block: 32px; }
  .text h3 { font-size: 26px; }
  .entry > .mini { max-width: none; }
  .pipeline li { display: grid; grid-template-columns: 2.25rem minmax(0, 1fr); padding-block: 14px; }
  .pipeline li > * { grid-column: 2; }
  .pipeline .n { grid-column: 1; grid-row: 1 / span 2; padding-top: 4px; }
  .pipeline h3 { margin-top: 0; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } html { scroll-behavior: auto; } }
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


# Shared with the other sites under eduardofrafre.com: the root follows the
# browser language, and the icon is this page's mark in the family palette.
LANG_SCRIPT = '<script>\n// The root follows the browser\'s language until a visitor picks one with the\n// EN / PT switch. The pick is a cookie on eduardofrafre.com, so it carries over\n// to every subdomain.\n(function () {\n  var host = location.hostname, domain = /(^|\\.)eduardofrafre\\.com$/.test(host) ? "; Domain=eduardofrafre.com" : "";\n  document.addEventListener("click", function (e) {\n    var a = e.target.closest && e.target.closest("a[hreflang]");\n    if (!a || a.host !== location.host) return;\n    var pick = /^pt/i.test(a.hreflang) ? "pt" : "en";\n    document.cookie = "lang=" + pick + domain + "; Path=/; Max-Age=31536000; SameSite=Lax";\n  });\n  if (/^\\/pt-br(\\/|$)/.test(location.pathname)) return;\n  var m = document.cookie.match(/(?:^|; )lang=(en|pt)/), lang = m && m[1];\n  if (!lang) {\n    var list = navigator.languages || [navigator.language || ""];\n    for (var i = 0; i < list.length; i++) {\n      var code = String(list[i]).slice(0, 2).toLowerCase();\n      if (code === "pt" || code === "en") { lang = code; break; }\n    }\n  }\n  if (lang === "pt") location.replace("/pt-br/" + location.search + location.hash);\n})();\n</script>\n'
FAVICON = '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 48 48\'%3E%3Cstyle%3E.s%7Bfill:none;stroke:%232a48d4;stroke-width:4.5%7D.c%7Bfill:none;stroke:%231e9fd8;stroke-width:5%7D%40media %28prefers-color-scheme:dark%29%7B.s%7Bstroke:%238ea3d6%7D.c%7Bstroke:%2387deff%7D%7D%3C/style%3E%3Cpath class=\'s\' d=\'M5 22h11M16 7.75v28.5M16 8h27M16 36h9M25 26v18M25 26.25h18\'/%3E%3Cpath class=\'c\' d=\'M25 42h18\'/%3E%3C/svg%3E">\n'


# Dark is the house colour; the masthead's toggle switches to light, kept in a
# cookie on eduardofrafre.com like the language. Set before the first paint.
THEME_SCRIPT = ('<script>\n(function () {\n  var m = document.cookie.match(/(?:^|; )theme=(light|dark)/);\n'
                '  if (m) document.documentElement.dataset.theme = m[1];\n})();\n</script>\n')
TOGGLE = """    <button class="theme" type="button" aria-pressed="false" aria-label="{label}" title="{label}"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M8 1.5a6.5 6.5 0 0 0 0 13z" fill="currentColor"/></svg></button>
  </nav>
  <script>
  (function () {{
    var b = document.querySelector(".theme"), root = document.documentElement, meta = document.querySelector('meta[name="theme-color"]');
    var domain = /(^|\\.)eduardofrafre\\.com$/.test(location.hostname) ? "; Domain=eduardofrafre.com" : "";
    function show() {{ var light = root.dataset.theme === "light"; b.setAttribute("aria-pressed", light); if (meta) meta.content = light ? "#f3f3f0" : "#000000"; }}
    b.addEventListener("click", function () {{
      root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
      document.cookie = "theme=" + root.dataset.theme + domain + "; Path=/; Max-Age=31536000; SameSite=Lax";
      show();
    }});
    show();
  }})();
  </script>"""


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
        <details class="spec mono"><summary class="k">{t['for_specialists']}</summary>
          <p>{t['bins'].format(bins=bins)} {asap_line}</p>
          <p>{t['where'][label].format(sa=sa, sb=sb, km=f"{km:.0f}")}</p>
          <p>{published}</p>
        </details>
      </div>
      <figure class="mini plate">
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

    facts = "".join(f"<div><dt>{label}</dt><dd>{num(counts[key], lang)}</dd></div>" for label, key in t["facts"])
    how = "".join(f'<li><span class="n mono">{i:02d}</span><h3>{h}</h3><span class="tech mono">{tech}</span></li>'
                  for i, (h, tech, p) in enumerate(t["how"], 1))
    limits = "".join(f"<li>{x.format(ins=insect_candidates)}</li>" for x in t["limits"])
    sfx = "" if lang == "en" else "pt-br/"
    lab = "https://lab.eduardofrafre.com/" + sfx
    out = "".join(f'<a href="https://{h}.eduardofrafre.com/{sfx}"{' aria-current="true"' if h == "lab" else ""}>{n}</a>'
                  for h, n in (("lab", "Lab"), ("tools", t["tools"]), ("studio", "Studio")))
    sections = "\n".join(f'    <a href="#{i}">{n}</a>' for i, n in t["sections"])
    other_lang = "pt-BR" if lang == "en" else "en"
    langs = (f'<span aria-current="true">EN</span> / <a href="pt-br/" hreflang="pt-BR" lang="pt-BR" title="{t["other_title"]}">PT</a>'
             if lang == "en" else
             f'<a href="../" hreflang="en" lang="en" title="{t["other_title"]}">EN</a> / <span aria-current="true">PT</span>')

    return f"""<!doctype html>
<html lang="{t['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['title']}</title>
<meta name="description" content="{escape(t['description'])}">
<meta name="theme-color" content="#000000">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Eduardo Freitas">
<meta property="og:title" content="{t['title']}">
<meta property="og:description" content="{escape(t['description'])}">
<meta property="og:url" content="{base}{sfx}">
<meta property="og:image" content="{base}assets/{t['og_image']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{t['title']}">
<meta property="og:locale" content="{t['og_locale'][0]}">
<meta property="og:locale:alternate" content="{t['og_locale'][1]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{base}{'' if lang == 'en' else 'pt-br/'}">
<link rel="alternate" hreflang="en" href="{base}">
<link rel="alternate" hreflang="pt-BR" href="{base}pt-br/">
<link rel="alternate" hreflang="x-default" href="{base}">
{LANG_SCRIPT}{THEME_SCRIPT}<link rel="preload" href="/assets/fonts/iAWriterQuattroS-Regular.woff2" as="font" type="font/woff2" crossorigin>
{FAVICON}<style>{CSS}</style>
</head>
<body>
{states_symbol()}
<header class="wrap top">
  <div class="brand">
    <a class="name mono" href="https://eduardofrafre.com/{sfx}">eduardofrafre.com</a>
    <a class="mono crumb" href="{lab}">/ lab</a>
    <span class="mono here">/ {t['crumb']}</span>
  </div>
  <nav class="mono" aria-label="{t['nav_label']}">
    <span class="out">{out}</span>
{sections}
    <span class="lang">{langs}</span>
{TOGGLE.format(label=t['theme'])}
</header>
<main>
  <div class="open">
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

  <section class="section" id="candidates" aria-labelledby="cands-h">
    <div class="wrap head">
      <span class="k mono">{t['cands_k']}</span>
      <div><h2 id="cands-h">{t['cands_h']}</h2><p>{t['cands_p']}</p></div>
    </div>
    {''.join(entries)}
  </section>

  <section class="section" id="limits" aria-labelledby="limits-h">
    <div class="wrap head"><span class="k mono">{t['limits_k']}</span><h2 id="limits-h">{t['limits_h']}</h2></div>
    <div class="wrap body">
      <ul class="limits">{limits}</ul>
    </div>
  </section>

  <section class="section" aria-labelledby="misid-h">
    <div class="wrap head"><span class="k mono">{t['misid_h']}</span><div><h2 id="misid-h">{t['misid_h']}</h2><p>{t['misid_p']}</p></div></div>
    <div class="wrap body">
      <details class="misid-fold mono"><summary>{t['misid_fold']}</summary><ul class="misid mono">{''.join(misid_items)}</ul></details>
      <div class="wanted mono">
        <div class="catno"><b>{t['wanted_b']}</b><span>{t['wanted_s']}</span></div>
        <p>{t['wanted_p']}</p>
        <div class="links"><a class="ln" href="mailto:{t['mail']}?subject=Hidden%20Lineages">{t['wanted_mail']}</a></div>
      </div>
      <p class="source mono">{t['data'].format(downloaded=downloaded, today=date.today().isoformat())}</p>
    </div>
  </section>

</main>
<footer class="ft">
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
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: https://hidden-lineages.lab.eduardofrafre.com/sitemap.xml\n")
    print(f"wrote site/: {counts}, {len(all_sites)} sites, {len(insects['kept'])} insect candidates")

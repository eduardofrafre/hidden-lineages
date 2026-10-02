"""Ungapped alignment of COI barcodes from one species or genus.

COI is protein-coding and barcodes from close relatives almost never carry indels,
so each sequence only needs an offset against a reference: found by voting on
shared 12-mers, then cut to the reference window and padded with gaps. Sequences
with an internal gap in BOLD, or that place on fewer than MIN_VOTES 12-mers,
are dropped and reported rather than forced in.
"""
from collections import Counter

K = 12
MIN_VOTES = 20


def clean(seq):
    return "".join(c if c in "ACGT" else "N" for c in seq.strip("-").upper())


def align(records):
    """records: {id: raw BOLD sequence}. Returns ({id: aligned}, {id: reason dropped})."""
    seqs, dropped = {}, {}
    for rid, raw in records.items():
        if "-" in raw.strip("-"):
            dropped[rid] = "internal gap"
        else:
            seqs[rid] = clean(raw)
    if not seqs:
        return {}, dropped
    lengths = Counter(len(s) for s in seqs.values())
    ref_len = 658 if 658 in lengths else max(lengths)
    ref = next(s for s in seqs.values() if len(s) == ref_len)
    index = {}
    for i in range(len(ref) - K + 1):
        index.setdefault(ref[i:i + K], i)

    out = {}
    for rid, s in seqs.items():
        votes = Counter(index[s[j:j + K]] - j for j in range(len(s) - K + 1) if s[j:j + K] in index)
        if not votes or votes.most_common(1)[0][1] < MIN_VOTES:
            dropped[rid] = "no placement"
            continue
        off = votes.most_common(1)[0][0]
        row = ["-"] * len(ref)
        for j, c in enumerate(s):
            if 0 <= off + j < len(ref):
                row[off + j] = c
        out[rid] = "".join(row)
    return out, dropped


def p_distance(a, b):
    """Share of differing sites among sites where both sequences have A, C, G or T."""
    pairs = [(x, y) for x, y in zip(a, b) if x in "ACGT" and y in "ACGT"]
    return sum(x != y for x, y in pairs) / len(pairs) if len(pairs) >= 300 else None

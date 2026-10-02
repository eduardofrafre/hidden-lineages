"""Where a split species' BINs were collected, relative to each other.

Records are grouped into sites by rounding coordinates to 0.1 degree (about 11 km), so
specimens from one collecting trip count once. For the two largest BINs of a species:
- "together": they share a site, and at least one BIN is also known from elsewhere;
- "one shared site": everything from a single site, so one sample says both exist;
- "apart": no shared site, and each BIN is known from 2 or more sites;
- "too few sites": no shared site, but a BIN is known from one site only.
The distance reported is between the closest sites of the two BINs.

Neither pattern is a verdict. Lineages apart can be one species with geographic
structure; lineages together with no intermediates point at separate species, or at
contamination. The pattern is shown next to the candidate, not used to rank it.
"""
from math import asin, cos, radians, sin, sqrt


def site(coord):
    return round(coord[0], 1), round(coord[1], 1)


def km(a, b):
    (la1, lo1), (la2, lo2) = (map(radians, a), map(radians, b))
    h = sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def pattern(coords_a, coords_b):
    """coords_*: (lat, lon) of each record in the two BINs. Returns (label, sites a, sites b, km apart)."""
    a, b = {site(c) for c in coords_a}, {site(c) for c in coords_b}
    closest = min(km(x, y) for x in a for y in b)
    if a & b:
        label = "together" if max(len(a), len(b)) >= 2 else "one shared site"
    elif len(a) >= 2 and len(b) >= 2:
        label = "apart"
    else:
        label = "too few sites"
    return label, len(a), len(b), closest

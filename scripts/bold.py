"""Download public BOLD v5 records and select the southern Atlantic Forest ones."""
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://portal.boldsystems.org/api"
DATA = Path(__file__).resolve().parent.parent / "data"
SOUTH = {"Parana", "Santa Catarina", "Rio Grande do Sul"}

csv.field_size_limit(sys.maxsize)


def _get(url):
    with urllib.request.urlopen(url, timeout=600) as r:
        return r.read()


def download(query, name):
    """Save every public record matching a BOLD query as data/<name>.tsv."""
    out = DATA / f"{name}.tsv"
    if out.exists():
        return out
    qid = json.loads(_get(f"{API}/query?query={urllib.parse.quote(query)}&extent=full"))["query_id"]
    DATA.mkdir(exist_ok=True)
    out.write_bytes(_get(f"{API}/documents/{qid}/download?format=tsv"))
    return out


def coord(row):
    nums = re.findall(r"-?\d+\.?\d*", row["coord"])
    return (float(nums[0]), float(nums[1])) if len(nums) == 2 else None


def south_records(path):
    """Rows from PR, SC or RS: by state label, or by coordinates when the label is empty.

    Most Brazilian records carry no state, so the coordinate box is needed. It stops
    at 24.7 S to keep São Paulo out, which also drops unlabelled records from northern Paraná.
    """
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            c = coord(row)
            state = row["province/state"]
            if state in SOUTH or (not state and c and c[0] <= -24.7 and -57.7 <= c[1] <= -48.0):
                row["_coord"] = c
                yield row


INTERIM = re.compile(r"^([A-Z][a-z]+ [a-z][a-z-]+) sp\. \S+$")


def barcodes(path):
    """COI-5P rows with a real species name, a BIN and coordinates.

    An interim name such as `Cosmosoma auge sp. MMZ01` marks a provisional lineage
    of `Cosmosoma auge` and is read as that species; `Genus sp. X` stays out.
    """
    for row in south_records(path):
        m = INTERIM.match(row["species"])
        if m:
            row["species"] = m.group(1)
        sp = row["species"]
        if (row["marker_code"] == "COI-5P" and sp and row["bin_uri"] and row["_coord"]
                and " sp." not in sp and " cf." not in sp and " aff." not in sp):
            yield row

"""Protein sequences from NCBI (GenBank, RefSeq), for what UniProt lacks: the publication's
strain, whose sequence gives the mappings (`docs/curation-rules.md` §3, mappings).

uv run drakkar-genbank search <query>... [--limit <n>] [--offset <n>] [--all]
    the NCBI protein records of each query (NCBI search syntax, e.g. `JFH-1 AND polyprotein`):
    accession, title, length, taxon
uv run drakkar-genbank seq <accession>[:<start>-<stop>]...
    a protein record: its accession and version, title, length and sequence, or the subsequence
    between those coordinates (1-based, inclusive); a nucleotide record (a genome): its coding
    sequences, one line each, with the protein accession that `seq` reads

Read-only, no database. One request at a time, at the pace NCBI allows (`NCBI_API_KEY` in the
project's `.env` raises it).
"""

import argparse
import json
import os
import re
import time
from typing import Any, cast
from urllib.parse import urlencode

from dotenv import load_dotenv

from drakkar.fetch import EFETCH, Get, http_get
from drakkar.read import DEFAULT, LIMIT, Page

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH = f"{EUTILS}/esearch.fcgi"
ESUMMARY = f"{EUTILS}/esummary.fcgi"
LOCATION = re.compile(r"([A-Za-z0-9_.]+?)(?::(\d+)-(\d+))?")  # BAB32872.1:1-191
COLUMNS = "#input\taccession\ttitle\tlength\tsequence"
TITLE = 120  # characters shown of a title: those of Swiss-Prot records list every name


def _title(text: str) -> str:
    return text if len(text) <= TITLE else f"{text[:TITLE]}…"


class Eutils:
    """Requests to the NCBI E-utilities, spaced as NCBI asks: 3 per second, 10 with a key."""

    def __init__(self, get: Get = http_get, pause: float | None = None) -> None:
        load_dotenv()
        self.get = get
        self.key = os.environ.get("NCBI_API_KEY")
        self.pause = (0.11 if self.key else 0.34) if pause is None else pause
        self.last = 0.0

    def __call__(self, url: str, **params: Any) -> tuple[int, str]:
        wait = self.last + self.pause - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        params = {**params, "tool": "drakkar", **({"api_key": self.key} if self.key else {})}
        r = self.get(f"{url}?{urlencode(params)}")
        self.last = time.monotonic()
        return r.status, r.body.decode(errors="replace")


def _fasta(text: str) -> list[tuple[str, str]]:
    """(header, sequence) of each record of a FASTA text."""
    records: list[tuple[str, str]] = []
    for block in text.split(">")[1:]:
        header, _, body = block.partition("\n")
        records.append((header.strip(), "".join(body.split())))
    return records


def _cds(header: str) -> tuple[str, str]:
    """(protein accession, title) of a coding sequence of `fasta_cds_aa`, whose header is
    `lcl|AB047639.1_prot_BAB32872.1_1 [gene=…] [protein=…] [protein_id=…] [location=…]`."""
    fields = dict(re.findall(r"\[(\w+)=([^\]]*)\]", header))
    title = " ".join(
        part
        for part in (
            f"CDS {fields.get('location', '?')}:",
            fields.get("protein", ""),
            f"(gene {fields['gene']})" if "gene" in fields else "",
        )
        if part
    )
    return fields.get("protein_id", "-"), title


def seq(eutils: Eutils, locations: list[str]) -> str:
    """The sequence of each protein record, or between its coordinates; the coding sequences of
    each nucleotide record."""
    lines = [COLUMNS]
    for text in locations:
        match = LOCATION.fullmatch(text)
        if match is None:
            lines.append(f"{text}\tnot <accession>[:<start>-<stop>]")
            continue
        accession, start, stop = match.groups()
        status, body = eutils(EFETCH, db="protein", id=accession, rettype="fasta", retmode="text")
        records = _fasta(body) if status == 200 else []
        if records:
            header, sequence = records[0]
            found, _, title = header.partition(" ")
            if start is not None and stop is not None:
                first, last = int(start), int(stop)
                if not 1 <= first <= last <= len(sequence):
                    lines.append(f"{text}\t{first}-{last} is outside 1-{len(sequence)}")
                    continue
                sequence = sequence[first - 1 : last]
            lines.append(f"{text}\t{found}\t{_title(title)}\t{len(sequence)}\t{sequence}")
            continue
        status, body = eutils(
            EFETCH, db="nuccore", id=accession, rettype="fasta_cds_aa", retmode="text"
        )
        coding = _fasta(body) if status == 200 else []
        if not coding:
            lines.append(f"{text}\tno protein or nucleotide record at NCBI")
        elif start is not None:
            lines.append(f"{text}\ta nucleotide record: coordinates are read on a protein")
        else:
            for header, sequence in coding:
                protein, title = _cds(header)
                lines.append(f"{text}\t{protein}\t{title}\t{len(sequence)}\t-")
    return "\n".join(lines)


def search(eutils: Eutils, queries: list[str], page: Page = DEFAULT) -> str:
    """The NCBI protein records of each query, in NCBI's order: a page of them, and how many."""
    lines = ["#query\taccession\ttitle\tlength\ttaxon"]
    for query in queries:
        retmax = 10_000 if page.limit is None else page.limit
        status, body = eutils(
            ESEARCH, db="protein", term=query, retstart=page.offset, retmax=retmax, retmode="json"
        )
        if status != 200:
            lines.append(f"{query}\tNCBI search failed (HTTP {status})")
            continue
        result = cast(dict[str, Any], json.loads(body)["esearchresult"])
        ids = cast(list[str], result.get("idlist", []))
        total = int(result.get("count", 0))
        rows: list[str] = []
        if ids:
            status, body = eutils(ESUMMARY, db="protein", id=",".join(ids), retmode="json")
            summaries = cast(dict[str, Any], json.loads(body)["result"]) if status == 200 else {}
            for uid in ids:
                s = cast(dict[str, Any], summaries.get(uid, {}))
                rows.append(
                    f"{s.get('accessionversion', uid)}\t{_title(s.get('title', '?'))}\t"
                    f"{s.get('slen', '?')}\t{s.get('taxid', '?')}"
                )
        lines += page.lines(query, rows, "a closer query (NCBI search syntax)", total)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Protein sequences from NCBI.")
    commands = parser.add_subparsers(dest="command", required=True)
    s = commands.add_parser("search", help="the NCBI protein records of each query")
    s.add_argument("queries", nargs="+")
    s.add_argument("--limit", type=int, default=LIMIT, help=f"records per query ({LIMIT})")
    s.add_argument("--offset", type=int, default=0, help="records skipped per query")
    s.add_argument("--all", action="store_true", help="every record")
    q = commands.add_parser("seq", help="protein sequences, or a genome's coding sequences")
    q.add_argument("locations", nargs="+", help="<accession>[:<start>-<stop>]")
    args = parser.parse_args()
    eutils = Eutils()
    if args.command == "search":
        print(search(eutils, args.queries, Page(args.offset, None if args.all else args.limit)))
    else:
        print(seq(eutils, args.locations))

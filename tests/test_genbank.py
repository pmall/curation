"""The GenBank tool, on NCBI answers recorded here (no network)."""

import json
from urllib.parse import parse_qs, urlparse

from drakkar.fetch import EFETCH, Response
from drakkar.genbank import ESEARCH, ESUMMARY, Eutils, search, seq
from drakkar.read import Page

POLYPROTEIN = "MSTNPKPQRKTKRNTNRRPEDVKFPGGGQIVGGVYLLPRRGPRLGVRTTRKTSERSQPRGRRQPIPKDRR"
FASTA = (
    f">BAB32872.1 polyprotein [Hepatitis C virus JFH-1]\n{POLYPROTEIN[:40]}\n{POLYPROTEIN[40:]}\n"
)
CDS = (
    ">lcl|AB047639.1_prot_BAB32872.1_1 [protein=polyprotein] [protein_id=BAB32872.1] "
    f"[location=341..9442] [gbkey=CDS]\n{POLYPROTEIN}\n"
    ">lcl|AB047639.1_prot_BAB32873.1_2 [gene=F] [protein=F protein] [protein_id=BAB32873.1] "
    "[location=355..804] [gbkey=CDS]\nMSTNPK\n"
)


def ok(text: str) -> Response:
    return Response("", 200, "text/plain", text.encode())


def ncbi(url: str) -> Response:
    """NCBI as recorded: BAB32872 a protein, AB047639 a genome, anything else unknown."""
    base = url.split("?")[0]
    query = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
    assert query["tool"] == "drakkar"
    if base == EFETCH and query["db"] == "protein" and query["id"] == "BAB32872":
        return ok(FASTA)
    if base == EFETCH and query["db"] == "nuccore" and query["id"] == "AB047639":
        return ok(CDS)
    if base == ESEARCH:
        ids = ["13122262", "13122263", "13122264"][: int(query["retmax"])]
        return ok(json.dumps({"esearchresult": {"count": "3", "idlist": ids}}))
    if base == ESUMMARY:
        result = {
            uid: {"accessionversion": f"BAB3287{i}.1", "title": "x" * 300, "slen": 3033, "taxid": 1}
            for i, uid in enumerate(query["id"].split(","))
        }
        return ok(json.dumps({"result": result}))
    return Response(url, 400, "", b"Error")


def test_seq():
    """A protein whole or between coordinates; a genome's coding sequences; an unknown record."""
    eutils = Eutils(ncbi, pause=0)
    lines = seq(eutils, ["BAB32872:1-15", "BAB32872", "AB047639", "XX1", "BAB32872:1-999"])
    assert lines.splitlines() == [
        "#location\taccession\ttitle\tlength\tsequence",
        "BAB32872:1-15\tBAB32872.1\tpolyprotein [Hepatitis C virus JFH-1]\t15\tMSTNPKPQRKTKRNT",
        f"BAB32872\tBAB32872.1\tpolyprotein [Hepatitis C virus JFH-1]\t70\t{POLYPROTEIN}",
        "AB047639\tBAB32872.1\tCDS 341..9442: polyprotein\t70\t-",
        "AB047639\tBAB32873.1\tCDS 355..804: F protein (gene F)\t6\t-",
        "XX1\tno protein or nucleotide record at NCBI",
        "BAB32872:1-999\t1-999 is outside 1-70",
    ]


def test_search_is_paged():
    eutils = Eutils(ncbi, pause=0)
    lines = search(eutils, ["JFH-1"], Page(limit=2)).splitlines()
    assert lines[1].startswith("JFH-1\tBAB32870.1\t" + "x" * 120 + "…\t3033\t1")
    assert lines[-1] == "JFH-1\t… 2 of 3"

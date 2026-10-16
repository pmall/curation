"""The sources of drakkar-fetch and its manifest, the downloads simulated (no network)."""

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from drakkar.fetch import (
    CROSSREF,
    EFETCH,
    EUROPE_PMC,
    OPENALEX,
    PMC_AWS,
    UNPAYWALL,
    Response,
    fetch,
    pmcids,
)

PMID = 123
SEARCH = f"{EUROPE_PMC}/search?query=EXT_ID%3A{PMID}%20AND%20SRC%3AMED&format=json&resultType=core"
WORK = f"{OPENALEX}/pmid:{PMID}"
XML = (
    b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><body><p>Text</p>'
    b'<supplementary-material xlink:href="s1.xlsx"/>'
    b'<supplementary-material xlink:href="movie_s1.mp4"/>'
    b'<supplementary-material xlink:href="fig_s1.tif"/></body></article>'
)
PARAGRAPHS = "<p>NS1 binds TRIM25 in cells.</p>" * 500
SUPPLEMENT = '<a href="/doi/suppl/mmc1.xlsx">Supplementary Table 1</a>'
ARTICLE = f"<html><body><article>{PARAGRAPHS}</article>{SUPPLEMENT}</body></html>".encode()
LANDING = b"<html><body><article><p>Abstract only.</p></article></body></html>"


def ok(body: bytes, content_type: str = "application/octet-stream", url: str = "") -> Response:
    return Response(url, 200, content_type, body)


def json_ok(data: Any) -> Response:
    return ok(json.dumps(data).encode(), "application/json")


@pytest.fixture(autouse=True)
def no_address(monkeypatch: pytest.MonkeyPatch):
    """No address configured, unless a test sets one: Unpaywall must then not be asked."""
    monkeypatch.setattr("drakkar.fetch.load_dotenv", lambda: None)
    monkeypatch.delenv("UNPAYWALL_EMAIL", raising=False)


def getter(responses: dict[str, Response], asked: list[str]):
    def get(url: str, headers: dict[str, str] | None = None) -> Response:
        asked.append(url)
        r = responses.get(url, Response(url, 404, "", b""))
        return Response(r.url or url, r.status, r.content_type, r.body)

    return get


def run(tmp_path: Path, responses: dict[str, Response]) -> tuple[dict[str, Any], list[str]]:
    asked: list[str] = []
    manifest = fetch(PMID, tmp_path, getter(responses, asked))
    assert json.loads((tmp_path / f"{PMID}.json").read_text()) == manifest
    return manifest, asked


def location(url: str, pdf: str | None = None, name: str = "J Virol") -> dict[str, Any]:
    return {
        "is_oa": True,
        "landing_page_url": url,
        "pdf_url": pdf,
        "license": "cc-by",
        "source": {"display_name": name},
    }


def test_pmc_open_access_files(tmp_path: Path):
    listing = (
        "<ListBucketResult><Key>PMC9.1/PMC9.1.xml</Key><Key>PMC9.2/PMC9.2.xml</Key>"
        "<Key>PMC9.2/PMC9.2.pdf</Key><Key>PMC9.2/s1.xlsx</Key><Key>PMC9.2/movie_s1.mp4</Key>"
        "<Key>PMC9.2/fig_s1.tif</Key>"
        "</ListBucketResult>"
    )
    manifest, asked = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"pmcid": "PMC9", "license": "cc by"}]}}),
            WORK: json_ok({"ids": {}}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": ok(listing.encode()),
            f"{PMC_AWS}/PMC9.2/PMC9.2.xml": ok(XML),
            f"{PMC_AWS}/PMC9.2/PMC9.2.pdf": ok(b"%PDF-1.7"),
            f"{PMC_AWS}/PMC9.2/s1.xlsx": ok(b"cells"),
        },
    )
    assert manifest["line"] == "Full text: PMC9 (cc by)"
    assert (manifest["file"], manifest["pdf"]) == (f"{PMID}.xml", f"{PMID}.pdf")
    assert (tmp_path / f"{PMID}.xml").read_bytes() == XML
    assert manifest["supplements"] == [
        {"file": f"{PMID}.supp/s1.xlsx", "url": f"{PMC_AWS}/PMC9.2/s1.xlsx"}
    ]
    assert [s["why"] for s in manifest["skipped_supplements"]] == ["video", "image"]
    assert f"{PMC_AWS}/PMC9.2/movie_s1.mp4" not in asked
    assert f"{PMC_AWS}/PMC9.2/fig_s1.tif" not in asked


def test_supplement_archive_is_unpacked(tmp_path: Path):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("tables/s1.xlsx", "cells")
        z.writestr("__MACOSX/._s1.xlsx", "junk")
        z.writestr("video_s2.mov", "frames")
    listing = (
        "<ListBucketResult><Key>PMC9.1/PMC9.1.xml</Key><Key>PMC9.1/s.zip</Key></ListBucketResult>"
    )
    xml = XML.replace(b"s1.xlsx", b"s.zip").replace(b"movie_s1.mp4", b"s.zip")
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"pmcid": "PMC9"}]}}),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": ok(listing.encode()),
            f"{PMC_AWS}/PMC9.1/PMC9.1.xml": ok(xml),
            f"{PMC_AWS}/PMC9.1/s.zip": ok(archive.getvalue()),
        },
    )
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/s1.xlsx"]
    assert (tmp_path / f"{PMID}.supp" / "s1.xlsx").read_text() == "cells"
    assert [s["why"] for s in manifest["skipped_supplements"]] == ["video", "image"]


def test_pmc_xml_from_europe_pmc_when_not_in_the_open_access_files(tmp_path: Path):
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"pmcid": "PMC9"}]}}),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": ok(b"<ListBucketResult/>"),
            f"{EUROPE_PMC}/PMC9/fullTextXML": ok(XML),
        },
    )
    assert manifest["line"] == (
        "Full text: PMC9 (no license given), supplementary files not offered by this source"
    )
    assert manifest["file"] == f"{PMID}.xml" and "pdf" not in manifest
    assert manifest["supplements_offered"] is False


def test_pmcid_known_only_to_openalex():
    work = {
        "ids": {"pmcid": "https://www.ncbi.nlm.nih.gov/pmc/articles/111"},
        "locations": [
            location("https://pmc.ncbi.nlm.nih.gov/articles/PMC222/"),
            location("https://doi.org/10.1/x"),
        ],
    }
    assert pmcids({}, work) == ["PMC111", "PMC222"]
    assert pmcids({"pmcid": "PMC111"}, work) == ["PMC111", "PMC222"]


def test_publisher_html_with_supplements(tmp_path: Path):
    doi = "https://doi.org/10.1/x"
    manifest, _ = run(
        tmp_path,
        {
            WORK: json_ok(
                {"doi": doi, "best_oa_location": location(doi), "locations": [location(doi)]}
            ),
            doi: ok(ARTICLE, "text/html", url="https://journal.org/article/x"),
            "https://journal.org/doi/suppl/mmc1.xlsx": ok(b"cells"),
        },
    )
    assert manifest["line"] == f"Full text: J Virol (cc-by, {doi})"
    assert manifest["file"] == f"{PMID}.html"
    assert manifest["supplements"][0]["file"] == f"{PMID}.supp/mmc1.xlsx"


def test_supplement_known_as_an_image_only_once_downloaded(tmp_path: Path):
    doi = "https://doi.org/10.1/x"
    links = (
        '<a href="/file?type=supplementary&id=s1">Supplementary Table S1</a>'
        '<a href="/file?type=supplementary&id=s2">Supplementary Figure S2</a>'
    )
    page = ARTICLE.replace(SUPPLEMENT.encode(), links.encode())
    manifest, _ = run(
        tmp_path,
        {
            WORK: json_ok({"doi": doi, "locations": [location(doi)]}),
            doi: ok(page, "text/html", url="https://journal.org/article/x"),
            "https://journal.org/file?type=supplementary&id=s1": ok(b"cells", "application/msword"),
            "https://journal.org/file?type=supplementary&id=s2": ok(b"II*", "image/tiff"),
        },
    )
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/s1.doc"]
    assert [s["why"] for s in manifest["skipped_supplements"]] == ["image"]
    assert not (tmp_path / f"{PMID}.supp" / "s2.tif").exists()


def test_publisher_landing_page_then_pdf(tmp_path: Path):
    """A landing page is no full text: the publisher's PDF is tried next. A preprint is never
    asked, even as OpenAlex's best copy; nor the PMC website, whose copies come from PMC's
    files."""
    doi = "https://doi.org/10.1/x"
    preprint = location("https://doi.org/10.1101/y", "https://biorxiv.org/y.pdf", "bioRxiv")
    publisher = location(doi, "https://journal.org/x.pdf")
    pmc = location("https://pmc.ncbi.nlm.nih.gov/articles/PMC5/")
    manifest, asked = run(
        tmp_path,
        {
            WORK: json_ok(
                {"doi": doi, "best_oa_location": preprint, "locations": [preprint, publisher, pmc]}
            ),
            doi: ok(LANDING, "text/html"),
            "https://doi.org/10.1101/y": ok(LANDING, "text/html"),
            "https://journal.org/x.pdf": ok(b"%PDF-1.7", "application/pdf"),
            "https://biorxiv.org/y.pdf": ok(b"%PDF-1.7", "application/pdf"),
        },
    )
    assert manifest["line"] == "Full text: J Virol (cc-by, https://journal.org/x.pdf)"
    assert manifest["file"] == f"{PMID}.pdf"
    assert "https://doi.org/10.1101/y" not in asked
    assert "https://biorxiv.org/y.pdf" not in asked
    assert not any("pmc.ncbi" in url for url in asked)
    assert f"{PMC_AWS}/?list-type=2&prefix=PMC5." in asked
    outcomes = {t["url"]: t["outcome"] for t in manifest["tried"]}
    assert outcomes[doi] == "HTTP 200, 2 words: not a full text"


def test_preprint_is_never_fetched(tmp_path: Path):
    preprint = location("https://doi.org/10.1101/y", "https://www.biorxiv.org/y.pdf", "bioRxiv")
    manifest, asked = run(tmp_path, {WORK: json_ok({"locations": [preprint]})})
    assert manifest["line"] == "Full text: closed — open access only as a preprint"
    assert not any("10.1101" in url or "biorxiv" in url for url in asked)


def test_closed(tmp_path: Path):
    manifest, _ = run(
        tmp_path, {WORK: json_ok({"locations": [{"is_oa": False, "landing_page_url": "x"}]})}
    )
    assert manifest["file"] is None
    assert manifest["line"] == "Full text: closed — not open access anywhere"


def test_blocked(tmp_path: Path):
    doi = "https://doi.org/10.1/x"
    manifest, _ = run(
        tmp_path,
        {
            WORK: json_ok({"doi": doi, "locations": [location(doi)]}),
            doi: Response(doi, 403, "", b""),
        },
    )
    assert manifest["line"] == f"Full text: closed — a copy at {doi} but download blocked"


def test_open_access_without_a_copy_to_download(tmp_path: Path):
    manifest, _ = run(tmp_path, {WORK: json_ok({"locations": [{"is_oa": True}]})})
    assert manifest["line"] == "Full text: closed — open access, but no copy to download"


def test_error_page_sent_as_success(tmp_path: Path):
    manifest, _ = run(tmp_path, {SEARCH: ok(b"<html>Service unavailable</html>", "text/html")})
    assert manifest["line"] == (
        "Full text: closed — not in OpenAlex, and no copy from Unpaywall or Crossref"
    )


def test_pmc_xml_from_efetch_when_europe_pmc_has_none(tmp_path: Path):
    """A PMC copy outside the open access files, which Europe PMC does not serve: `efetch`
    gives the body, and the supplementary files are asked for on their own."""
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("s1.xlsx", "cells")
    manifest, asked = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"pmcid": "PMC9", "license": "cc by"}]}}),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": ok(b"<ListBucketResult/>"),
            f"{EUROPE_PMC}/PMC9/fullTextXML": Response("", 500, "", b""),
            f"{EFETCH}?db=pmc&id=PMC9&rettype=xml": ok(XML),
            f"{EUROPE_PMC}/PMC9/supplementaryFiles": ok(archive.getvalue(), "application/zip"),
        },
    )
    assert manifest["line"] == "Full text: PMC9 (cc by)"
    assert manifest["file"] == f"{PMID}.xml"
    assert manifest["supplements_offered"] is True
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/s1.xlsx"]
    assert asked.index(f"{EUROPE_PMC}/PMC9/fullTextXML") < asked.index(
        f"{EFETCH}?db=pmc&id=PMC9&rettype=xml"
    )


def test_efetch_without_a_body_is_no_full_text(tmp_path: Path):
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"pmcid": "PMC9"}]}}),
            WORK: json_ok({"locations": [{"is_oa": False}]}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": ok(b"<ListBucketResult/>"),
            f"{EFETCH}?db=pmc&id=PMC9&rettype=xml": ok(
                b"<pmc-articleset><front/></pmc-articleset>"
            ),
        },
    )
    assert manifest["file"] is None
    assert manifest["line"] == "Full text: closed — not open access anywhere"
    outcomes = {t["url"]: t["outcome"] for t in manifest["tried"]}
    assert outcomes[f"{EFETCH}?db=pmc&id=PMC9&rettype=xml"] == "HTTP 200, no full text"


def test_copy_from_unpaywall_when_an_address_is_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "curator@example.org")
    doi = "10.1/x"
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": doi}]}}),
            WORK: json_ok({}),
            f"{UNPAYWALL}/{doi}?email=curator%40example.org": json_ok(
                {
                    "oa_locations": [
                        {
                            "url_for_landing_page": "https://repo.org/record/1",
                            "url_for_pdf": "https://repo.org/record/1.pdf",
                            "license": "cc-by",
                            "repository_institution": "Repo",
                        }
                    ]
                }
            ),
            "https://repo.org/record/1": ok(ARTICLE, "text/html", url="https://repo.org/record/1"),
        },
    )
    assert manifest["line"] == "Full text: Repo (cc-by, https://repo.org/record/1)"
    assert manifest["file"] == f"{PMID}.html"


def test_unpaywall_is_not_asked_without_an_address(tmp_path: Path):
    manifest, asked = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": "10.1/x"}]}}),
            WORK: json_ok({"locations": [{"is_oa": True}]}),
        },
    )
    assert not any(url.startswith(UNPAYWALL) for url in asked)
    assert any(url.startswith(CROSSREF) for url in asked)
    assert manifest["line"] == "Full text: closed — open access, but no copy to download"


def test_copy_from_the_crossref_text_mining_link(tmp_path: Path):
    doi = "10.1/x"
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": doi}]}}),
            WORK: json_ok({}),
            f"{CROSSREF}/{doi}": json_ok(
                {
                    "message": {
                        "link": [
                            {"URL": "https://journal.org/x.html", "content-type": "text/html"},
                            {
                                "URL": "https://journal.org/x.pdf",
                                "content-type": "application/pdf",
                                "intended-application": "text-mining",
                            },
                        ]
                    }
                }
            ),
            "https://journal.org/x.pdf": ok(b"%PDF-1.7", "application/pdf"),
        },
    )
    assert manifest["file"] == f"{PMID}.pdf"
    assert manifest["source"] == "the publisher (Crossref)"

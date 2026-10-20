"""The routes of drakkar-fetch, its manifest and `--supplement`, the downloads simulated (no
network). The pages in `samples/fetch/` are real responses cut to what the routes read."""

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from drakkar.fetch import (
    EFETCH,
    EUROPE_PMC,
    OPENALEX,
    PMC_AWS,
    PMC_PAGE,
    UNPAYWALL,
    Response,
    fetch,
    fetch_supplements,
    pmcids,
)

SAMPLES = Path(__file__).parent / "samples" / "fetch"
PMID = 123
SEARCH = f"{EUROPE_PMC}/search?query=EXT_ID%3A{PMID}%20AND%20SRC%3AMED&format=json&resultType=core"
WORK = f"{OPENALEX}/pmid:{PMID}"
XML = (
    b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><body><p>Text</p>'
    b'<supplementary-material xlink:href="s1.xlsx"><caption><p>Hits</p></caption>'
    b"</supplementary-material>"
    b'<supplementary-material xlink:href="movie_s1.mp4"/>'
    b'<supplementary-material xlink:href="fig_s1.tif"/>'
    b'<supplementary-material><media xlink:href="s2.pdf"><caption><p>Reporting Summary</p>'
    b"</caption></media></supplementary-material></body></article>"
)
DOI = "10.1/x"
PUBLISHER = f"https://doi.org/{DOI}"


def ok(body: bytes, content_type: str = "application/octet-stream", url: str = "") -> Response:
    return Response(url, 200, content_type, body)


def json_ok(data: Any) -> Response:
    return ok(json.dumps(data).encode(), "application/json")


def page(name: str, url: str = "") -> Response:
    return ok((SAMPLES / name).read_bytes(), "text/html", url)


def listing(*keys: str) -> Response:
    return ok(
        (
            "<ListBucketResult>" + "".join(f"<Key>{k}</Key>" for k in keys) + "</ListBucketResult>"
        ).encode()
    )


def found(pmcid: str = "PMC9", **record: Any) -> Response:
    return json_ok({"resultList": {"result": [{"pmcid": pmcid, **record}]}})


@pytest.fixture(autouse=True)
def no_configuration(monkeypatch: pytest.MonkeyPatch):
    """No address configured, unless a test sets one: Unpaywall must then not be asked."""
    monkeypatch.setattr("drakkar.fetch.load_dotenv", lambda: None)
    monkeypatch.delenv("UNPAYWALL_EMAIL", raising=False)


class Server:
    """The responses by URL, and every request made."""

    def __init__(self, responses: dict[str, Response]) -> None:
        self.responses = responses
        self.asked: list[str] = []

    def __call__(self, url: str) -> Response:
        self.asked.append(url)
        r = self.responses.get(url, Response(url, 404, "", b""))
        return Response(r.url or url, r.status, r.content_type, r.body)


def run(tmp_path: Path, responses: dict[str, Response]) -> tuple[dict[str, Any], Server]:
    server = Server(responses)
    manifest = fetch(PMID, tmp_path, server)
    assert json.loads((tmp_path / f"{PMID}.json").read_text()) == manifest
    return manifest, server


def location(url: str, pdf: str | None = None, name: str = "J Virol") -> dict[str, Any]:
    return {
        "is_oa": True,
        "landing_page_url": url,
        "pdf_url": pdf,
        "license": "cc-by",
        "source": {"display_name": name},
    }


def outcomes(manifest: dict[str, Any]) -> dict[str, str]:
    return {t["url"]: t["outcome"] for t in manifest["tried"]}


# Step 2: the article


def test_pmc_open_access_files(tmp_path: Path):
    """The article and its PDF; videos, images and the Reporting Summary skipped, never asked."""
    manifest, server = run(
        tmp_path,
        {
            SEARCH: found(license="cc by"),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": listing(
                "PMC9.1/PMC9.1.xml",
                "PMC9.2/PMC9.2.xml",
                "PMC9.2/PMC9.2.pdf",
                "PMC9.2/s1.xlsx",
                "PMC9.2/movie_s1.mp4",
                "PMC9.2/fig_s1.tif",
                "PMC9.2/s2.pdf",
            ),  # fmt: skip
            f"{PMC_AWS}/PMC9.2/PMC9.2.xml": ok(XML),
            f"{PMC_AWS}/PMC9.2/PMC9.2.pdf": ok(b"%PDF-1.7"),
            f"{PMC_AWS}/PMC9.2/s1.xlsx": ok(b"cells"),
        },
    )
    assert manifest["line"] == "Full text: PMC9 (cc by)"
    assert manifest["missing_supplements"] == []
    assert (manifest["file"], manifest["pdf"]) == (f"{PMID}.xml", f"{PMID}.pdf")
    assert manifest["supplements"] == [
        {"name": "s1.xlsx", "file": f"{PMID}.supp/s1.xlsx", "url": f"{PMC_AWS}/PMC9.2/s1.xlsx"}
    ]
    assert [s["why"] for s in manifest["skipped_supplements"]] == [
        "video",
        "image",
        "reporting summary",
    ]
    assert not any(u.endswith(("movie_s1.mp4", "fig_s1.tif", "s2.pdf")) for u in server.asked)
    assert not any(PUBLISHER in u for u in server.asked)  # nothing missing: no other route


def test_supplement_archive_is_unpacked(tmp_path: Path):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("tables/s1.xlsx", "cells")
        z.writestr("__MACOSX/._s1.xlsx", "junk")
        z.writestr("video_s2.mov", "frames")
    xml = (
        b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><body>'
        b'<supplementary-material xlink:href="s.zip"/></body></article>'
    )
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: found(),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": listing("PMC9.1/PMC9.1.xml", "PMC9.1/s.zip"),
            f"{PMC_AWS}/PMC9.1/PMC9.1.xml": ok(xml),
            f"{PMC_AWS}/PMC9.1/s.zip": ok(archive.getvalue()),
        },
    )
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/s1.xlsx"]
    assert (tmp_path / f"{PMID}.supp" / "s1.xlsx").read_text() == "cells"
    assert [s["why"] for s in manifest["skipped_supplements"]] == ["video"]
    assert manifest["missing_supplements"] == []


def test_europe_pmc_xml_and_its_supplementary_files_service(tmp_path: Path):
    """Outside the open access files: the XML from Europe PMC, the files from its archive, asked
    once; a file in no route is missing, with every place tried."""
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("s1.xlsx", "cells")
    manifest, server = run(
        tmp_path,
        {
            SEARCH: found(),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": listing(),
            f"{EUROPE_PMC}/PMC9/fullTextXML": ok(
                XML.replace(b"s2.pdf", b"s3.pdf").replace(b"Reporting Summary", b"Table S3")
            ),
            f"{EUROPE_PMC}/PMC9/supplementaryFiles": ok(archive.getvalue(), "application/zip"),
        },
    )
    assert manifest["file"] == f"{PMID}.xml"
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/s1.xlsx"]
    assert (
        manifest["line"]
        == "Full text: PMC9 (no license given), supplementary files missing: s3.pdf"
    )
    [missing] = manifest["missing_supplements"]
    assert missing["name"] == "s3.pdf" and missing["caption"] == "Table S3"
    assert [t["url"] for t in missing["tried"]] == [f"{EUROPE_PMC}/PMC9/supplementaryFiles"]
    assert server.asked.count(f"{EUROPE_PMC}/PMC9/supplementaryFiles") == 1


def test_pmc_page_when_no_xml_has_a_body(tmp_path: Path):
    """`efetch` gives the front matter alone; the PMC article page holds the article. Its
    supplementary file, behind a challenge on PMC's website, is looked for elsewhere."""
    manifest, server = run(
        tmp_path,
        {
            SEARCH: found("PMC10537728", doi=DOI),
            WORK: json_ok({}),
            f"{EFETCH}?db=pmc&id=PMC10537728&rettype=xml": ok(
                b"<pmc-articleset><article><front/></article></pmc-articleset>"
            ),
            f"{PMC_PAGE}/PMC10537728/": page("pmc-page.html"),
            PUBLISHER: Response(PUBLISHER, 403, "", b""),
        },
    )
    assert (manifest["file"], manifest["source"]) == (f"{PMID}.html", "PMC10537728")
    assert manifest["supplements_from"] == "the PMC article page"
    assert outcomes(manifest)[f"{EFETCH}?db=pmc&id=PMC10537728&rettype=xml"] == "HTTP 200, no body"
    [missing] = manifest["missing_supplements"]
    assert missing["name"] == "jvi.00040-23-s0001.pdf"
    assert missing["tried"][-1]["url"] == f"{EUROPE_PMC}/PMC10537728/supplementaryFiles"
    assert not any("/bin/" in u for u in server.asked)
    assert server.asked.count(f"{PMC_PAGE}/PMC10537728/") == 1


def test_pmc_page_without_body_sections_is_no_article(tmp_path: Path):
    abstract_only = (
        b'<html><body><section class="body main-article-body"><section class="abstract">'
        b'<p>Abstract.</p></section><section id="notes1"><p>Note.</p></section></section>'
        b"</body></html>"
    )
    manifest, _ = run(
        tmp_path,
        {SEARCH: found(), WORK: json_ok({}), f"{PMC_PAGE}/PMC9/": ok(abstract_only, "text/html")},
    )
    assert manifest["file"] is None
    assert outcomes(manifest)[f"{PMC_PAGE}/PMC9/"] == "HTTP 200, no body sections"
    assert manifest["free"] is True


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


def test_publisher_page_declaring_free_access(tmp_path: Path):
    url = "https://www.nature.com/articles/s41467-020-19808-4"
    media = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-020-19808-4/MediaObjects/41467_2020_19808_"
    manifest, server = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": DOI}]}}),
            WORK: json_ok(
                {"doi": PUBLISHER, "locations": [location(PUBLISHER, name="Nat Commun")]}
            ),
            PUBLISHER: page("nature-free.html", url),
            f"{media}MOESM1_ESM.pdf": ok(b"%PDF-1.7", "application/pdf"),
            f"{media}MOESM2_ESM.pdf": ok(b"%PDF-1.7", "application/pdf"),
            f"{media}MOESM4_ESM.xlsx": ok(b"cells"),
        },
    )
    assert manifest["file"] == f"{PMID}.html"
    assert manifest["line"] == f"Full text: Nat Commun (cc-by, {url})"
    assert outcomes(manifest)[PUBLISHER] == "HTTP 200, declares free access"
    assert [s["name"] for s in manifest["supplements"]] == [
        "41467_2020_19808_MOESM1_ESM.pdf",
        "41467_2020_19808_MOESM4_ESM.xlsx",
    ]
    assert [s["why"] for s in manifest["skipped_supplements"]] == [
        "peer review",
        "reporting summary",
    ]
    assert f"{media}MOESM2_ESM.pdf" not in server.asked
    assert f"{media}MOESM3_ESM.pdf" not in server.asked
    assert manifest["missing_supplements"] == []


def test_page_declaring_a_creative_commons_license(tmp_path: Path):
    """PLOS declares open access only by its license, in its copyright line; its
    supplementary links name no file type, the type comes with the download."""
    url = "https://journals.plos.org/plospathogens/article?id=10.1371/journal.ppat.1009743"
    file = "https://journals.plos.org/plospathogens/article/file?type=supplementary&id=10.1371/journal.ppat.1009743"
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": DOI}]}}),
            WORK: json_ok({}),
            PUBLISHER: page("plos.html", url),
            f"{file}.s001": ok(b"II*", "image/tiff"),
            f"{file}.s005": ok(
                b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        },
    )
    assert outcomes(manifest)[PUBLISHER] == "HTTP 200, declares free access"
    assert manifest["file"] == f"{PMID}.html"
    assert [s["file"] for s in manifest["supplements"]] == [
        f"{PMID}.supp/journal.ppat.1009743.s005.xlsx"
    ]
    assert [s["why"] for s in manifest["skipped_supplements"]] == ["image"]
    assert [x["name"] for x in manifest["missing_supplements"]] == [
        f"journal.ppat.1009743.s00{n}" for n in (2, 3, 4, 6, 7)
    ]


def test_paywalled_page_is_no_article_but_lists_the_files(tmp_path: Path):
    """A page that declares a paywall is never the article; its PDF is tried, then the free
    copies' PDFs. Its supplementary links, served freely, are the article's files."""
    pdf = "https://link.springer.com/content/pdf/10.1007/s10495-023-01883-9.pdf"
    docx = "https://media.springernature.com/original/springer-static/esm/art%3A10.1007%2Fs10495-023-01883-9/MediaObjects/10495_2023_1883_MOESM1_ESM.docx"
    repository = location("https://repo.org/record/1", "https://repo.org/record/1.pdf", "Repo")
    manifest, server = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": DOI}]}}),
            WORK: json_ok({"doi": PUBLISHER, "locations": [repository]}),
            PUBLISHER: page("springer-paywall.html", "https://link.springer.com/article/x"),
            pdf: Response(pdf, 403, "", b""),
            "https://repo.org/record/1.pdf": ok(b"%PDF-1.7", "application/pdf"),
            docx: ok(b"PK\x03\x04", "application/octet-stream"),
        },
    )
    assert outcomes(manifest)[PUBLISHER] == "HTTP 200, declares a paywall"
    assert (manifest["file"], manifest["source"]) == (f"{PMID}.pdf", "Repo")
    assert server.asked.index(pdf) < server.asked.index("https://repo.org/record/1.pdf")
    assert manifest["supplements_from"] == "the publisher's page"
    assert [s["file"] for s in manifest["supplements"]] == [
        f"{PMID}.supp/10495_2023_1883_MOESM1_ESM.docx"
    ]
    assert manifest["missing_supplements"] == []


def test_plos_link_names_the_file_without_its_extension(tmp_path: Path):
    """A file of the XML found on the publisher's page, its name inside the link."""
    xml = (
        b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><body><p>T</p>'
        b'<supplementary-material xlink:href="ppat.1002331.s004.doc"/></body></article>'
    )
    link = "https://journals.plos.org/plospathogens/article/file?type=supplementary&id=10.1371/journal.ppat.1002331.s004"
    article_page = f'<html><body><a href="{link}">Table S4</a></body></html>'.encode()
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: found(doi=DOI),
            WORK: json_ok({}),
            f"{PMC_AWS}/?list-type=2&prefix=PMC9.": listing("PMC9.1/PMC9.1.xml"),
            f"{PMC_AWS}/PMC9.1/PMC9.1.xml": ok(xml),
            PUBLISHER: ok(article_page, "text/html", "https://journals.plos.org/x"),
            link: ok(b"\xd0\xcf\x11\xe0", "application/msword"),
        },
    )
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/ppat.1002331.s004.doc"]
    assert manifest["missing_supplements"] == []


def test_supplement_known_as_an_image_only_once_downloaded(tmp_path: Path):
    links = (
        '<a href="/file?type=supplementary&id=s1">Supplementary Table S1</a>'
        '<a href="/file?type=supplementary&id=s2">Supplementary Figure S2</a>'
    )
    free = '<meta name="citation_fulltext_world_readable" content="">'
    html = f"<html><head>{free}</head><body><p>Text</p>{links}</body></html>".encode()
    manifest, _ = run(
        tmp_path,
        {
            WORK: json_ok({"doi": PUBLISHER}),
            PUBLISHER: ok(html, "text/html", url="https://journal.org/article/x"),
            "https://journal.org/file?type=supplementary&id=s1": ok(b"cells", "application/msword"),
            "https://journal.org/file?type=supplementary&id=s2": ok(b"II*", "image/tiff"),
        },
    )
    assert manifest["file"] == f"{PMID}.html"
    assert [s["file"] for s in manifest["supplements"]] == [f"{PMID}.supp/s1.doc"]
    assert [s["why"] for s in manifest["skipped_supplements"]] == ["image"]


# Step 1: access, and the outcome without an article


def test_closed(tmp_path: Path):
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": DOI}]}}),
            WORK: json_ok({"locations": [{"is_oa": False, "landing_page_url": PUBLISHER}]}),
            PUBLISHER: page("springer-paywall.html"),
        },
    )
    assert (manifest["free"], manifest["file"]) == (False, None)
    assert manifest["line"] == "Full text: closed — not open access anywhere"


def test_preprint_is_never_fetched(tmp_path: Path):
    preprint = location("https://doi.org/10.1101/y", "https://www.biorxiv.org/y.pdf", "bioRxiv")
    manifest, server = run(tmp_path, {WORK: json_ok({"locations": [preprint]})})
    assert manifest["line"] == "Full text: closed — open access only as a preprint"
    assert not any("10.1101" in url or "biorxiv" in url for url in server.asked)


def test_free_but_blocked(tmp_path: Path):
    manifest, _ = run(
        tmp_path,
        {
            WORK: json_ok(
                {"doi": PUBLISHER, "locations": [location(PUBLISHER, PUBLISHER + ".pdf")]}
            ),
            PUBLISHER: Response(PUBLISHER, 403, "", b""),
            PUBLISHER + ".pdf": Response(PUBLISHER + ".pdf", 403, "", b""),
        },
    )
    assert (manifest["free"], manifest["file"]) == (True, None)
    assert manifest["line"] == (
        f"Full text: not downloaded — a free copy at {PUBLISHER} but download blocked (HTTP 403)"
    )


def test_page_declaring_free_access_makes_the_article_free(tmp_path: Path):
    """Neither a PMCID nor a free copy listed: the publisher's page decides."""
    manifest, _ = run(
        tmp_path,
        {
            WORK: json_ok({"doi": PUBLISHER}),
            PUBLISHER: page("nature-free.html", "https://www.nature.com/articles/x"),
        },
    )
    assert manifest["free"] is True and manifest["file"] == f"{PMID}.html"


def test_copy_from_unpaywall_when_an_address_is_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "curator@example.org")
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": DOI}]}}),
            WORK: json_ok({}),
            f"{UNPAYWALL}/{DOI}?email=curator%40example.org": json_ok(
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
            "https://repo.org/record/1.pdf": ok(b"%PDF-1.7", "application/pdf"),
        },
    )
    assert manifest["line"] == "Full text: Repo (cc-by, https://repo.org/record/1.pdf)"
    assert manifest["file"] == f"{PMID}.pdf"


def test_unpaywall_is_not_asked_without_an_address(tmp_path: Path):
    manifest, server = run(
        tmp_path, {SEARCH: json_ok({"resultList": {"result": [{"doi": DOI}]}}), WORK: json_ok({})}
    )
    assert not any(url.startswith(UNPAYWALL) for url in server.asked)
    assert (manifest["free"], manifest["file"]) == (False, None)


def test_error_page_sent_as_success(tmp_path: Path):
    manifest, _ = run(tmp_path, {SEARCH: ok(b"<html>Service unavailable</html>", "text/html")})
    assert manifest["line"] == "Full text: closed — not open access anywhere"


# --supplement


def fetched_with_a_missing_file(tmp_path: Path) -> dict[str, Response]:
    responses = {
        SEARCH: found(doi=DOI),
        WORK: json_ok({}),
        f"{PMC_AWS}/?list-type=2&prefix=PMC9.": listing("PMC9.1/PMC9.1.xml", "PMC9.1/s1.xlsx"),
        f"{PMC_AWS}/PMC9.1/PMC9.1.xml": ok(
            XML.replace(b"s2.pdf", b"s3.csv").replace(b"Reporting Summary", b"Table S3")
        ),
        f"{PMC_AWS}/PMC9.1/s1.xlsx": ok(b"cells"),
    }
    manifest, _ = run(tmp_path, responses)
    assert [x["name"] for x in manifest["missing_supplements"]] == ["s3.csv"]
    return responses


def test_supplement_found_at_a_url(tmp_path: Path):
    responses = fetched_with_a_missing_file(tmp_path)
    url = "https://data.org/files/s3.csv"
    responses[url] = ok(b"a,b\n1,2\n", "text/csv")
    lines = fetch_supplements(PMID, tmp_path, [url], Server(responses))
    converted = tmp_path / f"{PMID}.supp" / "s3.csv.md"
    assert lines == [f"s3.csv: found, {converted}"]
    assert converted.read_text() == "a,b\n1,2\n"
    manifest = json.loads((tmp_path / f"{PMID}.json").read_text())
    assert manifest["supplements"][-1] == {
        "name": "s3.csv",
        "file": f"{PMID}.supp/s3.csv",
        "url": url,
        "asked": True,
    }
    assert manifest["missing_supplements"] == []
    assert manifest["line"] == "Full text: PMC9 (no license given)"
    assert (tmp_path / f"{PMID}.xml").read_bytes().startswith(b"<article")


def test_supplement_by_its_label_on_the_publisher_page(tmp_path: Path):
    responses = fetched_with_a_missing_file(tmp_path)
    responses[PUBLISHER] = ok(
        b'<html><body><a href="/suppl/t3.csv">Supplementary Table S3</a></body></html>',
        "text/html",
        "https://journal.org/a",
    )
    responses["https://journal.org/suppl/t3.csv"] = ok(b"x\n", "text/csv")
    lines = fetch_supplements(PMID, tmp_path, ["Table S3", "Table S30"], Server(responses))
    assert lines[0] == f"Table S3: found, {tmp_path / f'{PMID}.supp' / 't3.csv.md'}"
    assert lines[1].startswith("Table S30: missing, tried ")
    manifest = json.loads((tmp_path / f"{PMID}.json").read_text())
    assert [x["name"] for x in manifest["missing_supplements"]] == ["s3.csv", "Table S30"]
    assert manifest["missing_supplements"][-1]["asked"] is True


def test_supplement_still_missing_and_already_there(tmp_path: Path):
    responses = fetched_with_a_missing_file(tmp_path)
    lines = fetch_supplements(PMID, tmp_path, ["s3.csv", "s1.xlsx"], Server(responses))
    assert lines[0] == (
        f"s3.csv: missing, tried {EUROPE_PMC}/PMC9/supplementaryFiles (HTTP 404, no archive)"
    )
    assert lines[1] == f"s1.xlsx: already there, {tmp_path / f'{PMID}.supp' / 's1.xlsx'}"
    manifest = json.loads((tmp_path / f"{PMID}.json").read_text())
    assert [s["name"] for s in manifest["supplements"]] == ["s1.xlsx"]
    assert (
        manifest["line"]
        == "Full text: PMC9 (no license given), supplementary files missing: s3.csv"
    )


def test_preprint_doi_is_never_the_articles(tmp_path: Path):
    """Europe PMC may give the preprint's DOI; OpenAlex the article's."""
    manifest, server = run(
        tmp_path,
        {
            SEARCH: json_ok({"resultList": {"result": [{"doi": "10.1101/y"}]}}),
            WORK: json_ok({"doi": PUBLISHER}),
        },
    )
    assert manifest["doi"] == DOI
    assert PUBLISHER in server.asked and "https://doi.org/10.1101/y" not in server.asked


def test_pmc_copy_of_a_preprint_is_no_article(tmp_path: Path):
    """PubMed links some articles to the PMC copy of their preprint, known by its own DOI."""
    preprint = b'<html><head><meta name="citation_doi" content="10.1101/y"></head><body>'
    preprint += (SAMPLES / "pmc-page.html").read_bytes().split(b"<body>", 1)[1]
    efetch = (
        b'<article><front><article-meta><article-id pub-id-type="doi">10.1101/y</article-id>'
        b"</article-meta></front><body><p>Text</p></body></article>"
    )
    manifest, _ = run(
        tmp_path,
        {
            SEARCH: found(),
            WORK: json_ok({"doi": PUBLISHER}),
            f"{EFETCH}?db=pmc&id=PMC9&rettype=xml": ok(efetch),
            f"{PMC_PAGE}/PMC9/": ok(preprint, "text/html"),
            PUBLISHER: Response(PUBLISHER, 403, "", b""),
        },
    )
    assert manifest["file"] is None
    assert outcomes(manifest)[f"{EFETCH}?db=pmc&id=PMC9&rettype=xml"] == "HTTP 200, a preprint"
    assert outcomes(manifest)[f"{PMC_PAGE}/PMC9/"] == "HTTP 200, a preprint"
    assert manifest["line"] == (
        f"Full text: not downloaded — a free copy at {PUBLISHER} but download blocked (HTTP 403)"
    )

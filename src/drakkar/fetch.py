"""Download the full text of a publication, as published, with its supplementary files.

uv run drakkar-fetch <pmid> <dir>
uv run drakkar-fetch --supplement <pmid> <dir> <url or file name>...

Three steps, each a list of routes; a route answers yes or no by one test.
1. Access: the article is free when it has a PMCID, when OpenAlex or Unpaywall list a free copy
   (never a preprint), or when the publisher's page declares free access (a Creative Commons
   license among the declarations); closed otherwise.
2. The article, from the first route that gives it: the PMC open access files, Europe PMC
   `fullTextXML` and NCBI `efetch` (each when its XML has a body), the PMC article page (when
   it has the body sections), the publisher's HTML page (when it declares free access), then
   the publisher's PDF (`citation_pdf_url`) and the other free copies' PDFs (when the file is
   a PDF).
3. The supplementary files the article lists (its XML, or the supplementary links of its
   page), each looked for on every route that serves one, whatever route gave the article: the
   PMC open access files, the link the article gives, the publisher's page, then Europe PMC's
   supplementary files service. Videos, images, the Reporting Summary and the peer review
   file are skipped.
Nothing is converted (`drakkar-parse`). Writes `<pmid>.xml|html|pdf`, the supplementary files
in `<pmid>.supp/`, and last the manifest `<pmid>.json`: the article, or why there is none, and
each supplementary file found, skipped or missing, with every place tried.

`--supplement` runs step 3 on the files given, also at the URL itself when one is given,
converts each file found to `<file>.md` beside it, and updates the manifest. It never replaces
the article or a file already there.

Configuration, in the project's `.env`: `UNPAYWALL_EMAIL`, the address Unpaywall asks for to
answer a request. Without it Unpaywall is not asked at all.
"""

import argparse
import io
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote, unquote, urljoin, urlparse

from dotenv import load_dotenv
from lxml import etree
from lxml.etree import _Element  # pyright: ignore[reportPrivateUsage]

from drakkar.parse import ParseError, class_names, one_line, parse, tag_name

EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
OPENALEX = "https://api.openalex.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2"
PMC_AWS = "https://pmc-oa-opendata.s3.amazonaws.com"
PMC_PAGE = "https://pmc.ncbi.nlm.nih.gov/articles"
XLINK = "{http://www.w3.org/1999/xlink}href"
# Publishers refuse requests without a browser user agent.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0 drakkar-fetch"
TIMEOUT = 30
SUPPLEMENT_SUFFIXES = {
    ".xlsx",
    ".xls",
    ".xlsm",
    ".csv",
    ".tsv",
    ".txt",
    ".docx",
    ".doc",
    ".pdf",
    ".zip",
}
# Supplementary files no curation reads: videos and images.
VIDEOS = {".mp4", ".mov", ".avi", ".wmv", ".mpg", ".mpeg", ".m4v", ".webm"}
IMAGES = {".tif", ".tiff", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".eps", ".svg", ".webp"}
# Preprints are not peer-reviewed publications: their copies are never fetched.
PREPRINT_HOSTS = (
    "biorxiv.org",
    "medrxiv.org",
    "researchsquare.com",
    "preprints.org",
    "ssrn.com",
    "arxiv.org",
)
PREPRINT_DOIS = ("10.1101/", "10.64898/", "10.21203/", "10.20944/", "10.2139/", "10.48550/")
# PMC copies are fetched by their PMCID (routes of step 2), never as an open access location.
PMC_HOSTS = ("ncbi.nlm.nih.gov", "europepmc.org")
# Services, not copies: a failure there says nothing of where the article is blocked.
SERVICES = (PMC_AWS, EUROPE_PMC, EFETCH)
CAPTION_LENGTH = 200


@dataclass
class Response:
    url: str  # after redirects
    status: int
    content_type: str
    body: bytes


Get = Callable[[str], Response]


def http_get(url: str) -> Response:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as r:
            return Response(r.geturl(), r.status, r.headers.get_content_type(), r.read())
    except urllib.error.HTTPError as e:
        return Response(url, e.code, "", b"")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", e)
        return Response(url, 0, "", str(reason).encode())


def _outcome(r: Response) -> str:
    if r.status == 0:
        return f"failed: {r.body.decode(errors='replace')}"
    return f"HTTP {r.status}"


def _json(get: Get, url: str) -> dict[str, Any] | None:
    r = get(url)
    if r.status != 200:
        return None
    try:
        return cast(dict[str, Any], json.loads(r.body))
    except ValueError:  # an error page sent as a success
        return None


def _is_pdf(r: Response) -> bool:
    return r.body.startswith(b"%PDF")


def _is_html(r: Response) -> bool:
    return r.content_type in ("text/html", "application/xhtml+xml")


def _xml(body: bytes) -> _Element | None:
    try:
        return etree.fromstring(body, etree.XMLParser(resolve_entities=False, no_network=True))
    except etree.XMLSyntaxError:
        return None


def _html(body: bytes) -> _Element | None:
    try:
        return etree.fromstring(body, etree.HTMLParser())
    except (etree.XMLSyntaxError, ValueError):
        return None


def _zip(body: bytes) -> zipfile.ZipFile | None:
    try:
        return zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile:
        return None


def _text(el: _Element) -> str:
    return one_line(" ".join(str(t) for t in el.itertext()))


def _safe_name(name: str, taken: set[str]) -> str:
    """A file name with no path and no odd character, unique in the directory."""
    name = re.sub(r"[^\w.-]", "_", name).lstrip(".") or "file"
    stem, suffix, n = Path(name).stem, Path(name).suffix, 1
    while name in taken:
        n += 1
        name = f"{stem}_{n}{suffix}"
    taken.add(name)
    return name


def _extension(name: str) -> str:
    """The extension of a file name when it names a file type: not `.s004` in PLOS's
    `journal.ppat.1002331.s004`."""
    suffix = Path(name).suffix.lower()
    known = SUPPLEMENT_SUFFIXES | VIDEOS | IMAGES
    return suffix if suffix in known or mimetypes.guess_type(f"x{suffix}")[0] else ""


def _url_name(url: str) -> str:
    """The last part of the URL's path, or of its query when the path names no file."""
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    if not _extension(name) and parsed.query:
        name = re.split(r"[=/]", unquote(parsed.query))[-1]
    return name


def _left_out(name: str, caption: str = "") -> str | None:
    """Why a supplementary file is not fetched: a video (or an archive named as videos,
    `movies_s1_to_s3.zip`), an image, or by its caption the Reporting Summary (a checklist) or
    the peer review file: none holds an interaction."""
    suffix = Path(name).suffix.lower()
    if suffix in VIDEOS or re.search(r"movie|video", name, re.I):
        return "video"
    if suffix in IMAGES:
        return "image"
    if re.search(r"reporting summary", caption, re.I):
        return "reporting summary"
    if re.search(r"peer review (file|report)|transparent peer review", caption, re.I):
        return "peer review"
    return None


def _same_file(name: str, url: str, text: str = "") -> bool:
    """Whether a link holds the file the article names: the same file name; or its name,
    extension apart, standing whole in the URL (`s004` in `...journal.ppat.1002331.s004`,
    `mmc1` in `...-mmc1.xlsx`); or, for a label rather than a file name (`Table S1`), standing
    whole in the link's text."""
    if Path(unquote(urlparse(url).path)).name.lower() == name.lower():
        return True
    stem = (Path(name).stem if _extension(name) else name).lower()
    whole = rf"(?<![a-z0-9]){re.escape(stem)}(?![a-z0-9])"
    if len(stem) >= 3 and re.search(whole, unquote(url).lower()):
        return True
    return not _extension(name) and bool(re.search(whole, one_line(text).lower()))


def _is_preprint(location: dict[str, Any]) -> bool:
    urls = [(location.get(k) or "").lower() for k in ("landing_page_url", "pdf_url")]
    return any(
        any(host in urlparse(url).netloc for host in PREPRINT_HOSTS)
        or any(f"doi.org/{prefix}" in url for prefix in PREPRINT_DOIS)
        for url in urls
    )


def _locations(work: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], work.get("locations") or [])


def _is_pmc(url: str | None) -> bool:
    return any(host in urlparse(url or "").netloc for host in PMC_HOSTS)


def _pmcid(url: str | None) -> str | None:
    """The PMCID of a PMC link: `.../pmc/articles/123` or `.../articles/PMC123/`."""
    m = re.search(r"/articles/(?:PMC)?(\d+)", url or "") if _is_pmc(url) else None
    return f"PMC{m.group(1)}" if m else None


def pmcids(record: dict[str, Any], work: dict[str, Any]) -> list[str]:
    """Every PMCID of a publication, Europe PMC's first: Europe PMC can lag behind PMC, and
    OpenAlex gives some only in the links of its PMC copies."""
    ids = cast(dict[str, Any], work.get("ids") or {})
    found = [record.get("pmcid"), _pmcid(ids.get("pmcid"))]
    found += [_pmcid(x.get("landing_page_url")) for x in _locations(work)]
    return list(dict.fromkeys(p for p in found if p))


def _pmc_license(record: dict[str, Any], work: dict[str, Any]) -> str:
    if record.get("license"):
        return record["license"]
    for location in _locations(work):
        if _is_pmc(location.get("landing_page_url")) and location.get("license"):
            return location["license"]
    return "no license given"


@dataclass
class Supplement:
    """A supplementary file the article lists: its file name (or the label the curation gives
    it), its caption, and the link the article gives to it when that link can be fetched."""

    name: str
    caption: str = ""
    url: str | None = None


def jats_supplements(xml: bytes) -> list[Supplement]:
    """The supplementary files of a PMC XML, in their order, with their captions."""
    root = _xml(xml)
    found: dict[str, Supplement] = {}
    if root is None:
        return []

    def caption(node: _Element) -> str:
        return " ".join(_text(c) for c in node if tag_name(c) in ("label", "caption"))

    for el in root.iter("{*}supplementary-material", "{*}inline-supplementary-material"):
        for node in [el, *el.iter("{*}media")]:
            name = node.get(XLINK)
            if name and name not in found:
                # The caption of the material, or of its file (Nature's: `media/caption`).
                both = (caption(el), caption(node) if node is not el else "")
                found[name] = Supplement(name, " ".join(c for c in both if c))
    return list(found.values())


def pmc_page_supplements(page: bytes) -> list[Supplement]:
    """The supplementary files of a PMC article page, from its supplementary sections. Their
    links on the PMC website are behind a challenge: only their names are kept."""
    doc = _html(page)
    found: dict[str, Supplement] = {}
    if doc is None:
        return []
    for section in doc.iter("section"):
        if "sm" not in class_names(section):
            continue
        for a in section.iter("a"):
            href = a.get("href") or ""
            if "/bin/" in href:
                name = _url_name(href)
                found.setdefault(name, Supplement(name, _text(section)))
    return list(found.values())


def _is_preprint_doi(doi: str | None) -> bool:
    return bool(doi) and doi.lower().removeprefix("https://doi.org/").startswith(PREPRINT_DOIS)


def pmc_xml_problem(xml: bytes) -> str | None:
    """Why a PMC XML is not the article: no body (`efetch` answers the front matter alone for an
    article it does not serve), or the copy of a preprint, by its own DOI."""
    if b"<body" not in xml:
        return "no body"
    doi = re.search(rb'<article-id pub-id-type="doi">\s*([^<\s]+)', xml)
    return "a preprint" if doi and _is_preprint_doi(doi.group(1).decode(errors="replace")) else None


def pmc_page_problem(page: bytes) -> str | None:
    """Why a PMC article page is not the article: no body sections, or the copy of a preprint,
    by its own DOI (`citation_doi`)."""
    if not pmc_page_has_body(page):
        return "no body sections"
    return "a preprint" if _is_preprint_doi(_meta(page, "citation_doi")) else None


def pmc_page_has_body(page: bytes) -> bool:
    """A PMC article page holds the article when its main body has sections of its own, beyond
    the abstract and the back matter: those have a class, or are notes."""
    doc = _html(page)
    if doc is None:
        return False
    for body in doc.iter("section"):
        if "main-article-body" not in class_names(body):
            continue
        for section in body.iterchildren("section"):
            own = not section.get("class") and not (section.get("id") or "").startswith("notes")
            if own and next(section.iter("p"), None) is not None:
                return True
    return False


def declared_access(page: bytes) -> bool | None:
    """What a publisher's page declares of the article's access: True free, False a paywall,
    None nothing. Free: `"isAccessibleForFree": true`, `<meta name="access" content="Yes">`,
    `citation_fulltext_world_readable`, or a link to the article's Creative Commons license
    (PLOS declares it only so, in its copyright line). A paywall declared anywhere wins."""
    found = {
        m.lower()
        for m in re.findall(
            rb'"isAccessibleForFree"\s*:\s*"?(true|false)', page, flags=re.IGNORECASE
        )
    }
    doc = _html(page)
    for meta in doc.iter("meta") if doc is not None else iter(()):
        name, content = (meta.get("name") or "").lower(), (meta.get("content") or "").lower()
        if name == "access" and content in ("yes", "no"):
            found.add(b"true" if content == "yes" else b"false")
        elif name == "citation_fulltext_world_readable":
            found.add(b"true")
    for link in doc.iter("a", "link") if doc is not None else iter(()):
        if "creativecommons.org/licenses/" in (link.get("href") or "").lower():
            found.add(b"true")
    if b"false" in found:
        return False
    return True if b"true" in found else None


def _meta(page: bytes, name: str) -> str | None:
    doc = _html(page)
    for meta in doc.iter("meta") if doc is not None else iter(()):
        if (meta.get("name") or "").lower() == name and meta.get("content"):
            return meta.get("content")
    return None


def supplement_links(page: bytes, base: str) -> list[Supplement]:
    """The supplementary files a publisher's page links: a link or a URL that says
    supplementary (`mmc` is Elsevier's name for them, `MOESM` Springer Nature's), to a file type
    or to a URL that names no type (PLOS: `article/file?type=supplementary&id=...`)."""
    doc = _html(page)
    found: dict[str, Supplement] = {}
    for a in doc.iter("a") if doc is not None else iter(()):
        href = a.get("href")
        if not href or href.startswith("#"):
            continue
        url, text = urljoin(base, href), _text(a)
        lowered = unquote(url).lower()
        named = re.search(r"supp|mmc\d|moesm", lowered) or re.search(r"supp|additional", text, re.I)
        suffix = Path(urlparse(url).path).suffix.lower()
        typed = suffix in SUPPLEMENT_SUFFIXES | VIDEOS | IMAGES or "supplementary" in lowered
        if named and typed and url not in found:
            found[url] = Supplement(_url_name(url), text, url)
    return list(found.values())


class Fetch:
    def __init__(self, pmid: int, out: Path, get: Get) -> None:
        self.pmid, self.out, self.get = pmid, out, get
        self.manifest: dict[str, Any] = {"pmid": pmid, "file": None}
        self.tried: list[dict[str, str]] = []  # the routes of the article
        self.taken: set[str] = set()
        self.record: dict[str, Any] = {}
        self.work: dict[str, Any] = {}
        self.pmcids: list[str] = []
        self.doi: str | None = None
        self.listed: list[Supplement] = []
        self.oa_files: dict[str, str] = {}  # the PMC open access files, name to URL
        self._page: Response | None = None
        self._copies: list[dict[str, Any]] | None = None
        self._archive: tuple[zipfile.ZipFile | None, str] | None = None  # and its outcome
        load_dotenv()

    # Requests

    def _try(self, url: str) -> Response:
        r = self.get(url)
        self.tried.append({"url": url, "outcome": _outcome(r)})
        return r

    def _note(self, outcome: str) -> None:
        self.tried[-1]["outcome"] += f", {outcome}"

    @property
    def page(self) -> Response | None:
        """The publisher's page, at the DOI, asked once."""
        if self._page is None and self.doi:
            self._page = self._try(f"https://doi.org/{self.doi}")
            if self._page.status == 200 and _is_html(self._page):
                said: dict[bool | None, str] = {
                    True: "declares free access",
                    False: "declares a paywall",
                    None: "declares no access",
                }
                self._note(said[declared_access(self._page.body)])
        return self._page

    @property
    def html_page(self) -> Response | None:
        """The publisher's page when it is an HTML page."""
        page = self.page
        return page if page is not None and page.status == 200 and _is_html(page) else None

    @property
    def copies(self) -> list[dict[str, Any]]:
        """The free copies OpenAlex and Unpaywall list, best first, never a preprint nor a PMC
        copy (fetched by its PMCID). Unpaywall is asked once, and only when needed."""
        if self._copies is None:
            best = self.work.get("best_oa_location")
            locations = [best] if best else []
            locations += [x for x in _locations(self.work) if x.get("is_oa") and x != best]
            if self.doi:
                locations += self.unpaywall(self.doi)
            self._copies, seen = [], set[str]()
            for location in locations:
                key = f"{location.get('landing_page_url')}|{location.get('pdf_url')}"
                if _is_pmc(location.get("landing_page_url")) or key in seen:
                    continue
                seen.add(key)
                self._copies.append(location)
        return self._copies

    def unpaywall(self, doi: str) -> list[dict[str, Any]]:
        """Unpaywall's open access copies, in its own order (best first). It answers only a
        request that carries an address, so it is asked only when one is configured."""
        email = os.environ.get("UNPAYWALL_EMAIL")
        if not email:
            return []
        record = _json(self.get, f"{UNPAYWALL}/{quote(doi)}?email={quote(email)}")
        locations = cast(list[dict[str, Any]], (record or {}).get("oa_locations") or [])
        return [
            {
                "is_oa": True,
                "landing_page_url": x.get("url_for_landing_page") or x.get("url"),
                "pdf_url": x.get("url_for_pdf"),
                "license": x.get("license"),
                "source": {"display_name": x.get("repository_institution") or "Unpaywall"},
            }
            for x in locations
        ]

    def _publisher(self) -> dict[str, Any]:
        """The publisher's location in OpenAlex, the one at the DOI, for its name and license."""
        doi = f"https://doi.org/{self.doi}".lower()
        for location in _locations(self.work):
            if (location.get("landing_page_url") or "").lower() == doi:
                return location
        return {}

    # Step 1: access

    def free(self) -> bool:
        return bool(
            self.pmcids
            or [x for x in self.copies if not _is_preprint(x)]
            or ((page := self.html_page) is not None and declared_access(page.body) is True)
        )

    def closed_why(self) -> str:
        if any(_is_preprint(x) for x in self.copies):
            return "open access only as a preprint"
        return "not open access anywhere"

    # Step 2: the article

    def article_routes(self) -> Iterator[Callable[[], bool]]:
        for pmcid in self.pmcids:
            yield lambda pmcid=pmcid: self.pmc_files(pmcid)
            yield lambda pmcid=pmcid: self.pmc_xml(pmcid, f"{EUROPE_PMC}/{pmcid}/fullTextXML")
            yield lambda pmcid=pmcid: self.pmc_xml(pmcid, f"{EFETCH}?db=pmc&id={pmcid}&rettype=xml")
        for pmcid in self.pmcids:
            yield lambda pmcid=pmcid: self.pmc_page(pmcid)
        yield self.publisher_html
        yield self.pdfs

    def _save(self, body: bytes, suffix: str) -> None:
        name = f"{self.pmid}{suffix}"
        (self.out / name).write_bytes(body)
        self.manifest["file"] = name

    def _from_pmc(self, pmcid: str) -> None:
        license_ = _pmc_license(self.record, self.work)
        self.manifest.update(source=pmcid, url=f"{PMC_PAGE}/{pmcid}/", license=license_)

    def _from(self, url: str, location: dict[str, Any]) -> None:
        venue = cast(dict[str, Any], location.get("source") or {})
        source = venue.get("display_name") or urlparse(url).netloc
        license_ = location.get("license") or "no license given"
        self.manifest.update(source=source, url=url, license=license_)

    def pmc_listing(self, pmcid: str) -> str | None:
        """The latest version of a PMC copy in the open access files (`PMC123.2` after
        `PMC123.1`), its files kept as a route of step 3."""
        listing = self._try(f"{PMC_AWS}/?list-type=2&prefix={pmcid}.")
        keys = re.findall(r"<Key>([^<]+)</Key>", listing.body.decode(errors="replace"))
        if not keys:
            if listing.status == 200:
                self._note("not in the PMC open access files")
            return None
        version = max({k.split("/")[0] for k in keys}, key=lambda v: int(v.split(".")[1]))
        for key in keys:
            folder, _, name = key.partition("/")
            if folder == version:
                self.oa_files[name] = f"{PMC_AWS}/{version}/{quote(name)}"
        return version

    def pmc_files(self, pmcid: str) -> bool:
        """The PMC open access files: their XML as `pmc_xml`, with its PDF."""
        version = self.pmc_listing(pmcid)
        if version is None or not self.pmc_xml(pmcid, f"{PMC_AWS}/{version}/{version}.xml"):
            return False
        if f"{version}.pdf" in self.oa_files:
            pdf = self.get(self.oa_files[f"{version}.pdf"])
            if pdf.status == 200 and _is_pdf(pdf):
                (self.out / f"{self.pmid}.pdf").write_bytes(pdf.body)
                self.manifest["pdf"] = f"{self.pmid}.pdf"
        return True

    def pmc_xml(self, pmcid: str, url: str) -> bool:
        """A PMC XML (the open access files', Europe PMC `fullTextXML` or NCBI `efetch`), the
        article when it has a body and is no preprint."""
        xml = self._try(url)
        if xml.status != 200:
            return False
        if problem := pmc_xml_problem(xml.body):
            self._note(problem)
            return False
        self._save(xml.body, ".xml")
        self._from_pmc(pmcid)
        self._list(jats_supplements(xml.body), "the article's XML")
        return True

    def pmc_page(self, pmcid: str) -> bool:
        """The PMC article page: the whole article of a PMC copy outside the open access files.
        NCBI forbids bulk downloads from its website: one page per publication."""
        r = self._try(f"{PMC_PAGE}/{pmcid}/")
        if r.status != 200:
            return False
        if problem := pmc_page_problem(r.body):
            self._note(problem)
            return False
        self._save(r.body, ".html")
        self._from_pmc(pmcid)
        self._list(pmc_page_supplements(r.body), "the PMC article page")
        return True

    def publisher_html(self) -> bool:
        """The publisher's page, the article when it declares free access."""
        page = self.html_page
        if page is None or declared_access(page.body) is not True:
            return False
        self._save(page.body, ".html")
        self._from(page.url, self._publisher())
        return True

    def pdfs(self) -> bool:
        """The publisher's PDF (`citation_pdf_url`), then the other free copies' PDFs."""
        candidates: list[tuple[str, dict[str, Any]]] = []
        if (page := self.html_page) is not None and (url := _meta(page.body, "citation_pdf_url")):
            candidates.append((url, self._publisher()))
        for location in self.copies:
            if not _is_preprint(location):
                for key in ("pdf_url", "landing_page_url"):
                    if url := location.get(key):
                        candidates.append((url, location))
        seen: set[str] = {t["url"] for t in self.tried}
        for url, location in candidates:
            if url in seen:
                continue
            seen.add(url)
            r = self._try(url)
            if r.status == 200 and _is_pdf(r):
                self._save(r.body, ".pdf")
                self._from(url, location)
                return True
            if r.status == 200:
                self._note("not a PDF")
        return False

    def _list(self, supplements: list[Supplement], source: str) -> None:
        self.listed = supplements
        self.manifest["supplements_from"] = source

    # Step 3: the supplementary files

    def supplement_routes(self, item: Supplement) -> Iterator[str]:
        """The URLs that may serve a file, in order; Europe PMC's archive comes after them all."""
        for name, url in self.oa_files.items():
            if name == item.name or _same_file(item.name, url):
                yield url
        if item.url and not _is_pmc(item.url):
            yield item.url
        if (page := self.html_page) is not None:
            for link in supplement_links(page.body, page.url):
                if (
                    link.url
                    and link.url != item.url
                    and _same_file(item.name, link.url, link.caption)
                ):
                    yield link.url

    def find(self, items: list[Supplement]) -> list[tuple[Supplement, list[dict[str, str]]]]:
        """Each file looked for on every route; returns the files still missing, with every
        place tried."""
        missing: list[tuple[Supplement, list[dict[str, str]]]] = []
        for item in items:
            if why := _left_out(item.name, item.caption):
                self._skip(item, why)
                continue
            tried: list[dict[str, str]] = []
            for url in dict.fromkeys(self.supplement_routes(item)):
                r = self.get(url)
                tried.append({"url": url, "outcome": _outcome(r)})
                if self._take(item, r, url, tried):
                    break
            else:
                missing.append((item, tried))
        if missing and self.pmcids:
            missing = self.from_europe_pmc(missing)
        return missing

    def from_europe_pmc(
        self, missing: list[tuple[Supplement, list[dict[str, str]]]]
    ) -> list[tuple[Supplement, list[dict[str, str]]]]:
        """Europe PMC's supplementary files service: one archive of all of them, slow, so it is
        asked once and last."""
        url = f"{EUROPE_PMC}/{self.pmcids[0]}/supplementaryFiles"
        if self._archive is None:
            r = self.get(url)
            archive = _zip(r.body) if r.status == 200 and r.body[:2] == b"PK" else None
            self._archive = (archive, _outcome(r) + ("" if archive else ", no archive"))
        archive, outcome = self._archive
        still: list[tuple[Supplement, list[dict[str, str]]]] = []
        for item, tried in missing:
            members = [
                m
                for m in (archive.infolist() if archive else [])
                if not m.is_dir() and _same_file(item.name, Path(m.filename).name)
            ]
            for member in members:
                assert archive is not None
                body = archive.read(member)
                self._keep(item, Path(member.filename).name, body, f"{url}#{member.filename}")
            if not members:
                place = outcome if archive is None else f"{outcome}, not in it"
                still.append((item, [*tried, {"url": url, "outcome": place}]))
        return still

    def _take(self, item: Supplement, r: Response, url: str, tried: list[dict[str, str]]) -> bool:
        """Whether a response is the file: kept, or skipped once its type shows an image."""
        if r.status != 200:
            return False
        if r.content_type.startswith(("image/", "video/")):  # a link that named no type
            self._skip(item, r.content_type.split("/")[0])
            return True
        if _is_html(r):
            tried[-1]["outcome"] += ", an HTML page"
            return False
        name = item.name if _extension(item.name) else _url_name(url)
        if Path(name).suffix.lower() not in SUPPLEMENT_SUFFIXES:
            name += mimetypes.guess_extension(r.content_type) or ""
        self._keep(item, name, r.body, url)
        return True

    def _keep(self, item: Supplement, name: str, body: bytes, url: str) -> None:
        """A supplementary file saved; a zip archive is unpacked, its videos and images left
        out."""
        archive = _zip(body) if name.lower().endswith(".zip") else None
        if archive is not None:
            for info in archive.infolist():
                member = Path(info.filename)
                if info.is_dir() or "__MACOSX" in member.parts or member.name[:1] == ".":
                    continue
                inside = Supplement(member.name, item.caption)
                if why := _left_out(member.name):
                    self._skip(inside, why, f"{url}#{info.filename}")
                else:
                    self._keep(item, member.name, archive.read(info), f"{url}#{info.filename}")
            return
        folder = self.out / f"{self.pmid}.supp"
        folder.mkdir(exist_ok=True)
        self.taken |= {p.name for p in folder.iterdir()}
        name = _safe_name(name, self.taken)
        (folder / name).write_bytes(body)
        self.manifest.setdefault("supplements", []).append(
            {"name": item.name, "file": f"{folder.name}/{name}", "url": url}
        )

    def _skip(self, item: Supplement, why: str, url: str | None = None) -> None:
        entry = {"name": item.name, "why": why}
        if url or item.url:
            entry["url"] = url or item.url or ""
        self.manifest.setdefault("skipped_supplements", []).append(entry)

    # The manifest

    def _missing(self, item: Supplement, tried: list[dict[str, str]]) -> dict[str, Any]:
        entry: dict[str, Any] = {"name": item.name}
        if item.caption:
            entry["caption"] = item.caption[:CAPTION_LENGTH]
        if item.url:
            entry["url"] = item.url
        entry["tried"] = tried
        return entry

    def conclude(self) -> None:
        """The `Full text` line of the publication note."""
        m = self.manifest
        missing = [x["name"] for x in m.get("missing_supplements", [])]
        if m["file"] is None:
            if m["free"]:
                m["why"] = self.not_downloaded_why()
                m["line"] = f"Full text: not downloaded — {m['why']}"
            else:
                m["line"] = f"Full text: closed — {m['why']}"
            return
        m.pop("why", None)
        if m["source"] in self.pmcids:
            m["line"] = f"Full text: {m['source']} ({m['license']})"
        else:
            m["line"] = f"Full text: {m['source']} ({m['license']}, {m['url']})"
        if missing:
            m["line"] += ", supplementary files missing: " + ", ".join(missing)

    def not_downloaded_why(self) -> str:
        """Why a free article was not downloaded: the first copy tried, outside the services
        and the preprints."""
        tried = self.manifest.get("tried", [])
        copies = [
            t
            for t in tried
            if not t["url"].startswith(SERVICES) and not t["outcome"].endswith("a preprint")
        ]
        for t in copies:
            if not t["outcome"].startswith("HTTP 200"):
                return f"a free copy at {t['url']} but download blocked ({t['outcome']})"
        if copies:
            return f"a free copy at {copies[0]['url']} but no article there"
        return "free, but no copy to download"

    def write(self) -> dict[str, Any]:
        path = self.out / f"{self.pmid}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)  # last: a manifest means the fetch is done
        return self.manifest

    # The two modes

    def _identify(self) -> None:
        query = quote(f"EXT_ID:{self.pmid} AND SRC:MED")
        search = _json(self.get, f"{EUROPE_PMC}/search?query={query}&format=json&resultType=core")
        results = (search or {}).get("resultList", {}).get("result", [])
        self.record = cast(dict[str, Any], results[0]) if results else {}
        self.work = _json(self.get, f"{OPENALEX}/pmid:{self.pmid}") or {}
        self.pmcids = pmcids(self.record, self.work)
        # Europe PMC may give the DOI of the preprint, never the article's.
        work_doi = (self.work.get("doi") or "").removeprefix("https://doi.org/")
        dois = [d for d in (self.record.get("doi"), work_doi) if d]
        self.doi = next((d for d in dois if not _is_preprint_doi(d)), None)

    def run(self) -> dict[str, Any]:
        self.out.mkdir(parents=True, exist_ok=True)
        self._identify()
        m = self.manifest
        m.update(pmcid=self.pmcids[0] if self.pmcids else None, pmcids=self.pmcids, doi=self.doi)
        m["free"] = self.free()
        if not m["free"]:
            m["why"] = self.closed_why()
        any(route() for route in self.article_routes())
        m["tried"] = self.tried
        if m["file"] is not None:
            if "supplements_from" not in m and (page := self.html_page) is not None:
                self._list(supplement_links(page.body, page.url), "the publisher's page")
            m.setdefault("supplements", [])
            missing = self.find(self.listed)
            m["missing_supplements"] = [self._missing(item, tried) for item, tried in missing]
        self.conclude()
        return self.write()

    def supplement(self, asked: list[str]) -> list[str]:
        """Step 3 on the files the curation asks for; returns one line per file."""
        m = self.manifest = json.loads((self.out / f"{self.pmid}.json").read_text())
        self.pmcids = m.get("pmcids") or ([m["pmcid"]] if m.get("pmcid") else [])
        self.doi = m.get("doi")
        for pmcid in self.pmcids:
            self.pmc_listing(pmcid)  # self.tried, not the manifest's: no route of the article
        m.setdefault("supplements", [])
        m.setdefault("missing_supplements", [])
        listed = {x["name"]: x for x in m["missing_supplements"]}
        lines: list[str] = []
        for arg in asked:
            url = arg if re.match(r"https?://", arg) else None
            name = _url_name(arg) if url else arg
            there = [s for s in m["supplements"] if name in (s["name"], Path(s["file"]).name)]
            if there:
                lines.append(f"{name}: already there, {self.out / there[0]['file']}")
                continue
            known = listed.get(name, {})
            item = Supplement(name, known.get("caption", ""), url or known.get("url"))
            kept, skipped = len(m["supplements"]), len(m.get("skipped_supplements", []))
            others = [x for x in m["missing_supplements"] if x["name"] != name]
            if missing := self.find([item]):
                tried = missing[0][1]
                m["missing_supplements"] = [*others, self._missing(item, tried) | {"asked": True}]
                places = "; ".join(f"{t['url']} ({t['outcome']})" for t in tried)
                lines.append(f"{name}: missing, tried {places or 'nothing: no route holds it'}")
                continue
            m["missing_supplements"] = others
            for s in m["supplements"][kept:]:
                s["asked"] = True
                lines.append(f"{name}: found, {self.convert(s['file'])}")
            for s in m.get("skipped_supplements", [])[skipped:]:
                lines.append(f"{name}: skipped, {s['why']}")
        if m["file"] is not None:
            self.conclude()
        self.write()
        return lines

    def convert(self, file: str) -> str:
        source = self.out / file
        target = source.with_name(source.name + ".md")
        try:
            target.write_text(parse(source), encoding="utf-8")
        except ParseError as e:
            return f"{source}, not converted: {e}"
        return str(target)


def fetch(pmid: int, out: Path, get: Get = http_get) -> dict[str, Any]:
    return Fetch(pmid, out, get).run()


def fetch_supplements(pmid: int, out: Path, asked: list[str], get: Get = http_get) -> list[str]:
    return Fetch(pmid, out, get).supplement(asked)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the full text of a publication.")
    parser.add_argument(
        "--supplement",
        action="store_true",
        help="look for the supplementary files given, for a publication already fetched",
    )
    parser.add_argument("pmid", type=int)
    parser.add_argument("dir", type=Path)
    parser.add_argument("files", nargs="*", help="with --supplement: URLs or file names")
    args = parser.parse_args()
    if args.supplement:
        if not args.files:
            parser.error("--supplement needs at least one URL or file name")
        if not (args.dir / f"{args.pmid}.json").exists():
            sys.exit(f"{args.dir}: no manifest, fetch the publication first")
        print("\n".join(fetch_supplements(args.pmid, args.dir, args.files)))
    else:
        if args.files:
            parser.error("files are given only with --supplement")
        print(fetch(args.pmid, args.dir)["line"])

"""Download the full text of a publication, as published, with its supplementary files.

uv run drakkar-fetch <pmid> <dir>

Sources, the first that works. Every PMCID Europe PMC or OpenAlex knows is tried on 1 to 3:
1. The PMC open access files: the XML, its PDF and its supplementary files, the only source
   that holds them all.
2. Europe PMC `fullTextXML`: the XML alone.
3. NCBI `efetch db=pmc`: the XML alone, for a PMC copy outside the open access files.
4. After 2 or 3, Europe PMC's supplementary files service, the one source left for them; when
   it holds none, the manifest says the supplementary files were not offered, which is not the
   same as a publication that has none.
5. A copy elsewhere, from the open access locations of OpenAlex, Unpaywall and Crossref: the
   publisher at the DOI first, then the repositories (never a preprint server), an HTML full
   text before a PDF.
6. Failing all of them: a PDF the user provides, saved as `<pmid>.pdf` outside this tool.
Nothing is converted (`drakkar-parse`). Writes `<pmid>.xml|html|pdf`, the supplementary files
in `<pmid>.supp/` (no video, no image), and last the manifest `<pmid>.json`: where the full
text comes from, or why there is none.

Configuration, in the project's `.env`: `UNPAYWALL_EMAIL`, the address Unpaywall asks for to
answer a request. Without it Unpaywall is not asked at all.
"""

import argparse
import io
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import quote, unquote, urljoin, urlparse

import trafilatura
from dotenv import load_dotenv
from lxml import etree

EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
OPENALEX = "https://api.openalex.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2"
CROSSREF = "https://api.crossref.org/works"
PMC_AWS = "https://pmc-oa-opendata.s3.amazonaws.com"
XLINK = "{http://www.w3.org/1999/xlink}href"
# Publishers refuse requests without a browser user agent.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0 drakkar-fetch"
TIMEOUT = 30
# An HTML page is a full text, not a landing page, when its main text has this many words:
# an abstract page, even with its reference list, has fewer; an article has more.
FULL_TEXT_WORDS = 2000
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
# The PMC website refuses downloads: its copies are fetched as PMC (steps 1 to 3), never as pages.
PMC_HOSTS = ("ncbi.nlm.nih.gov", "europepmc.org")


def _setting(name: str) -> str | None:
    """A setting of the project's `.env`, absent when it is not configured: a request that
    needs it is not made at all, so nothing of the user is sent without being configured."""
    load_dotenv()
    return os.environ.get(name) or None


@dataclass
class Response:
    url: str  # after redirects
    status: int
    content_type: str
    body: bytes


class Get(Protocol):
    def __call__(self, url: str, headers: dict[str, str] | None = None) -> Response: ...


def http_get(url: str, headers: dict[str, str] | None = None) -> Response:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
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


def _words(html: bytes) -> int:
    text = trafilatura.extract(html, include_tables=True) or ""  # bytes: it finds the charset
    return len(text.split())


def _safe_name(name: str, taken: set[str]) -> str:
    """A file name with no path and no odd character, unique in the directory."""
    name = re.sub(r"[^\w.-]", "_", name).lstrip(".") or "file"
    stem, suffix, n = Path(name).stem, Path(name).suffix, 1
    while name in taken:
        n += 1
        name = f"{stem}_{n}{suffix}"
    taken.add(name)
    return name


def _file_name(url: str, taken: set[str]) -> str:
    """The last part of the URL's path, or of its query when the path names no file."""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not Path(name).suffix and parsed.query:
        name = re.split(r"[=/]", parsed.query)[-1]
    return _safe_name(unquote(name), taken)


def _left_out(name: str) -> str | None:
    """Why a supplementary file is not fetched: a video (or an archive named as videos,
    `movies_s1_to_s3.zip`) or an image."""
    suffix = Path(name).suffix.lower()
    if suffix in VIDEOS or re.search(r"movie|video", name, re.I):
        return "video"
    return "image" if suffix in IMAGES else None


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


def supplementary_files(xml: bytes) -> list[str]:
    """The files of the supplementary materials of a PMC XML, in their order."""
    root = etree.fromstring(xml, etree.XMLParser(resolve_entities=False, no_network=True))
    names: list[str] = []
    for el in root.iter("{*}supplementary-material"):
        for node in [el, *el.iter("{*}media")]:
            name = node.get(XLINK)
            if name and name not in names:
                names.append(name)
    return names


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href, self._text = dict(attrs).get("href"), []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text)))
            self._href = None


def supplement_links(html: bytes, base: str) -> list[str]:
    """Links of an HTML full text to its supplementary files: a link or a URL that says
    supplementary (`mmc` is Elsevier's name for them), to a file type a curation reads or to a
    URL that names no type (PLOS: `article/file?type=supplementary&id=...`)."""
    parser = _Links()
    parser.feed(html.decode(errors="replace"))
    urls: list[str] = []
    for href, text in parser.links:
        url = urljoin(base, href)
        path = urlparse(url).path.lower()
        named = re.search(r"supp|mmc\d", url.lower()) or re.search(r"supp|additional", text.lower())
        typed = Path(path).suffix in SUPPLEMENT_SUFFIXES or "supplementary" in url.lower()
        if named and typed and url not in urls:
            urls.append(url)
    return urls


class Fetch:
    def __init__(self, pmid: int, out: Path, get: Get) -> None:
        self.pmid, self.out, self.get = pmid, out, get
        self.manifest: dict[str, Any] = {"pmid": pmid, "file": None, "supplements": []}
        self.tried: list[dict[str, str]] = []
        self.taken: set[str] = set()

    def _try(self, url: str, headers: dict[str, str] | None = None) -> Response:
        r = self.get(url, headers)
        self.tried.append({"url": url, "outcome": _outcome(r)})
        return r

    def _save(self, r: Response, suffix: str) -> None:
        name = f"{self.pmid}{suffix}"
        (self.out / name).write_bytes(r.body)
        self.manifest["file"] = name

    def _supplement(self, name: str, body: bytes, url: str) -> None:
        """A supplementary file; a zip archive is unpacked, its videos and images left out."""
        if name.lower().endswith(".zip"):
            try:
                archive = zipfile.ZipFile(io.BytesIO(body))
            except zipfile.BadZipFile:
                archive = None
            if archive is not None:
                for info in archive.infolist():
                    member = Path(info.filename)
                    if info.is_dir() or "__MACOSX" in member.parts or member.name[:1] == ".":
                        continue
                    if why := _left_out(member.name):
                        self._skip(f"{url}#{info.filename}", why)
                    else:
                        member_name = _safe_name(member.name, self.taken)
                        self._supplement(member_name, archive.read(info), f"{url}#{info.filename}")
                return
        folder = self.out / f"{self.pmid}.supp"
        folder.mkdir(exist_ok=True)
        (folder / name).write_bytes(body)
        self.manifest["supplements"].append({"file": f"{folder.name}/{name}", "url": url})

    def _skip(self, url: str, why: str) -> None:
        self.manifest.setdefault("skipped_supplements", []).append({"url": url, "why": why})

    def pmc(self, pmcid: str, license_: str) -> bool:
        """The PMC open access files (XML, PDF, supplementary files); else the XML alone, from
        Europe PMC and then from `efetch`, with the supplementary files asked for on their own."""
        if not self.pmc_files(pmcid):
            if not (self.europe_pmc(pmcid) or self.efetch(pmcid)):
                return False
            self.pmc_supplements(pmcid)
        url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
        self.manifest.update(source=pmcid, url=url, license=license_)
        self.manifest["line"] = f"Full text: {pmcid} ({license_})"
        if self.manifest.get("supplements_offered") is False:
            self.manifest["line"] += ", supplementary files not offered by this source"
        return True

    def europe_pmc(self, pmcid: str) -> bool:
        xml = self._try(f"{EUROPE_PMC}/{pmcid}/fullTextXML")
        if xml.status != 200 or b"<body" not in xml.body:
            if xml.status == 200:
                self.tried[-1]["outcome"] += ", no full text"
            return False
        self._save(xml, ".xml")
        return True

    def efetch(self, pmcid: str) -> bool:
        """NCBI `efetch`: it serves the body of PMC articles outside the open access files,
        and answers an article with no body (the front matter alone) when it serves none."""
        xml = self._try(f"{EFETCH}?db=pmc&id={pmcid}&rettype=xml")
        if xml.status != 200 or b"<body" not in xml.body:
            if xml.status == 200:
                self.tried[-1]["outcome"] += ", no full text"
            return False
        self._save(xml, ".xml")
        return True

    def pmc_supplements(self, pmcid: str) -> None:
        """Europe PMC's supplementary files service (a zip), the only source for them once the
        text comes from `fullTextXML` or `efetch`. It is slow, so it is asked once, here."""
        r = self._try(f"{EUROPE_PMC}/{pmcid}/supplementaryFiles")
        offered = r.status == 200 and r.body[:2] == b"PK"
        self.manifest["supplements_offered"] = offered
        if offered:
            self._supplement(
                f"{pmcid}.zip", r.body, r.url or f"{EUROPE_PMC}/{pmcid}/supplementaryFiles"
            )
        else:
            self._skip(f"{EUROPE_PMC}/{pmcid}/supplementaryFiles", f"{_outcome(r)}, none offered")

    def pmc_files(self, pmcid: str) -> bool:
        listing = self._try(f"{PMC_AWS}/?list-type=2&prefix={pmcid}.")
        keys = re.findall(r"<Key>([^<]+)</Key>", listing.body.decode(errors="replace"))
        if not keys:
            if listing.status == 200:
                self.tried[-1]["outcome"] += ", not in the PMC open access files"
            return False
        # The latest version of the article: PMC123.2/ after PMC123.1/.
        version = max({k.split("/")[0] for k in keys}, key=lambda v: int(v.split(".")[1]))
        files = {k.split("/")[1] for k in keys if k.startswith(f"{version}/")}
        xml = self._try(f"{PMC_AWS}/{version}/{version}.xml")
        if xml.status != 200 or b"<body" not in xml.body:
            return False
        self._save(xml, ".xml")
        if f"{version}.pdf" in files:
            pdf = self.get(f"{PMC_AWS}/{version}/{version}.pdf")
            if pdf.status == 200 and _is_pdf(pdf):
                (self.out / f"{self.pmid}.pdf").write_bytes(pdf.body)
                self.manifest["pdf"] = f"{self.pmid}.pdf"
        for name in supplementary_files(xml.body):
            link = f"{PMC_AWS}/{version}/{quote(name)}"
            if why := _left_out(name):
                self._skip(link, why)
            elif name not in files:
                self._skip(link, "not in the PMC open access files")
            elif (r := self.get(link)).status == 200:
                self._supplement(_safe_name(name, self.taken), r.body, link)
            else:
                self._skip(link, _outcome(r))
        return True

    def unpaywall(self, doi: str) -> list[dict[str, Any]]:
        """Unpaywall's open access copies, in its own order (best first). It answers only a
        request that carries an address, so it is asked only when one is configured."""
        email = _setting("UNPAYWALL_EMAIL")
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

    def crossref(self, doi: str) -> list[dict[str, Any]]:
        """The full-text links the publisher declares to Crossref, text mining first."""
        record = _json(self.get, f"{CROSSREF}/{quote(doi)}")
        message = cast(dict[str, Any], (record or {}).get("message") or {})
        links = cast(list[dict[str, Any]], message.get("link") or [])
        links.sort(key=lambda x: x.get("intended-application") != "text-mining")
        return [
            {
                "is_oa": True,
                "landing_page_url": None
                if "pdf" in (x.get("content-type") or "")
                else x.get("URL"),
                "pdf_url": x.get("URL") if "pdf" in (x.get("content-type") or "") else None,
                "license": "no license given",
                "source": {"display_name": "the publisher (Crossref)"},
            }
            for x in links
            if x.get("URL")
        ]

    def open_access(self, work: dict[str, Any], doi: str | None) -> bool:
        """The publisher's copy first, then the others, best first; each time the HTML full
        texts first, then the PDFs. OpenAlex's version labels are not reliable enough to sort
        on (a bioRxiv copy labelled accepted, PMC copies labelled submitted), so the three
        sources of locations are taken in their own order, OpenAlex first."""
        best = work.get("best_oa_location")
        locations = [best] if best else []
        locations += [x for x in _locations(work) if x.get("is_oa") and x != best]
        if doi:
            locations += self.unpaywall(doi) + self.crossref(doi)
        kept: list[dict[str, Any]] = []
        seen: set[str] = set()
        for location in locations:
            key = f"{location.get('landing_page_url')}|{location.get('pdf_url')}"
            if _is_pmc(location.get("landing_page_url")) or _is_preprint(location) or key in seen:
                continue
            seen.add(key)
            kept.append(location)
        locations = kept
        doi = (f"https://doi.org/{doi}" if doi else "").lower()
        publisher = [x for x in locations if (x.get("landing_page_url") or "").lower() == doi]
        others = [x for x in locations if x not in publisher]
        for tier in (publisher, others):
            for location in tier:
                url = location.get("landing_page_url")
                if url and self.html(url, location):
                    return True
            for location in tier:
                for url in (location.get("pdf_url"), location.get("landing_page_url")):
                    if url and self.pdf(url, location):
                        return True
        return False

    def _source(self, url: str, location: dict[str, Any]) -> None:
        venue = cast(dict[str, Any], location.get("source") or {})
        source = venue.get("display_name") or urlparse(url).netloc
        license_ = location.get("license") or "no license given"
        self.manifest.update(source=source, url=url, license=license_)
        self.manifest["line"] = f"Full text: {source} ({license_}, {url})"

    def html(self, url: str, location: dict[str, Any]) -> bool:
        if any(t["url"] == url for t in self.tried):
            return False
        r = self._try(url)
        if r.status != 200 or r.content_type not in ("text/html", "application/xhtml+xml"):
            return False
        if (words := _words(r.body)) < FULL_TEXT_WORDS:
            self.tried[-1]["outcome"] += f", {words} words: not a full text"
            return False
        self._save(r, ".html")
        self._source(url, location)
        for link in supplement_links(r.body, r.url):
            if why := _left_out(urlparse(link).path):
                self._skip(link, why)
                continue
            s = self.get(link)
            if s.content_type.startswith(("image/", "video/")):  # a link that named no type
                self._skip(link, s.content_type.split("/")[0])
            elif s.status == 200 and s.content_type != "text/html":
                name = _file_name(link, self.taken)
                if Path(name).suffix.lower() not in SUPPLEMENT_SUFFIXES:
                    name += mimetypes.guess_extension(s.content_type) or ""
                self._supplement(name, s.body, link)
            else:
                self._skip(link, _outcome(s) if s.status != 200 else "an HTML page")
        return True

    def pdf(self, url: str, location: dict[str, Any]) -> bool:
        if any(t["url"] == url and t["outcome"] != "HTTP 200" for t in self.tried):
            return False
        r = self._try(url)
        if r.status != 200 or not _is_pdf(r):
            if r.status == 200:
                self.tried[-1]["outcome"] += ", not a PDF"
            return False
        self._save(r, ".pdf")
        self._source(url, location)
        return True

    def run(self) -> dict[str, Any]:
        self.out.mkdir(parents=True, exist_ok=True)
        query = quote(f"EXT_ID:{self.pmid} AND SRC:MED")
        search = _json(self.get, f"{EUROPE_PMC}/search?query={query}&format=json&resultType=core")
        results = (search or {}).get("resultList", {}).get("result", [])
        record = cast(dict[str, Any], results[0]) if results else {}
        work = _json(self.get, f"{OPENALEX}/pmid:{self.pmid}") or {}
        ids = pmcids(record, work)
        doi = record.get("doi") or (work.get("doi") or "").removeprefix("https://doi.org/") or None
        self.manifest.update(pmcid=ids[0] if ids else None, doi=doi)
        license_ = _pmc_license(record, work)
        if not any(self.pmc(pmcid, license_) for pmcid in ids):
            start = len(self.tried)
            if not self.open_access(work, doi):
                self.manifest["why"] = self.why(work, self.tried[start:])
        if self.manifest["file"] is None:
            self.manifest["line"] = f"Full text: closed — {self.manifest['why']}"
        self.manifest["tried"] = self.tried
        path = self.out / f"{self.pmid}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)  # last: a manifest means the fetch is done
        return self.manifest

    def why(self, work: dict[str, Any], tried: list[dict[str, str]]) -> str:
        """Why there is no full text, for the `Full text: closed — ...` line of the note. The
        copies tried come first: they say what happened, where the locations say what was
        announced."""
        copies = [t for t in tried if not t["url"].startswith((UNPAYWALL, CROSSREF))]
        blocked = [t["url"] for t in copies if not t["outcome"].startswith("HTTP 200")]
        if blocked:
            return f"a copy at {blocked[0]} but download blocked"
        if copies:
            return f"a copy at {copies[0]['url']} but no full text there"
        oa = [x for x in _locations(work) if x.get("is_oa")]
        if not work:
            return "not in OpenAlex, and no copy from Unpaywall or Crossref"
        if not oa:
            return "not open access anywhere"
        if any(_is_preprint(x) for x in oa):
            return "open access only as a preprint"
        if any(_is_pmc(x.get("landing_page_url")) for x in oa):
            return "open access only in PMC, outside its open access files"
        return "open access, but no copy to download"


def fetch(pmid: int, out: Path, get: Get = http_get) -> dict[str, Any]:
    return Fetch(pmid, out, get).run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the full text of a publication.")
    parser.add_argument("pmid", type=int)
    parser.add_argument("dir", type=Path)
    args = parser.parse_args()
    print(fetch(args.pmid, args.dir)["line"])

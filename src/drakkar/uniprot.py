"""Upgrade the Drakkar proteins to a new UniProt release.

Python port of drakkar-uniprot (`bin/proteins`, `bin/metadata`, `bin/import/proteins`), reading
the UniProt FTP files instead of website search results:

- `uniprot_sprot_human.xml.gz` (human, Swiss-Prot), `uniprot_sprot_viruses.xml.gz` and
  `uniprot_trembl_viruses.xml.gz` (all viruses), `uniprot_sprot_varsplic.fasta.gz` (isoforms).

Two steps:

1. `parse`: each XML file is converted into a TSV file next to it (one row per entry).
2. `upgrade`: the TSV files are staged, then, in one transaction:
   - an entry whose existing snapshot is unchanged (same accession, taxon and isoform sequences,
     and for human the same gene name) keeps it; any other entry gets a new `proteins` row;
   - `proteins_versions` is rebuilt: one row per entry of the release, pointing to its snapshot;
   - a Markdown report lists what changed and the descriptions that need a revision.

Unlike the Perl import, entries whose taxon is missing from `taxon` are imported (and reported)
instead of silently skipped: the type (human or viral) comes from the file.
"""

import argparse
import csv
import gzip
import json
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
from typing import Any, LiteralString

from lxml import etree
from lxml.etree import _Element  # pyright: ignore[reportPrivateUsage]

from drakkar.db import connect

HUMAN_TAXON_ID = 9606
VIRUSES_TAXON_ID = 10239
VARSPLIC = "uniprot_sprot_varsplic.fasta.gz"
SOURCES = {
    "uniprot_sprot_human.xml.gz": "h",
    "uniprot_sprot_viruses.xml.gz": "v",
    "uniprot_trembl_viruses.xml.gz": "v",
}
COLUMNS = (
    "accession",
    "secondary_accessions",
    "reviewed",
    "type",
    "ncbi_taxon_id",
    "name",
    "description",
    "sequences",
    "names",
    "features",
)

csv.field_size_limit(sys.maxsize)


def log(start: float, message: str) -> None:
    print(f"[{time.time() - start:7.1f}s] {message}", file=sys.stderr, flush=True)


# --- parse ------------------------------------------------------------------------------------


def read_isoforms(path: Path) -> dict[str, dict[str, str]]:
    """Return {canonical accession: {isoform accession: sequence}} from the varsplic FASTA."""
    isoforms: dict[str, dict[str, str]] = {}
    accession = ""
    chunks: list[str] = []

    def flush() -> None:
        if accession:
            isoforms.setdefault(accession.split("-")[0], {})[accession] = "".join(chunks)

    with gzip.open(path, "rt") as f:
        for line in f:
            if line.startswith(">"):
                flush()
                accession = line.split("|")[1]
                chunks = []
            else:
                chunks.append(line.strip())
    flush()
    return isoforms


@dataclass
class Entry:
    accession: str
    secondary_accessions: list[str]
    reviewed: bool
    type: str
    ncbi_taxon_id: int
    name: str
    description: str
    sequences: dict[str, str]
    names: list[str]
    features: list[dict[str, Any]]

    def row(self) -> tuple[str, ...]:
        return (
            self.accession,
            json.dumps(self.secondary_accessions),
            "t" if self.reviewed else "f",
            self.type,
            str(self.ncbi_taxon_id),
            self.name,
            self.description,
            json.dumps(self.sequences),
            json.dumps(self.names),
            json.dumps(self.features),
        )


def parse_entry(entry: _Element, ns: str, type: str, isoforms: dict[str, dict[str, str]]) -> Entry:
    accessions = [a.text or "" for a in entry.iterfind(f"{ns}accession")]
    accession = accessions[0]

    # All gene names, in order (proteins_versions.names). The protein name is the first gene
    # name as in the UniProt FASTA header (GN=): primary, else ordered locus, else ORF.
    genes = [(n.get("type"), n.text or "") for g in entry.iterfind(f"{ns}gene") for n in g]
    names = [name for _, name in genes if name != "null"]
    name = "N/A"
    for kind in ("primary", "ordered locus", "ORF"):
        first = next((n for t, n in genes if t == kind and n != "null"), None)
        if first is not None:
            name = first
            break

    protein = entry.find(f"{ns}protein")
    description = ""
    if protein is not None:
        for kind in ("recommendedName", "submittedName"):
            full_name = protein.find(f"{ns}{kind}/{ns}fullName")
            if full_name is not None:
                description = full_name.text or ""
                break

    taxon = entry.find(f"{ns}organism/{ns}dbReference[@type='NCBI Taxonomy']")
    assert taxon is not None, accession

    sequence = entry.find(f"{ns}sequence")
    assert sequence is not None, accession
    if sequence.get("fragment"):
        description += " (Fragment)"  # as in the UniProt FASTA header
    sequences = {accession: "".join((sequence.text or "").split())}
    sequences.update(isoforms.get(accession, {}))

    # Features on the canonical sequence with a begin and an end position, as in the Perl
    # metadata import (single-position features are skipped).
    features: list[dict[str, Any]] = []
    for feature in entry.iterfind(f"{ns}feature"):
        location = feature.find(f"{ns}location")
        if location is None or location.get("sequence", accession) != accession:
            continue
        begin = location.find(f"{ns}begin")
        end = location.find(f"{ns}end")
        begin_position = begin.get("position") if begin is not None else None
        end_position = end.get("position") if end is not None else None
        if not (feature.get("type") and begin_position and end_position):
            continue
        features.append(
            {
                "type": feature.get("type"),
                "start": int(begin_position),
                "stop": int(end_position),
                "description": feature.get("description", ""),
            }
        )

    return Entry(
        accession=accession,
        secondary_accessions=accessions[1:],
        reviewed=entry.get("dataset") == "Swiss-Prot",
        type=type,
        ncbi_taxon_id=int(taxon.get("id", "0")),
        name=name,
        description=description,
        sequences=sequences,
        names=names or ["N/A"],
        features=features,
    )


def parse_xml(path: Path, type: str, isoforms: dict[str, dict[str, str]]) -> Iterator[Entry]:
    with gzip.open(path, "rb") as f:
        for _, element in etree.iterparse(f, events=("end",), tag="{*}entry", huge_tree=True):
            ns = element.tag[: -len("entry")]
            yield parse_entry(element, ns, type, isoforms)
            element.clear()
            while element.getprevious() is not None:
                parent = element.getparent()
                assert parent is not None
                del parent[0]


def tsv_path(directory: Path, source: str) -> Path:
    return directory / source.replace(".xml.gz", ".tsv.gz")


def parse_one(args: tuple[Path, str]) -> tuple[str, int]:
    directory, source = args
    isoforms = read_isoforms(directory / VARSPLIC)
    output = tsv_path(directory, source)
    partial = output.with_suffix(".partial")
    n = 0
    with gzip.open(partial, "wt", compresslevel=1, newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(COLUMNS)
        for entry in parse_xml(directory / source, SOURCES[source], isoforms):
            writer.writerow(entry.row())
            n += 1
    partial.rename(output)
    return source, n


def parse(directory: Path) -> None:
    start = time.time()
    todo = [(directory, s) for s in SOURCES if not tsv_path(directory, s).exists()]
    for source in SOURCES:
        if (directory, source) not in todo:
            log(start, f"{source}: already parsed")
    with Pool(len(todo) or 1) as pool:
        for source, n in pool.imap_unordered(parse_one, todo):
            log(start, f"{source}: {n} entries")


# --- upgrade ----------------------------------------------------------------------------------


def stage(cur: Any, directory: Path, start: float) -> None:
    cur.execute("""
        CREATE TEMP TABLE staging (
            accession varchar(10) PRIMARY KEY,
            secondary_accessions varchar[] NOT NULL,
            reviewed boolean NOT NULL,
            type char(1) NOT NULL,
            ncbi_taxon_id integer NOT NULL,
            name varchar NOT NULL,
            description text NOT NULL,
            sequences jsonb NOT NULL,
            names varchar[] NOT NULL,
            features jsonb NOT NULL
        ) ON COMMIT DROP
    """)
    for source in SOURCES:
        path = tsv_path(directory, source)
        with (
            gzip.open(path, "rt", newline="") as f,
            cur.copy(f"COPY staging ({', '.join(COLUMNS)}) FROM STDIN") as copy,
        ):
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for row in reader:
                row[1] = json.loads(row[1])
                row[8] = json.loads(row[8])
                copy.write_row(row)
        log(start, f"staged {path.name}")
    cur.execute("ANALYZE staging")


REPORT_QUERIES: dict[str, LiteralString] = {
    "entries": """
        SELECT s.type, s.reviewed, count(*) AS entries,
               count(*) FILTER (WHERE m.id IS NOT NULL) AS unchanged,
               count(*) FILTER (WHERE m.id IS NULL AND NOT EXISTS (
                   SELECT 1 FROM proteins AS p WHERE p.accession = s.accession
               )) AS new_accessions,
               count(*) FILTER (WHERE m.id IS NULL AND EXISTS (
                   SELECT 1 FROM proteins AS p WHERE p.accession = s.accession
               )) AS changed
        FROM staging AS s LEFT JOIN matched AS m USING (accession)
        GROUP BY 1, 2 ORDER BY 1, 2
    """,
    "missing_taxa": """
        SELECT s.type, count(*) AS entries, count(DISTINCT s.ncbi_taxon_id) AS taxa
        FROM staging AS s
        WHERE NOT EXISTS (SELECT 1 FROM taxon AS t WHERE t.ncbi_taxon_id = s.ncbi_taxon_id)
        GROUP BY 1 ORDER BY 1
    """,
}


def fetch_table(cur: Any, sql: LiteralString) -> tuple[list[str], list[tuple[Any, ...]]]:
    cur.execute(sql)
    return [c.name for c in cur.description], cur.fetchall()


def upgrade(release: str, directory: Path, *, dry_run: bool) -> None:
    start = time.time()
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM proteins WHERE version = %s LIMIT 1", (release,))
        if cur.fetchone():
            sys.exit(f"release {release} is already in proteins")

        stage(cur, directory, start)

        log(start, "matching unchanged snapshots")
        cur.execute("""
            CREATE TEMP TABLE matched ON COMMIT DROP AS
            SELECT DISTINCT ON (s.accession) s.accession, p.id, p.version
            FROM staging AS s
            JOIN proteins AS p
              ON p.accession = s.accession
             AND p.ncbi_taxon_id = s.ncbi_taxon_id
             AND p.sequences = s.sequences
             AND (s.type = 'v' OR p.name = s.name)
            ORDER BY s.accession, p.id DESC
        """)
        cur.execute("ALTER TABLE matched ADD PRIMARY KEY (accession)")
        report: dict[str, list[tuple[Any, ...]]] = {}
        headers: dict[str, list[str]] = {}
        for key, sql in REPORT_QUERIES.items():
            headers[key], report[key] = fetch_table(cur, sql)

        log(start, "inserting new snapshots")
        cur.execute(
            """
            INSERT INTO proteins
                (type, ncbi_taxon_id, accession, name, description, version, sequences)
            SELECT s.type, s.ncbi_taxon_id, s.accession, s.name, s.description, %s, s.sequences
            FROM staging AS s
            WHERE NOT EXISTS (SELECT 1 FROM matched AS m WHERE m.accession = s.accession)
            """,
            (release,),
        )
        log(start, f"{cur.rowcount} snapshots inserted")

        log(start, "rebuilding proteins_versions")
        cur.execute("DELETE FROM proteins_versions")
        cur.execute(
            """
            INSERT INTO proteins_versions (accession, version, current_version, names, features)
            SELECT s.accession, coalesce(m.version, %s), %s, s.names, s.features
            FROM staging AS s LEFT JOIN matched AS m USING (accession)
            """,
            (release, release),
        )
        log(start, f"{cur.rowcount} current snapshots")
        cur.execute("""
            UPDATE proteins_versions AS v
            SET search = concat_ws(' ', p.accession, array_to_string(v.names, ' '), tn.name,
                                   p.description)
            FROM proteins AS p
            LEFT JOIN taxon AS t ON t.ncbi_taxon_id = p.ncbi_taxon_id
            LEFT JOIN taxon_name AS tn
              ON tn.taxon_id = t.taxon_id AND tn.name_class = 'scientific name'
            WHERE p.accession = v.accession AND p.version = v.version
        """)

        log(start, "listing descriptions on obsolete snapshots")
        cur.execute("""
            CREATE TEMP TABLE secondary ON COMMIT DROP AS
            SELECT unnest(secondary_accessions) AS secondary_accession, accession FROM staging
        """)
        cur.execute("CREATE INDEX ON secondary (secondary_accession)")
        cur.execute("""
            CREATE TEMP TABLE obsolete_uses ON COMMIT DROP AS
            SELECT d.stable_id, a.pmid, r.type AS run_type, x.side, p.type, p.accession,
                   p.version AS old_version, s.accession IS NOT NULL AS in_release,
                   CASE
                     WHEN s.accession IS NULL THEN 'removed'
                     WHEN p.ncbi_taxon_id <> s.ncbi_taxon_id THEN 'taxon'
                     WHEN p.sequences->>p.accession <> s.sequences->>s.accession
                       THEN 'canonical sequence'
                     WHEN p.sequences <> s.sequences THEN 'isoforms'
                     ELSE 'gene name'
                   END AS reason,
                   (SELECT string_agg(x.accession, ' ') FROM secondary AS x
                    WHERE x.secondary_accession = p.accession) AS now_secondary_of
            FROM descriptions AS d
            JOIN associations AS a ON a.id = d.association_id
            JOIN runs AS r ON r.id = a.run_id
            CROSS JOIN LATERAL (VALUES (1, d.protein1_id), (2, d.protein2_id)) AS x (side, id)
            JOIN proteins AS p ON p.id = x.id
            LEFT JOIN staging AS s ON s.accession = p.accession
            WHERE d.deleted_at IS NULL
            AND NOT EXISTS (
                SELECT 1 FROM proteins_versions AS v
                WHERE v.accession = p.accession AND v.version = p.version
            )
        """)
        headers["obsolete"], report["obsolete"] = fetch_table(
            cur,
            """
            SELECT run_type, type, reason, count(DISTINCT stable_id) AS descriptions,
                   count(DISTINCT accession) AS accessions,
                   count(DISTINCT accession) FILTER (WHERE now_secondary_of IS NOT NULL)
                     AS now_secondary
            FROM obsolete_uses GROUP BY 1, 2, 3 ORDER BY 1, 2, 4 DESC
            """,
        )
        details_header, details = fetch_table(
            cur,
            """
            SELECT stable_id, pmid, side, accession, old_version, reason,
                   coalesce(now_secondary_of, '') AS now_secondary_of
            FROM obsolete_uses WHERE run_type = 'vh' ORDER BY reason, accession, stable_id
            """,
        )

        write_report(directory / "report.md", release, dry_run, headers, report)
        with (directory / "obsolete_vh_descriptions.tsv").open("w") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(details_header)
            writer.writerows(details)

        if dry_run:
            conn.rollback()
            log(start, "dry run: rolled back")
        else:
            conn.commit()
            log(start, "committed")
            conn.execute("REFRESH MATERIALIZED VIEW dataset")
            conn.commit()
            log(start, "dataset refreshed")


def write_report(
    path: Path,
    release: str,
    dry_run: bool,
    headers: dict[str, list[str]],
    report: dict[str, list[tuple[Any, ...]]],
) -> None:
    titles = {
        "entries": "Entries of the release",
        "missing_taxa": "Entries whose taxon is missing from `taxon` (imported anyway)",
        "obsolete": "Live descriptions on snapshots made obsolete (to revise)",
    }
    lines = [f"# UniProt upgrade to {release}{' (dry run)' if dry_run else ''}", ""]
    for key, title in titles.items():
        lines += [f"## {title}", ""]
        lines.append("| " + " | ".join(headers[key]) + " |")
        lines.append("|" + "---|" * len(headers[key]))
        lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in report[key]]
        lines.append("")
    path.write_text("\n".join(lines))
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade the proteins to a new UniProt release.")
    commands = parser.add_subparsers(dest="command", required=True)
    parse_parser = commands.add_parser("parse", help="convert the XML files into TSV files")
    parse_parser.add_argument("directory", type=Path)
    upgrade_parser = commands.add_parser("upgrade", help="import the TSV files")
    upgrade_parser.add_argument("release", help="UniProt release, e.g. 2026_03")
    upgrade_parser.add_argument("directory", type=Path)
    upgrade_parser.add_argument("--dry-run", action="store_true", help="roll back at the end")
    args = parser.parse_args()
    if args.command == "parse":
        parse(args.directory)
    else:
        upgrade(args.release, args.directory, dry_run=args.dry_run)

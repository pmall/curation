"""The read views: what a decision needs, from the test database."""

import subprocess

from drakkar.read import Page, entries, entry, methods, names, search, seq, taxa


def _command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", "drakkar-read", *args], capture_output=True, text=True)


def test_methods(conn):
    """By name or synonym, case aside, many texts at once, with the detection flag; the closest
    names first, a list cut at its limit ending with how many there are; each word of the text
    in one name, punctuation aside."""
    lines = methods(conn.cursor(), ["coimmuno", "Co-IP", "western blot"]).splitlines()
    assert lines[0] == "#text\tpsimi_id\tname (synonym matched)\tis_detection\tlive_descriptions"
    assert "coimmuno\tMI:0019\tcoimmunoprecipitation\tyes\t3" in lines
    assert "Co-IP\tMI:0019\tcoimmunoprecipitation (Co-IP)\tyes\t3" in lines
    assert "western blot\tMI:0113\twestern blot\tno\t0" in lines
    first = methods(conn.cursor(), ["two hybrid"], Page(3)).splitlines()
    assert first[1] == "two hybrid\tMI:0018\ttwo hybrid\tyes\t90"  # the exact name first
    assert len(first) == 1 + 3 + 1 and first[-1] == "two hybrid\t… 3 of 17"
    words = methods(conn.cursor(), ["biolayer interferometry", "pulldown"]).splitlines()
    assert words[1:] == [
        "biolayer interferometry\tMI:0969\tbio-layer interferometry\tyes\t0",
        "pulldown\tMI:0096\tpull down\tyes\t10",
    ]


def test_taxon(conn):
    """By any of its names, case aside, with the taxa above it up to its family."""
    lines = taxa(conn.cursor(), ["cuhk", "Rabies"]).splitlines()
    assert lines[0] == "#text\ttaxon (name matched)\trank\tlineage"
    assert lines[1].startswith(
        "cuhk\t239241 SARS coronavirus CUHK-AG01\tno rank\t"
        "694009 Severe acute respiratory syndrome-related coronavirus < "
    )
    assert lines[1].endswith(" < 11118 Coronaviridae")
    assert (
        "Rabies\t11292 Lyssavirus rabies\tspecies\t"
        "11286 Lyssavirus < 2842407 Alpharhabdovirinae < 11270 Rhabdoviridae"
    ) in lines


def test_entry(conn):
    """Its lineage with the IDs, its chains; many at once, a secondary accession followed."""
    text = entry(conn.cursor(), "P26662")
    assert "- 810-1026 chain: Protease NS2" in text
    assert "viral, taxon 11116 Hepatitis C virus (isolate Japanese) < 31647 " in text
    assert (
        "< 3052230 Orthohepacivirus hominis < 11102 Orthohepacivirus < 3700683 Hepaciviridae\n"
        in text
    )
    secondary = entry(conn.cursor(), "O00297")
    assert secondary.startswith("# O00297 is a secondary accession of O00499\n# O00499: ")
    both = entries(conn.cursor(), ["P26662", "X1"])
    assert both.startswith("# P26662: ")
    assert both.endswith("\n\n# X1: no snapshot, and no current entry holds it as secondary")


def test_search(conn):
    """By the `search` text, case aside, several texts, Swiss-Prot first; under a taxon, its
    whole subtree."""
    lines = search(conn.cursor(), ["brf1", "nothing such"]).splitlines()
    assert lines == [
        "#text\taccession\tdb\tgene\tprotein\ttaxon\tlength",
        "brf1\tQ92994\tSP\tBRF1\tTranscription factor IIIB 90 kDa subunit\t9606 Homo sapiens\t677",
        "nothing such\t(none)",
    ]
    dbs = [line.split("\t")[2] for line in search(conn.cursor(), ["protein"]).splitlines()[1:-1]]
    assert dbs == sorted(dbs)  # Swiss-Prot first
    under = search(conn.cursor(), ["Uncharacterized"], taxon=694009, page=Page(3)).splitlines()
    assert (
        "Uncharacterized\tQ6VA95\tTR\tN/A\tUncharacterized protein\t"
        "239241 SARS coronavirus CUHK-AG01\t63"
    ) in under
    assert under[-1] == "Uncharacterized\t… 3 of 5"
    assert search(conn.cursor(), ["brf1"], taxon=694009).splitlines()[1] == "brf1\t(none)"


def test_seq(conn):
    lines = seq(conn.cursor(), ["P0C6X7:1-20", "Q6VA95", "P0C6X7:8000-8001"]).splitlines()
    assert lines[0] == "#location\tsequence"
    assert lines[1] == "P0C6X7:1-20\tMESLVLGVNEKTHVQLSLPV"
    assert lines[2].startswith("Q6VA95\tMFHLVDFQVT") and len(lines[2].split("\t")[1]) == 63
    assert lines[3] == "P0C6X7:8000-8001\t8000-8001 is outside 1-7073"


def test_names(conn):
    """Under each taxon, its whole subtree: the most used names first, with their three most
    used interactors; an obsolete snapshot marked."""
    lines = names(conn.cursor(), [239241, 694009], Page(3)).splitlines()
    assert lines == [
        "#taxon\tgeneric_name\tlive_descriptions\tinteractors (live descriptions)",
        "239241\torf3b\t3\tQ6VA98:1-154 (3)",
        "239241\tN\t2\tQ6VA95:1-63 (2)",
        "239241\torf7a\t2\tQ6VA94:1-122 (2)",
        "694009\tnsp3\t19\tP0C6U8:819-2740 (8), P0C6X7:819-2740 (5), D3W8N4:1-1922 (4), 1 more",
        "694009\tN\t13\tP59595:1-422 (7), Q3I5I7:1-421 (4), Q6VA95:1-63 (2)",
        "694009\tnsp12\t11\tP0C6X7:4370-5301 (11)",
        "694009\t… 3 of 20",
    ]
    every = names(conn.cursor(), [3418604], Page(100)).splitlines()
    assert "3418604\tnsp15\t1\tQ6SRE2:1-312 obsolete (1)" in every


def test_a_taxon_is_given_by_its_id(dbname):
    result = _command("names", "SARS coronavirus CUHK-AG01")
    assert result.returncode == 2 and "invalid int value" in result.stderr


def test_sql_is_guarded(dbname):
    """Every row, long cells cut; a limit required, and more rows than it refused; a write
    refused."""
    query = "SELECT accession, sequences FROM proteins ORDER BY id LIMIT 2"
    result = _command("sql", query, "--limit", "2")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "#accession\tsequences" and len(lines) == 1 + 2
    assert all(len(line) < 300 for line in lines) and "chars)" in result.stdout
    assert _command("sql", query).returncode == 2  # no --limit
    result = _command("sql", "SELECT accession FROM proteins", "--limit", "2")
    assert result.returncode == 1 and result.stdout == ""
    assert "more than 2 rows, none printed" in result.stderr
    result = _command(
        "sql", "UPDATE methods SET name = 'x' WHERE psimi_id = 'MI:0018'", "--limit", "1"
    )
    assert result.returncode == 1 and "read-only transaction" in result.stderr

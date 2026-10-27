"""The read views: what a decision needs, from the test database."""

import subprocess

from drakkar.read import (
    Page,
    closest,
    entries,
    entry,
    methods,
    names,
    search,
    seq,
    sequence_of,
    taxa,
)


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
    assert len(first) == 1 + 3 + 1
    assert first[-1] == "two hybrid\t… 3 of 17 shown, cut by --limit 3"
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
    """Its lineage with the IDs, its chains and regions, its generic names; many at once, a
    secondary accession followed."""
    text = entry(conn.cursor(), "P26662")
    assert "- 810-1026 chain: Protease NS2" in text
    assert "- 2-75 region: Disordered" in text
    assert "viral, taxon 11116 Hepatitis C virus (isolate Japanese) < 31647 " in text
    assert (
        "< 3052230 Orthohepacivirus hominis < 11102 Orthohepacivirus < 3700683 Hepaciviridae\n"
        in text
    )
    assert "\nGeneric names (live descriptions):\n- 810-1026 NS2-3 (" in text
    assert "Generic names" not in entry(conn.cursor(), "Q14258")  # human
    secondary = entry(conn.cursor(), "sp|O00297|BIN1_HUMAN")
    assert secondary.startswith("# O00297 is a secondary accession of O00499\n# O00499: ")
    assert entry(conn.cursor(), "o00499-2").startswith("# o00499-2 is an isoform of O00499\n")
    obsolete = entry(conn.cursor(), "Q6SRE2")  # obsolete snapshots only: never shown
    assert obsolete == "# Q6SRE2: no current entry has this accession, current or old"
    both = entries(conn.cursor(), ["P26662;", "X1", "Q9Y6K9"])
    assert both.startswith("# P26662: ")
    assert both.endswith(
        "\n\n# X1: not an accession"
        "\n\n# Q9Y6K9: no current entry has this accession, current or old"
    )


def test_search(conn):
    """By the `search` text, case aside, several texts, Swiss-Prot first; under a taxon, its
    whole subtree."""
    lines = search(conn.cursor(), ["brf1", "nothing such"]).splitlines()
    assert lines == [
        "#text\taccession\tother_accessions\tdb\tgene\tprotein\ttaxon\tlength",
        f"brf1\tQ92994\t{BRF1_OLD}\tSP\tBRF1\tTranscription factor IIIB 90 kDa subunit\t"
        "9606 Homo sapiens\t677",
        "nothing such\t(none)",
    ]
    dbs = [line.split("\t")[3] for line in search(conn.cursor(), ["protein"]).splitlines()[1:-1]]
    assert dbs == sorted(dbs)  # Swiss-Prot first
    under = search(conn.cursor(), ["Uncharacterized"], taxon=694009, page=Page(3)).splitlines()
    assert (
        "Uncharacterized\tQ6VA95\t-\tTR\tN/A\tUncharacterized protein\t"
        "239241 SARS coronavirus CUHK-AG01\t63"
    ) in under
    assert under[-1] == "Uncharacterized\t… 3 of 5 shown, cut by --limit 3"
    assert search(conn.cursor(), ["brf1"], taxon=694009).splitlines()[1] == "brf1\t(none)"


BRF1_OLD = (
    "B3KU36,B4DIG5,B7Z2N3,F5H5Z7,F8WA46,Q13223,Q3SYD9,Q5PR24,Q6IQ02,Q96KX3,Q9HCW6,Q9HCW7,Q9HCW8"
)


def test_search_accessions_as_written(conn):
    """An accession as publications write it gives its current entry: a UniProt ID, a group one
    by one, an isoform's, a version, an old accession, case aside; an accession of no entry,
    none."""
    texts = ["sp|Q92994|BRF1_HUMAN", "o00297; Q92994", "O00499-2", "Q92994.1", "Q9Y6K9"]
    found = [line.split("\t")[:2] for line in search(conn.cursor(), texts).splitlines()[1:]]
    assert found == [
        ["sp|Q92994|BRF1_HUMAN", "Q92994"],
        ["o00297", "O00499"],
        ["Q92994", "Q92994"],
        ["O00499-2", "O00499"],
        ["Q92994.1", "Q92994"],
        ["Q9Y6K9", "(none)"],
    ]
    assert search(conn.cursor(), ["O00297"]).splitlines()[1].split("\t")[2].startswith("O00297,")


SARS = "694009 Severe acute respiratory syndrome-related coronavirus"


def test_closest(conn):
    """The entries of the taxon subtree by the score of their best isoform, Swiss-Prot first
    among equals, an accession or a sequence as query, as `search` shows them; every entry
    counted."""
    lines = closest(conn.cursor(), ["P0C6X7:1-20", "MESLVLGVNE"], 694009, Page(3)).splitlines()
    assert lines[:5] == [
        "#sequence\taccession\tother_accessions\tdb\tgene\tprotein\ttaxon\tlength"
        "\tidentity\tcoverage\tregion",
        f"P0C6X7:1-20\tP0C6U8\tP59641\tSP\t1a\tReplicase polyprotein 1a\t{SARS}\t4382"
        "\t100.0 %\t100.0 %\t1-20",
        "P0C6X7:1-20\tP0C6X7\tP59641,Q6WGN0,Q7T697,Q808C0,Q80BV7,Q80BV8,Q80E51\tSP\trep"
        f"\tReplicase polyprotein 1ab\t{SARS}\t7073\t100.0 %\t100.0 %\t1-20",
        "P0C6X7:1-20\tP0C6W6\tQ3I5J6,Q3I5J7\tSP\trep\tReplicase polyprotein 1ab"
        "\t349344 Bat SARS CoV Rp3/2004\t7071\t95.0 %\t100.0 %\t1-20",
        "P0C6X7:1-20\t… 3 of 18 shown, cut by --limit 3",
    ]
    unread = closest(conn.cursor(), ["X1", "MESLVLGVNE", "NS-protease"], 694009).splitlines()
    assert unread[-2:] == [
        "X1\tX1 has no current snapshot",
        "NS-protease\tneither an accession nor an amino acid sequence",
    ]
    spaced = closest(conn.cursor(), ["MESLVLGVNE\n", "MESLVLGVNE KTHVQLSLPV"], 694009)
    assert spaced.splitlines()[1:] == [
        "MESLVLGVNE\tleading or trailing whitespace around the argument",
        "MESLVLGVNE KTHVQLSLP…(21 characters)\t2 parts separated by whitespace: one sequence "
        "per argument",
    ]


def test_closest_identity_counts_the_gaps(conn):
    """A residue deleted from the query: one gap column among the aligned columns."""
    query = sequence_of(conn.cursor(), "P0C6X7:1-41")
    gapped = query[:20] + query[21:]  # 40 residues, 41 columns
    line = closest(conn.cursor(), [gapped], 694009, Page(1)).splitlines()[1]
    fields = line.split("\t")
    assert [fields[1], *fields[-3:]] == ["P0C6U8", "97.6 %", "100.0 %", "1-41"]


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
        "694009\t… 3 of 20 shown, cut by --limit 3",
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

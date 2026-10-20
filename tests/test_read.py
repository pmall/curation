"""The read views: what a decision needs, from the test database."""

import subprocess

from drakkar.read import (
    Page,
    closest,
    entry,
    map_,
    methods,
    names,
    publication,
    rows,
    search,
    seq,
    taxa,
    used,
)


def test_publication(conn):
    text = publication(conn.cursor(), 1, 22046132)
    assert "Title: The SARS-coronavirus-host interactome" in text
    assert "Abstract: Coronaviruses" in text
    assert "EY73D2C965 v1 MI:0018: BRF1 (Q92994) – N Q6VA95[1-63]" in text


def test_entry_lists_the_chains(conn):
    text = entry(conn.cursor(), "P26662")
    assert "- 810-1026 chain: Protease NS2" in text
    assert "viral, taxon" in text
    assert text.endswith("Sequence: drakkar-read seq P26662[:<start>-<stop>]")  # not the sequence


def test_names(conn):
    text = names(conn.cursor(), "Q6VA95")
    assert "- `N` 2: Q6VA95[1-63] (2)" in text


def test_curation_names_leave_out_the_publication_curated(conn):
    """SARS-CoV pp1ab: `nsp12` only in PMID 22046132, `nsp1` in it and in PMID 34799561."""
    every = names(conn.cursor(), "P0C6X7")
    assert "- `nsp12` 11: P0C6X7[4370-5301] (11)" in every
    assert "- `nsp1` 9: P0C6X7[1-180] (7), P0C6U8[1-180] (2)" in every
    curation = names(conn.cursor(), "P0C6X7", exclude=22046132)
    assert "`nsp12`" not in curation
    assert "- `nsp1` 3: P0C6U8[1-180] (2), P0C6X7[1-180] (1)" in curation
    assert "- `nsp3` 13: P0C6U8[819-2740] (8), P0C6X7[819-2740] (5)" in curation


def test_curation_names_command(dbname):
    args = ["uv", "run", "drakkar-read", "curation-names", "22046132", "P0C6X7"]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "- `nsp1` 3: P0C6U8[1-180] (2), P0C6X7[1-180] (1)" in result.stdout


def test_rows(conn):
    lines = rows(conn.cursor(), ["EY73D2C965"]).splitlines()
    assert lines[0].startswith("#stable_id") and lines[1].startswith("EY73D2C965\t1\t1\t22046132")


def _command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", "drakkar-read", *args], capture_output=True, text=True)


def test_entry_by_a_secondary_accession(conn):
    text = entry(conn.cursor(), "O00297")
    assert text.startswith("# O00297 is a secondary accession of O00499\n# O00499: ")


def test_methods(conn):
    """By name or synonym, case aside, many texts at once, with the detection flag; a page of
    10 lines per text, then what is left out."""
    lines = methods(conn.cursor(), ["coimmuno", "Co-IP", "western blot"]).splitlines()
    assert lines[0] == "#text\tpsimi_id\tname (synonym matched)\tis_detection\tlive_descriptions"
    assert "coimmuno\tMI:0019\tcoimmunoprecipitation\tyes\t3" in lines
    assert (
        "co-ip\t" not in lines and "Co-IP\tMI:0019\tcoimmunoprecipitation (Co-IP)\tyes\t3" in lines
    )
    assert "western blot\tMI:0113\twestern blot\tno\t0" in lines
    first = methods(conn.cursor(), ["two hybrid"]).splitlines()
    assert first[1] == "two hybrid\tMI:0018\ttwo hybrid\tyes\t90"  # the exact name first
    assert len(first) == 1 + 10 + 1 and first[-1].startswith("two hybrid\t… 1-10 of ")
    assert "--offset 10 for the next" in first[-1]


def test_search(conn):
    """By the `search` text, case aside, several texts, Swiss-Prot first."""
    lines = search(conn.cursor(), ["brf1", "nucleoprotein", "nothing such"]).splitlines()
    assert lines[0] == "#text\taccession\tdb\tgene\tprotein\ttaxon\tlength"
    assert lines[1] == (
        "brf1\tQ92994\tSP\tBRF1\tTranscription factor IIIB 90 kDa subunit\t9606 Homo sapiens\t677"
    )
    assert "nothing such\t(none)" in lines
    assert search(conn.cursor(), ["brf1"], kind="v").splitlines()[1] == "brf1\t(none)"
    kinds = [line.split("\t")[2] for line in search(conn.cursor(), ["protein"]).splitlines()[1:-1]]
    assert kinds == sorted(kinds)  # Swiss-Prot first


def test_search_a_taxon_covers_its_subtree(conn):
    """The SARS-CoV species (694009) holds the entries of its strains, CUHK-AG01 included."""
    text = search(conn.cursor(), [], taxon="694009", page=Page(limit=None))
    assert "Q6VA95\tTR\tN/A\tUncharacterized protein\t239241 SARS coronavirus CUHK-AG01\t63" in text
    assert "P26662" not in text


def test_taxon(conn):
    """By any of its names, case aside, with its lineage; only under a taxon, when given."""
    lines = taxa(conn.cursor(), ["cuhk", "Rabies"]).splitlines()
    assert lines[0] == "#text\ttaxon\tname (name matched)\trank\tlineage"
    assert lines[1].startswith("cuhk\t239241\tSARS coronavirus CUHK-AG01\tno rank\t")
    assert lines[1].endswith("< Coronaviridae")
    assert (
        "Rabies\t11292\tLyssavirus rabies\tspecies\tLyssavirus < Alpharhabdovirinae < "
        "Rhabdoviridae" in lines
    )
    assert taxa(conn.cursor(), ["CUHK"], taxon="349344").splitlines()[1] == "CUHK\t(none)"


def test_seq(conn):
    lines = seq(conn.cursor(), ["P0C6X7:1-20", "Q6VA95", "P0C6X7:8000-8001"]).splitlines()
    assert lines[0] == "P0C6X7:1-20\tMESLVLGVNEKTHVQLSLPV"
    assert lines[1].startswith("Q6VA95\tMFHLVDFQVT") and len(lines[1].split("\t")[1]) == 63
    assert lines[2] == "P0C6X7:8000-8001\t8000-8001 is outside 1-7073"


def test_closest(conn):
    """The entries of the taxon subtree by identity, an accession or a sequence as query."""
    lines = closest(conn.cursor(), ["P0C6X7:1-20", "MESLVLGVNE"], "694009").splitlines()
    assert lines[0] == "#sequence\taccession\tdb\tprotein\ttaxon\tidentity\tregion"
    first = [line.split("\t")[1] for line in lines if line.startswith("P0C6X7:1-20\t")]
    assert first[:3] == ["P0C6U8", "P0C6X7", "P0C6W6"]
    best = closest(conn.cursor(), ["P0C6X7:1-20"], "694009", min_identity=100).splitlines()
    assert [line.split("\t")[1] for line in best[1:]] == ["P0C6U8", "P0C6X7"]


def test_map(conn):
    """The write's occurrences, relative to the interactor, extra end residues apart."""
    lines = map_(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG", "WWWWW"]).splitlines()
    assert lines[:3] == [
        "# on P26662[810-1026]",
        "#sequence\tnter\tcter\toccurrences\tverdict",
        "mDREMAASCGG\tM\t-\tP26662 2-11 (100 %)\tok",
    ]
    assert lines[3].endswith("below 90 %")


def test_used(conn):
    """Under the species; without the publication excluded; obsolete snapshots marked."""
    lines = used(conn.cursor(), "694009", ["nsp1", "n", "none such"]).splitlines()
    assert lines[1:3] == [
        "nsp1\tnsp1\tP0C6X7\t1-180\tcurrent\t7",
        "nsp1\tnsp1\tP0C6U8\t1-180\tcurrent\t2",
    ]
    assert "n\tN\tQ6VA95\t1-63\tcurrent\t2" in lines
    assert lines[-1] == "none such\t(none)"
    assert used(conn.cursor(), "694009", ["nsp12"], exclude=22046132).splitlines()[1] == (
        "nsp12\t(none)"  # used only by that publication
    )
    assert "nsp15\tnsp15\tQ6SRE2\t1-312\tobsolete\t1" in used(conn.cursor(), "3418604", ["nsp15"])


def test_sql_is_guarded(dbname):
    """A page of rows with their total, long cells cut, a write refused."""
    result = _command(
        "sql", "SELECT accession, sequences FROM proteins ORDER BY id", "--limit", "2"
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "accession\tsequences"
    assert len(lines) == 1 + 2 + 1 and lines[-1].startswith("… 1-2 of 231 shown: --offset 2")
    assert all(len(line) < 300 for line in lines) and "chars)" in result.stdout
    result = _command("sql", "UPDATE methods SET name = 'x' WHERE psimi_id = 'MI:0018'")
    assert result.returncode == 1 and "read-only transaction" in result.stderr

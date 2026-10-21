"""The alignments on the sequences of the test database: the write's, and the database search."""

import subprocess

from drakkar.alignments import closest, mapping
from drakkar.read import Page, sequence_of


def test_closest(conn):
    """The entries of the taxon subtree by the score of their best isoform, Swiss-Prot first
    among equals, an accession or a sequence as query; every entry counted."""
    lines = closest(conn.cursor(), ["P0C6X7:1-20", "MESLVLGVNE"], 694009, Page(3)).splitlines()
    assert lines[:5] == [
        "#sequence\taccession\tdb\tprotein\ttaxon\tidentity\tcoverage\tregion",
        "P0C6X7:1-20\tP0C6U8\tSP\tReplicase polyprotein 1a\t"
        "694009 Severe acute respiratory syndrome-related coronavirus\t100.0 %\t100.0 %\t1-20",
        "P0C6X7:1-20\tP0C6X7\tSP\tReplicase polyprotein 1ab\t"
        "694009 Severe acute respiratory syndrome-related coronavirus\t100.0 %\t100.0 %\t1-20",
        "P0C6X7:1-20\tP0C6W6\tSP\tReplicase polyprotein 1ab\t"
        "349344 Bat SARS CoV Rp3/2004\t95.0 %\t100.0 %\t1-20",
        "P0C6X7:1-20\t… 3 of 18",
    ]
    unread = closest(conn.cursor(), ["X1", "MESLVLGVNE", "not a sequence"], 694009).splitlines()
    assert unread[-2:] == [
        "X1\tX1 has no current snapshot",
        "not a sequence\tneither an accession nor an amino acid sequence",
    ]


def test_closest_identity_counts_the_gaps(conn):
    """A residue deleted from the query: one gap column among the aligned columns."""
    query = sequence_of(conn.cursor(), "P0C6X7:1-41")
    gapped = query[:20] + query[21:]  # 40 residues, 41 columns
    line = closest(conn.cursor(), [gapped], 694009, Page(1)).splitlines()[1]
    fields = line.split("\t")
    assert [fields[1], *fields[5:]] == ["P0C6U8", "97.6 %", "100.0 %", "1-41"]


def test_mapping(conn):
    """The write's occurrences, in the entry's numbering, extra end residues apart."""
    lines = mapping(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG", "WWWWW"]).splitlines()
    assert lines[:2] == [
        "#sequence\tnter\tcter\toccurrences\tverdict",
        "mDREMAASCGG\tM\t-\tP26662 811-820 (100 %)\tok",
    ]
    assert lines[2].endswith("below 90 %")


def test_mapping_refuses_a_second_interactor(dbname):
    result = subprocess.run(
        ["uv", "run", "drakkar-align", "mapping", "P26662:810-1026", "DREMAASCGG", "P26662:1-10"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1 and result.stdout == ""
    assert "P26662:1-10: an accession where a sequence is expected" in result.stderr

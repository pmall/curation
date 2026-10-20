"""The alignments, as the write computes them, on the sequences of the test database."""

from drakkar.alignments import closest, mapping


def test_closest(conn):
    """The entries of the taxon subtree by identity, an accession or a sequence as query."""
    lines = closest(conn.cursor(), ["P0C6X7:1-20", "MESLVLGVNE"], 694009).splitlines()
    assert lines[0] == "#sequence\taccession\tdb\tprotein\ttaxon\tidentity\tregion"
    first = [line.split("\t") for line in lines if line.startswith("P0C6X7:1-20\t")]
    assert [(f[1], f[5]) for f in first[:3]] == [
        ("P0C6U8", "100.0 %"),
        ("P0C6X7", "100.0 %"),
        ("P0C6W6", "95.0 %"),
    ]
    unread = closest(conn.cursor(), ["X1", "MESLVLGVNE", "not a sequence"], 694009).splitlines()
    assert unread[-2:] == [
        "X1\tX1 has no current snapshot",
        "not a sequence\tneither an accession nor an amino acid sequence",
    ]


def test_mapping(conn):
    """The write's occurrences, relative to the interactor, extra end residues apart."""
    lines = mapping(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG", "WWWWW"]).splitlines()
    assert lines[:2] == [
        "#sequence\tnter\tcter\toccurrences\tverdict",
        "mDREMAASCGG\tM\t-\tP26662 2-11 (100 %)\tok",
    ]
    assert lines[2].endswith("below 90 %")

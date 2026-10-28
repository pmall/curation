"""The mapping check on the sequences of the test database: the write's occurrences."""

from drakkar.mapping import mapping
from drakkar.read import sequence_of


def test_mapping(conn):
    """The write's occurrences, in the entry's numbering, extra end residues apart; a long
    sequence shown by its start."""
    lines = mapping(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG", "WWWWW"]).splitlines()
    assert lines[:2] == [
        "#sequence\tnter\tcter\toccurrences\tverdict",
        "mDREMAASCGG\tM\t-\tP26662 811-820 (100 %)\tok",
    ]
    assert lines[2].endswith("below 90 %")
    long = sequence_of(conn.cursor(), "P26662:811-840")
    line = mapping(conn.cursor(), "P26662:810-1026", [long]).splitlines()[1]
    assert line == f"{long[:20]}…(30 characters)\t-\t-\tP26662 811-840 (100 %)\tok"
    spaced = mapping(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG WWWWW", " DREMAASCGG"])
    assert spaced.splitlines()[1:] == [
        "mDREMAASCGG WWWWW\t2 parts separated by whitespace: one sequence per argument",
        "DREMAASCGG\tleading or trailing whitespace around the argument",
    ]


def test_mapping_refuses_a_second_interactor(conn):
    """An accession among the sequences: its own line, the others checked."""
    lines = mapping(conn.cursor(), "P26662:810-1026", ["DREMAASCGG", "P26662:1-10"]).splitlines()
    assert lines[1].endswith("\tok")
    assert lines[2] == "P26662:1-10\tan accession: one interactor per call"


def test_mapping_takes_an_accession_as_written(conn):
    """Lowercase and versioned, on its current entry."""
    assert (
        mapping(conn.cursor(), "p26662.3:810-1026", ["DREMAASCGG"]).splitlines()[1].endswith("ok")
    )


def test_mapping_interactor_that_cannot_be_read(conn):
    """An isoform, or coordinates outside the entry: a message alone."""
    isoform = mapping(conn.cursor(), "O00499-2", ["DREMAASCGG"])
    assert isoform == "O00499-2: an interactor is an entry, not an isoform"
    outside = mapping(conn.cursor(), "P26662:1-99999", ["DREMAASCGG"])
    assert outside == "P26662:1-99999: 1-99999 is not a stretch of 1-3010"

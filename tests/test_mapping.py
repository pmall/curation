"""The mapping check on the sequences of the test database: the write's occurrences."""

import subprocess

from drakkar.mapping import mapping


def test_mapping(conn):
    """The write's occurrences, in the entry's numbering, extra end residues apart."""
    lines = mapping(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG", "WWWWW"]).splitlines()
    assert lines[:2] == [
        "#sequence\tnter\tcter\toccurrences\tverdict",
        "mDREMAASCGG\tM\t-\tP26662 811-820 (100 %)\tok",
    ]
    assert lines[2].endswith("below 90 %")
    spaced = mapping(conn.cursor(), "P26662:810-1026", ["mDREMAASCGG WWWWW", " DREMAASCGG"])
    assert spaced.splitlines()[1:] == [
        "mDREMAASCGG WWWWW\t2 parts separated by whitespace: one sequence per argument",
        "DREMAASCGG\tleading or trailing whitespace around the argument",
    ]


def test_mapping_refuses_a_second_interactor(dbname):
    result = subprocess.run(
        ["uv", "run", "drakkar-mapping", "P26662:810-1026", "DREMAASCGG", "P26662:1-10"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1 and result.stdout == ""
    assert "P26662:1-10: an accession where a sequence is expected" in result.stderr

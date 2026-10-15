"""The read views: what a decision needs, from the test database."""

import subprocess

from drakkar.read import entry, names, publication, rows


def test_publication(conn):
    text = publication(conn.cursor(), 1, 22046132)
    assert "Title: The SARS-coronavirus-host interactome" in text
    assert "Abstract: Coronaviruses" in text
    assert "EY73D2C965 v1 MI:0018: BRF1 (Q92994) – N Q6VA95[1-63]" in text


def test_entry_lists_the_chains(conn):
    text = entry(conn.cursor(), "P26662")
    assert "- 810-1026 chain: Protease NS2" in text
    assert "viral, taxon" in text


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

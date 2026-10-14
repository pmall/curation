"""The read views: what a decision needs, from the test database."""

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


def test_rows(conn):
    lines = rows(conn.cursor(), ["EY73D2C965"]).splitlines()
    assert lines[0].startswith("#stable_id") and lines[1].startswith("EY73D2C965\t1\t1\t22046132")

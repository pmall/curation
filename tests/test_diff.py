"""The diff of a curated publication against its live descriptions, and its command."""

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from drakkar.diff import diff_descriptions
from drakkar.files import ADD, REVISE, format_new_description, read_rows, revision, write_rows
from drakkar.write import Description, NewDescription, live_revisions

SARS = (1, 22046132)  # Q6VA95 `N` carried by EY73D2C965 and EYF737084C
SELECTED = (12, 25031347)
NEW = NewDescription(*SELECTED, Description("MI:0007", "P46934", "P25223", "P"))  # NEDD4


def curated_again(conn, run_id: int, pmid: int) -> dict[str, NewDescription]:
    """The live descriptions of a publication, as a curation that finds them all would give them."""
    rows = {
        r.stable_id: NewDescription(run_id, pmid, r.description, "CREATED: Fig. 1")
        for r in live_revisions(conn.cursor(), run_id, pmid)
        if r.description is not None
    }
    conn.rollback()
    return rows


def diff(conn, publication, items):
    result = diff_descriptions(conn.cursor(), *publication, list(items))
    conn.rollback()
    return result


def test_the_same_curation_changes_nothing(conn):
    again = curated_again(conn, *SARS)
    result = diff(conn, SARS, again.values())
    assert sorted(result.same) == sorted(again)
    assert not result.added and not result.revised and not result.deleted


def test_empty_coordinates_are_the_full_protein(conn):
    again = curated_again(conn, *SARS)
    n = again["EY73D2C965"]
    assert (n.description.accession2, n.description.start2, n.description.stop2) == (
        "Q6VA95",
        1,
        63,
    )
    again["EY73D2C965"] = replace(n, description=replace(n.description, start2=None, stop2=None))
    assert "EY73D2C965" in diff(conn, SARS, again.values()).same


def test_a_new_publication_gives_only_additions(conn):
    conn.execute(  # a selected publication without descriptions, in this transaction only
        "UPDATE descriptions SET deleted_at = now() WHERE association_id = "
        "(SELECT id FROM associations WHERE run_id = %s AND pmid = %s)",
        SELECTED,
    )
    result = diff(conn, SELECTED, [NEW])
    assert result.added == [NEW]
    assert not result.same and not result.revised and not result.deleted


def test_another_name_or_other_mappings_are_a_revision(conn):
    again = curated_again(conn, *SARS)
    n = again["EY73D2C965"]
    again["EY73D2C965"] = replace(
        n,
        description=replace(
            n.description, name2="orf9b", mappings2=("MDPNQTNVVPPALHLVDPQIQLTITR",)
        ),
        note="CREATED: Y2H (MI:0018), Table S1\n- Mapping: 1–26 (Fig. 3)",
    )
    result = diff(conn, SARS, again.values())
    [revised] = result.revised
    assert (revised.stable_id, revised.version, revised.action) == ("EY73D2C965", 1, "revise")
    assert revised.description == again["EY73D2C965"].description
    assert revised.note == (
        "REVISED: re-curation, name2 N → orf9b, mappings2 1 added, 0 removed; "
        "Y2H (MI:0018), Table S1\n- Mapping: 1–26 (Fig. 3)"
    )
    assert "EY73D2C965" not in result.same and not result.added and not result.deleted


def test_another_method_or_interactor_is_a_deletion_and_an_addition(conn):
    again = curated_again(conn, *SARS)
    n = again.pop("EY73D2C965")
    other = replace(n, description=replace(n.description, method="MI:0007"))
    result = diff(conn, SARS, [*again.values(), other])
    assert result.added == [other]
    [deleted] = result.deleted
    assert (deleted.stable_id, deleted.action, deleted.description) == (
        "EY73D2C965",
        "remove",
        None,
    )
    assert deleted.note == "REMOVED: not found by the re-curation"


def test_an_empty_curation_deletes_every_live_description(conn):
    live = curated_again(conn, *SARS)
    result = diff(conn, SARS, [])
    assert sorted(r.stable_id for r in result.deleted) == sorted(live)
    assert not result.same and not result.added and not result.revised


def test_a_description_of_another_publication_is_refused(conn):
    with pytest.raises(ValueError, match="is in publication 25031347 of run 12, not 22046132"):
        diff(conn, SARS, [NEW])


def test_a_description_curated_twice_is_refused(conn):
    with pytest.raises(ValueError, match="curated twice"):
        diff(conn, SELECTED, [NEW, replace(NEW, note="CREATED: Fig. 2")])


def test_a_publication_not_in_the_run_is_refused(conn):
    with pytest.raises(ValueError, match="publication 22046132 is not in run 12"):
        diff(conn, (12, 22046132), [])


# --- The command --------------------------------------------------------------------------------


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", *args], capture_output=True, text=True)


def test_diff_command_writes_files_the_write_tools_take(conn, tmp_path: Path):
    again = curated_again(conn, *SARS)
    del again["EY73D2C965"], again["EYF737084C"]  # the two `N`: deleted
    added = NewDescription(
        *SARS,
        Description("MI:0007", "P46934", "Q6VA95", "N"),
        "CREATED: anti-tag co-IP (MI:0007), Fig. 2B",
    )
    path = tmp_path / "descriptions.tsv"
    write_rows(path, ADD, [format_new_description(d) for d in [*again.values(), added]])

    result = run("drakkar-diff", *map(str, SARS), str(path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"PMID 22046132, run 1: {len(again)} same",
        f"1 to add: {tmp_path / 'descriptions.add.tsv'}",
        f"0 to revise: {tmp_path / 'descriptions.revise.tsv'}",
        f"2 to delete: {tmp_path / 'descriptions.delete.tsv'}",
    ]
    deleted = [revision(*row) for row in read_rows([tmp_path / "descriptions.delete.tsv"], REVISE)]
    assert sorted(r.stable_id for r in deleted) == ["EY73D2C965", "EYF737084C"]
    assert read_rows([tmp_path / "descriptions.revise.tsv"], REVISE) == []

    # The files are those of the write tools: deleting the two `N` frees Q6VA95[1-63] for the
    # addition, which passes once they are gone.
    removed = run("drakkar-revise", str(tmp_path / "descriptions.delete.tsv"), "--commit")
    assert removed.returncode == 0 and "committed" in removed.stdout, removed.stdout
    add = run("drakkar-add", str(tmp_path / "descriptions.add.tsv"))
    assert add.returncode == 0 and "dry run passed" in add.stdout, add.stdout


def test_diff_command_refuses_another_publication(dbname, tmp_path: Path):
    path = tmp_path / "descriptions.tsv"
    write_rows(path, ADD, [format_new_description(NEW)])
    result = run("drakkar-diff", *map(str, SARS), str(path))
    assert result.returncode == 1 and "not 22046132 of run 1" in result.stderr
    assert not (tmp_path / "descriptions.add.tsv").exists()

"""The file formats, and the commands run end to end on the test database."""

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from drakkar.files import (
    ADD,
    PUBLICATIONS,
    REVISE,
    FileError,
    format_new_description,
    format_revision,
    header,
    read_rows,
    revision,
    write_rows,
)
from drakkar.write import Description, NewDescription, live_revisions

SARS = (1, 22046132)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", *args], capture_output=True, text=True)


def test_revision_rows_round_trip(conn, tmp_path: Path):
    revisions = live_revisions(conn.cursor(), *SARS)
    path = tmp_path / "rows.tsv"
    path.write_text("\n".join([header(REVISE), *map(format_revision, revisions)]) + "\n")
    assert [revision(w, r) for w, r in read_rows([path], REVISE)] == revisions


def test_files_concatenate(tmp_path: Path):
    row = "\t".join(["EY73D2C965", "1", "1", "22046132", "remove", "", *[""] * 9, "a\\nb"])
    for name in ("a.tsv", "b.tsv"):
        (tmp_path / name).write_text(f"{header(REVISE)}\n{row}\n")
    paths = [tmp_path / "a.tsv", tmp_path / "b.tsv"]
    rows = read_rows(paths, REVISE)
    assert len(rows) == 2 and revision(*rows[0]).note == "a\nb"


def test_bad_header_and_bad_rows_are_refused(tmp_path: Path):
    path = tmp_path / "bad.tsv"
    path.write_text("#stable_id\tversion\n")
    with pytest.raises(FileError, match="header"):
        read_rows([path], REVISE)
    path.write_text("EY73D2C965\t1\n")
    with pytest.raises(FileError, match="fields"):
        read_rows([path], REVISE)


def test_revise_command(dbname, tmp_path: Path):
    rows = run("drakkar-read", "row", "EY73D2C965", "EYF737084C").stdout.splitlines()
    assert rows[0] == header(REVISE)
    note = "REVISED: name2 N → orf6"
    edited = [rows[0]]
    for row in rows[1:]:
        fields = row.split("\t")
        fields[REVISE.index("name2")] = "orf6"
        fields[REVISE.index("note")] = note
        edited.append("\t".join(fields))
    path = tmp_path / "22046132.revise.tsv"
    path.write_text("\n".join(edited) + "\n")

    dry = run("drakkar-revise", str(path))
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert "dry run passed" in dry.stdout
    done = run("drakkar-revise", str(path), "--commit")
    assert done.returncode == 0 and "committed" in done.stdout
    again = run("drakkar-revise", str(path))  # decided on version 1, now 2
    assert again.returncode == 1 and "live version is 2" in again.stdout


def test_add_command_reports_the_refused_row(dbname, tmp_path: Path):
    add = run("drakkar-add", "--header").stdout.strip()
    fields = ["12", "25031347", "MI:0007", "P46934", "NOTANACC", "", "", "P", "", "", "", ""]
    path = tmp_path / "25031347.add.tsv"
    path.write_text(f"{add}\n" + "\t".join(fields) + "\n")
    result = run("drakkar-add", str(path))
    assert result.returncode == 1
    assert f"refused {path}:2: protein 2: NOTANACC" in result.stdout


def test_batch_command(conn, tmp_path: Path):
    """The merged files of a batch: two renames, an addition that relies on them (no delete
    file), and a publication left `selected`, moved last."""
    note = "REVISED: name2 N → orf6"
    renames = [
        replace(r, description=replace(r.description, name2="orf6"), note=note)
        for r in live_revisions(conn.cursor(), *SARS)
        if r.description is not None and r.description.name2 == "N"
    ]
    added = NewDescription(
        *SARS, Description("MI:0007", "P46934", "Q6VA95", "orf6"), "CREATED: Fig. 2B"
    )
    selected = "SELECTED: no full text\\n- Pass 2026-10-20: not accessible"
    write_rows(tmp_path / "descriptions.revise.tsv", REVISE, [format_revision(r) for r in renames])
    write_rows(tmp_path / "descriptions.add.tsv", ADD, [format_new_description(added)])
    write_rows(tmp_path / "publications.tsv", PUBLICATIONS, [f"12\t25031347\tselected\t{selected}"])

    dry = run("drakkar-batch", str(tmp_path))
    assert dry.returncode == 0 and "dry run passed" in dry.stdout, dry.stdout + dry.stderr
    done = run("drakkar-batch", str(tmp_path), "--commit")
    assert done.returncode == 0 and "committed" in done.stdout, done.stdout
    assert "move 32/25031347 to the special run" in done.stdout

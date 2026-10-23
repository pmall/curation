"""The file formats, and the commands run end to end on the test database."""

import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from drakkar.files import (
    FileError,
    format_new_description,
    format_revision,
    read_descriptions,
    read_publications,
    read_revisions,
    write_descriptions,
    write_publications,
    write_revisions,
)
from drakkar.write import (
    Description,
    NewDescription,
    PublicationUpdate,
    Revision,
    live_revisions,
)

SARS = 22046132
SELECTED = 25031347


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", *args], capture_output=True, text=True)


def test_revisions_round_trip_in_json_lines(conn, tmp_path: Path):
    """A revision, a removal, its description keys null, and a merge, as they were written."""
    live = live_revisions(conn.cursor(), SARS)
    conn.rollback()
    removal = replace(live[0], action="remove", description=None, note="REMOVED: HLA protein")
    merge = replace(live[1], action="remove", into=live[0].stable_id, note="REMOVED: duplicate")
    items = [replace(live[0], note="name2 N → orf6"), removal, merge]
    path = tmp_path / "descriptions.revise.jsonl"
    write_revisions(path, items)
    assert [item for _, item in read_revisions([path])] == items
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert lines[1]["method"] is None and lines[1]["into"] is None
    assert lines[2]["into"] == live[0].stable_id


def test_a_revision_with_another_action_is_refused_with_its_line(tmp_path: Path):
    removal = Revision("EY73D2C965", 1, SARS, "remove", note="REMOVED: HLA protein")
    path = tmp_path / "descriptions.delete.jsonl"
    path.write_text(json.dumps(json.loads(format_revision(removal)) | {"action": "delete"}) + "\n")
    why = "action is 'delete', not revise or remove"
    with pytest.raises(FileError, match=re.escape(f"{path}:1: {why}")):
        read_revisions([path])


# --- Descriptions to add and publications -----------------------------------------------------

N = NewDescription(SARS, Description("MI:0007", "P46934", "Q6VA95", "N"), "Fig. 1")


def json_line(**changes: object) -> str:
    """N as a line of JSON, with some values changed."""
    return json.dumps(json.loads(format_new_description(N)) | changes)


def test_descriptions_round_trip_in_json_lines(tmp_path: Path):
    """Every value comes back as written, one line per description, a note with line breaks,
    quotes, a tab, a backslash and a line separator included; files merged with `cat` are read
    whole."""
    note = 'anti-tag co-IP (MI:0007), Fig. 2B\n- Remark: "NS3"\tmutant \\ 1–180 \u2028 kept'
    ns3 = Description(
        "MI:0018", "P46934", "P26662", "NS3", 1027, 1657, ("mSTNPK",), ("DREMA", "gstQQ"), ("QQ",)
    )
    items = [replace(N, note=note), NewDescription(SELECTED, ns3, "Y2H (MI:0018), Table S1")]
    path = tmp_path / "descriptions.jsonl"
    write_descriptions(path, items)
    assert path.read_text().count("\n") == 2
    assert [item for _, item in read_descriptions([path])] == items
    merged = tmp_path / "merged.jsonl"
    merged.write_text(path.read_text() * 2)
    assert [where for where, _ in read_descriptions([merged])] == [
        f"{merged}:{n}" for n in (1, 2, 3, 4)
    ]


def test_an_empty_descriptions_file_has_no_description(tmp_path: Path):
    path = tmp_path / "descriptions.jsonl"
    write_descriptions(path, [])
    assert path.read_text() == "" and read_descriptions([path]) == []


def test_a_missing_or_unknown_key_is_refused_with_its_line(tmp_path: Path):
    path = tmp_path / "descriptions.jsonl"
    row = json.loads(json_line(comment="from Fig. 3"))
    del row["note"], row["stop2"]
    path.write_text(f"{json_line()}\n{json.dumps(row)}\n")
    with pytest.raises(FileError) as refused:
        read_descriptions([path])
    assert str(refused.value) == f"{path}:2: missing stop2, note; unknown comment"


@pytest.mark.parametrize(
    ("line", "why"),
    [
        ('{"pmid": 1,', "not JSON: "),
        ("[1, 2]", "not a JSON object"),
        (json_line(start2="1"), "start2 is not a number: '1'"),
        (json_line(pmid=True), "pmid is not a number: True"),
        (json_line(mappings2="DREMA"), "mappings2 is not a list of strings: 'DREMA'"),
        (json_line(note=None), "note is not a string: None"),
    ],
)
def test_a_value_of_the_wrong_type_is_refused_with_its_line(tmp_path: Path, line: str, why: str):
    path = tmp_path / "descriptions.jsonl"
    path.write_text(line + "\n")
    with pytest.raises(FileError, match=re.escape(f"{path}:1: {why}")):
        read_descriptions([path])


def test_publications_round_trip_in_json_lines(tmp_path: Path):
    items = [
        PublicationUpdate(SARS, "curated", 'CURATED: co-IP of N\n- Not kept: N × B — "cited"'),
        PublicationUpdate(SELECTED, "selected", "SELECTED: no full text, closed"),
    ]
    path = tmp_path / "publications.jsonl"
    write_publications(path, items)
    assert [item for _, item in read_publications([path])] == items


def test_a_publication_in_another_state_is_refused_with_its_line(tmp_path: Path):
    path = tmp_path / "publications.jsonl"
    row = {"pmid": 22046132, "state": "discarded", "note": "DISCARDED: review"}
    path.write_text(json.dumps(row) + "\n")
    why = "state is 'discarded', not selected or curated"
    with pytest.raises(FileError, match=re.escape(f"{path}:1: {why}")):
        read_publications([path])


# --- The notes of a curation batch --------------------------------------------------------------


def test_notes_command_writes_the_publications_of_a_batch(tmp_path: Path):
    """One row per note, the PMID its directory's name, the state its header, the note as
    written; a directory without a note, and the merged files, are left out."""
    notes = {
        "22046132": "CURATED: co-IP of SARS-CoV N with NEDD4\n- Not kept: N × B — only cited\n",
        "25031347": "SELECTED: no full text, closed — not open access anywhere\n",
    }
    for pmid, note in notes.items():
        (tmp_path / pmid).mkdir()
        (tmp_path / pmid / "curation.txt").write_text(note)
    (tmp_path / "38566321").mkdir()  # left out of the batch: no note
    (tmp_path / "descriptions.jsonl").write_text("")

    result = run("drakkar-notes", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == f"1 curated, 1 selected: {tmp_path / 'publications.jsonl'}\n"
    assert [item for _, item in read_publications([tmp_path / "publications.jsonl"])] == [
        PublicationUpdate(22046132, "curated", notes["22046132"].strip()),
        PublicationUpdate(25031347, "selected", notes["25031347"].strip()),
    ]


def test_notes_command_never_refuses_a_note(tmp_path: Path):
    """A non-empty note without the SELECTED header is `curated`, whatever it holds, left to the
    write's check; an empty note, or a directory not named by a PMID, gives no row."""
    notes = {
        "22046132": b"co-IP of N\n",
        "25031347": b"CURATED co-IP of \xff\n",
        "38566321": b"\n",
        "notes": b"x",
    }
    for name, note in notes.items():
        (tmp_path / name).mkdir()
        (tmp_path / name / "curation.txt").write_bytes(note)

    result = run("drakkar-notes", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == f"2 curated, 0 selected: {tmp_path / 'publications.jsonl'}\n"
    assert [item for _, item in read_publications([tmp_path / "publications.jsonl"])] == [
        PublicationUpdate(22046132, "curated", "co-IP of N"),
        PublicationUpdate(25031347, "curated", "CURATED co-IP of \ufffd"),
    ]


def test_revise_command(conn, tmp_path: Path):
    live = {r.stable_id: r for r in live_revisions(conn.cursor(), SARS)}
    conn.rollback()
    note = "name2 N → orf6"
    edited = [
        replace(live[s], description=replace(live[s].description, name2="orf6"), note=note)
        for s in ("EY73D2C965", "EYF737084C")
    ]
    path = tmp_path / "22046132.revise.jsonl"
    write_revisions(path, edited)

    dry = run("drakkar-revise", str(path))
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert "dry run passed" in dry.stdout
    done = run("drakkar-revise", str(path), "--commit")
    assert done.returncode == 0 and "committed" in done.stdout
    again = run("drakkar-revise", str(path))  # decided on version 1, now 2
    assert again.returncode == 1 and "live version is 2" in again.stdout


def test_add_command_reports_the_refused_row(dbname, tmp_path: Path):
    bad = NewDescription(SELECTED, Description("MI:0007", "P46934", "NOTANACC", "P"), "Fig. 2B")
    path = tmp_path / "25031347.jsonl"
    write_descriptions(path, [bad])
    result = run("drakkar-add", str(path))
    assert result.returncode == 1
    assert f"refused {path}:1: protein 2: NOTANACC" in result.stdout


def test_batch_command_writes_a_curation_batch(dbname, tmp_path: Path):
    """A curation batch, its files merged as the curate skill merges them: a new description, and
    its publication left `selected`, moved last with it."""
    added = NewDescription(SELECTED, Description("MI:0007", "P46934", "P25223", "P"), "Fig. 2B")
    publication = tmp_path / "25031347"
    publication.mkdir()
    write_descriptions(publication / "descriptions.jsonl", [added])
    (publication / "curation.txt").write_text(
        "SELECTED: co-IP of P with NEDD4\n- Not read: Table S1 (Fig. 2) — relevant, no URL given\n"
    )
    merge = f"cat {tmp_path}/*/descriptions.jsonl > {tmp_path}/descriptions.jsonl"
    subprocess.run(merge, shell=True, check=True)
    notes = run("drakkar-notes", str(tmp_path))
    assert notes.returncode == 0, notes.stdout + notes.stderr

    dry = run("drakkar-batch", str(tmp_path))
    assert dry.returncode == 0 and "dry run passed" in dry.stdout, dry.stdout + dry.stderr
    done = run("drakkar-batch", str(tmp_path), "--commit")
    assert done.returncode == 0 and "3 rows, 3 applied: committed" in done.stdout, done.stdout
    assert "move 32/25031347 to the special run" in done.stdout


def test_batch_command_writes_the_files_of_a_diff(conn, tmp_path: Path):
    """The files of a diff: two renames and an addition that relies on them (no delete file),
    read in place of the descriptions.jsonl beside them, which would add it a second time."""
    note = "name2 N → orf6"
    renames = [
        replace(r, description=replace(r.description, name2="orf6"), note=note)
        for r in live_revisions(conn.cursor(), SARS)
        if r.description is not None and r.description.name2 == "N"
    ]
    conn.rollback()
    orf6 = NewDescription(SARS, Description("MI:0007", "P46934", "Q6VA95", "orf6"), "Fig. 2B")
    curated = "CURATED: co-IP of SARS-CoV orf6 with NEDD4"
    write_revisions(tmp_path / "descriptions.revise.jsonl", renames)
    write_descriptions(tmp_path / "descriptions.add.jsonl", [orf6])
    write_descriptions(tmp_path / "descriptions.jsonl", [orf6])
    publications = [PublicationUpdate(SARS, "curated", curated)]
    write_publications(tmp_path / "publications.jsonl", publications)

    done = run("drakkar-batch", str(tmp_path), "--commit")
    assert done.returncode == 0 and "4 rows, 4 applied: committed" in done.stdout, done.stdout

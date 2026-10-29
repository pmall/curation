"""Each invariant finds a violation made in the fixture; the fixture itself has no error."""

import pytest

from database.check import INVARIANTS, errors, run_checks

# A live vh row with a mapping on side 1, and a stable ID with several versions.
LIVE_VH = """
    SELECT d.id FROM descriptions AS d JOIN associations AS a ON a.id = d.association_id
    JOIN runs AS r ON r.id = a.run_id
    WHERE d.deleted_at IS NULL AND r.type = 'vh' AND json_array_length(d.mapping1) > 0
    ORDER BY d.id LIMIT 1
"""
OLD_VERSION = "SELECT id FROM descriptions WHERE deleted_at IS NOT NULL ORDER BY id LIMIT 1"
Q6VA95 = """
    SELECT d.id FROM descriptions AS d JOIN proteins AS p ON p.id = d.protein2_id
    WHERE d.deleted_at IS NULL AND p.accession = 'Q6VA95' ORDER BY d.id LIMIT 1
"""

# Each violation uses the rows found by the queries above: %(live)s, %(old)s, %(q6va95)s.
VIOLATIONS = {
    "R3": """
        UPDATE proteins SET ncbi_taxon_id = 999999999
        WHERE id = (SELECT protein1_id FROM descriptions WHERE id = %(live)s)
    """,
    "V2": "UPDATE descriptions SET version = version + 10 WHERE id = %(live)s",
    "V3": "UPDATE descriptions SET deleted_at = NULL WHERE id = %(old)s",
    "V4": """
        UPDATE descriptions SET deleted_at = deleted_at + interval '10 years' WHERE id = %(old)s
    """,
    "V5": "UPDATE descriptions SET deleted_at = created_at - interval '1 day' WHERE id = %(old)s",
    "V6": """
        UPDATE descriptions SET association_id = (SELECT max(id) FROM associations)
        WHERE id = %(old)s AND association_id <> (SELECT max(id) FROM associations)
    """,
    "V7": """
        UPDATE descriptions SET stable_id = 'XX00000000'
        WHERE stable_id = (SELECT stable_id FROM descriptions WHERE id = %(live)s)
    """,
    "D1": "UPDATE descriptions SET protein1_id = protein2_id WHERE id = %(live)s",
    "D3": "UPDATE descriptions SET start2 = stop2 + 1 WHERE id = %(live)s",
    "D4": "UPDATE descriptions SET stop1 = stop1 - 1 WHERE id = %(live)s",
    "D5": """
        INSERT INTO descriptions (stable_id, version, association_id, method_id, protein1_id,
            name1, start1, stop1, mapping1, protein2_id, name2, start2, stop2, mapping2)
        SELECT 'CW00000000', 1, association_id, method_id, protein1_id, name1, start1, stop1,
            mapping1, protein2_id, name2, start2, stop2, mapping2
        FROM descriptions WHERE id = %(live)s
    """,
    "D6": "UPDATE descriptions SET name2 = 'orf6' WHERE id = %(q6va95)s",
    "D7": "UPDATE descriptions SET name1 = 'NOTAGENE' WHERE id = %(live)s",
    "D9": """
        UPDATE descriptions
        SET mapping1 = regexp_replace(mapping1::text, '"sequence": *"', '"sequence": "WWWWW')::json
        WHERE id = %(live)s
    """,
    "D10": "UPDATE descriptions SET stop2 = stop2 - 1 WHERE id = %(q6va95)s",
    "D11": """UPDATE descriptions SET mapping1 = '[{"sequence": 1}]' WHERE id = %(live)s""",
    "D12": """
        UPDATE descriptions
        SET mapping1 = regexp_replace(mapping1::text, '"identity": *[0-9.]+', '"identity": 80',
                                      'g')::json
        WHERE id = %(live)s
    """,
    "S1": """
        UPDATE associations SET state = 'pending'
        WHERE id = (SELECT association_id FROM descriptions WHERE id = %(live)s)
    """,
    "S5": "INSERT INTO runs (type, name) SELECT type, name FROM runs ORDER BY id LIMIT 1",
}


def ids(conn) -> dict[str, int]:
    return {
        name: conn.execute(sql).fetchone()[0]
        for name, sql in (("live", LIVE_VH), ("old", OLD_VERSION), ("q6va95", Q6VA95))
    }


def counts(conn) -> dict[str, int]:
    return {r.invariant.id: len(r.rows) for r in run_checks(conn.cursor())}


def test_fixture_has_no_error(conn):
    assert errors(run_checks(conn.cursor())) == []


def test_every_invariant_is_tested():
    # D2 (obsolete snapshots) is in the fixture as it is.
    assert set(VIOLATIONS) | {"D2"} == {i.id for i in INVARIANTS}


@pytest.mark.parametrize("invariant", sorted(VIOLATIONS))
def test_violation_is_found(conn, invariant):
    before = counts(conn)
    conn.execute(VIOLATIONS[invariant], ids(conn))
    after = counts(conn)
    assert after[invariant] > before[invariant]


def test_checks_see_the_transaction_and_leave_it_usable(conn):
    cur = conn.cursor()
    before = counts(conn)
    cur.execute(VIOLATIONS["D5"], ids(conn))
    assert counts(conn)["D5"] == before["D5"] + 1  # uncommitted, seen; temp tables dropped
    conn.rollback()
    assert counts(conn) == before


def test_extra_end_residues_are_left_out_of_the_occurrences(conn):
    before = counts(conn)
    # WWWWW added before the first mapping, and named as its nter: its occurrences still fit
    conn.execute(
        """
        UPDATE descriptions
        SET mapping1 = jsonb_set(
            jsonb_set(mapping1::jsonb, '{0,sequence}',
                      to_jsonb('WWWWW' || (mapping1->0->>'sequence'))),
            '{0,nter}', '"WWWWW"')::json
        WHERE id = %(live)s
        """,
        ids(conn),
    )
    assert counts(conn)["D9"] == before["D9"]
    conn.execute(
        """
        UPDATE descriptions SET mapping1 = jsonb_set(mapping1::jsonb, '{0,nter}', '"AAAAA"')::json
        WHERE id = %(live)s
        """,
        ids(conn),
    )
    assert counts(conn)["D9"] == before["D9"] + 1


def test_extra_end_residues_must_be_text(conn):
    before = counts(conn)
    conn.execute(
        "UPDATE descriptions SET mapping1 = jsonb_set(mapping1::jsonb, '{0,nter}', '1')::json "
        "WHERE id = %(live)s",
        ids(conn),
    )
    assert counts(conn)["D11"] == before["D11"] + 1

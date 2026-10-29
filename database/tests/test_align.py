from typing import Any

import pytest

from database.align import best_identity, core, map_sequence, read_written, written

MOTIF = "PEPTIDEKLMNQRST"  # 15 residues
MUTANT = "PEPTIDEKLWNQRST"  # one mismatch: 93.33 %


def occurrences(mapping: dict[str, Any]) -> dict[str, Any]:
    return {i["accession"]: i["occurrences"] for i in mapping["isoforms"]}


def placements(sequence: str, region: str) -> list[tuple[int, int, float]]:
    """The occurrences of a mapping on a protein without isoforms."""
    mapping = map_sequence(sequence, {"P1": region}, "P1", 1, len(region))
    return [(o["start"], o["stop"], o["identity"]) for o in occurrences(mapping).get("P1", [])]


def test_every_exact_match_is_kept():
    region = "GGGG" + MOTIF + "GGGG" + MOTIF
    assert placements(MOTIF, region) == [(5, 19, 100), (24, 38, 100)]


def test_overlapping_exact_matches_are_one_cluster_its_first():
    # EEE in seven E: five overlapping matches, chained into one cluster
    assert placements("EEE", "AEEEEEEEA") == [(2, 4, 100)]


def test_every_non_overlapping_tie_is_kept():
    region = "GGGG" + MOTIF + "GGGG" + MOTIF + "GGGG" + MOTIF + "GGGG"
    assert placements(MUTANT, region) == [(5, 19, 93.33333), (24, 38, 93.33333), (43, 57, 93.33333)]


def test_a_lower_score_is_dropped_even_at_the_same_identity():
    similar = "PEPTIDEKIMNQRST"  # L faces I: one mismatch, a similar residue
    distant = "PEPTIDEKWMNQRST"  # L faces W: one mismatch, a distant residue
    region = "GGGG" + distant + "GGGG" + similar + "GGGG"
    assert placements(MOTIF, region) == [(24, 38, 93.33333)]


def test_one_stretch_read_two_ways_is_one_occurrence_its_first():
    # Q96IP4: 7-36 with a mismatch on the first residue, or 8-36 with a gap: same score
    mapping = "DFGGGDFGGGDFGGGDFGGGDFGGGGSFGG"
    region = "LACSPYIPLGGDFGGGDFGGGDFGGGDFGGGGSFGGHCLDY"
    assert placements(mapping, region) == [(7, 36, 90.0)]


def test_a_chain_of_overlapping_placements_is_one_cluster_its_first():
    # P0CG48: two repeat units and a residue of the construct fit on every two adjacent units
    unit = "MQIFVKTLTG"
    assert placements(unit + unit + "C", unit * 4) == [(1, 21, 95.2381)]


def test_only_the_isoforms_with_the_best_score_are_kept():
    isoforms = {"P1": "AAAA" + MUTANT + "AAAA", "P1-2": "CC" + MOTIF, "P1-3": MOTIF}
    mapping = map_sequence(MOTIF, isoforms, "P1", 1, 23)
    assert occurrences(mapping) == {
        "P1-2": [{"start": 3, "stop": 17, "identity": 100}],
        "P1-3": [{"start": 1, "stop": 15, "identity": 100}],
    }


def test_canonical_positions_are_relative_to_the_interactor():
    isoforms = {"P1": "AAAA" + MOTIF + "AAAA", "P1-2": "AAAA" + MOTIF}
    mapping = map_sequence(MOTIF, isoforms, "P1", 3, 23)
    assert occurrences(mapping) == {
        "P1": [{"start": 3, "stop": 17, "identity": 100}],
        "P1-2": [{"start": 5, "stop": 19, "identity": 100}],
    }


def test_a_mapping_below_the_threshold_keeps_its_best_occurrences():
    mapping = map_sequence("PEPWWWWWWW", {"P1": MOTIF}, "P1", 1, 15)
    assert mapping["isoforms"] and best_identity(mapping) < 90


def test_a_selenocysteine_is_aligned():
    # U is not in BLOSUM62: aligned as X, it still counts as identical to itself
    region = "GGGG" + "PEPUIDEKLMNQRST" + "GGGG"
    assert placements("PEPUIDEKLWNQRST", region) == [(5, 19, 93.33333)]


def test_extra_end_residues_are_written_in_lowercase():
    assert read_written("mgsPEPTIDEhhh") == ("MGSPEPTIDEHHH", "MGS", "HHH")
    assert read_written(MOTIF) == (MOTIF, "", "")
    with pytest.raises(ValueError):
        read_written("PEPtideKL")
    mapping: dict[str, Any] = {"sequence": "MGSPEPTIDEHHH", "nter": "MGS", "cter": "HHH"}
    assert written(mapping) == "mgsPEPTIDEhhh"
    assert core(mapping) == "PEPTIDE"


def test_extra_end_residues_are_left_out_of_the_occurrences():
    mapping = map_sequence("M" + MOTIF, {"P1": "AAAA" + MOTIF}, "P1", 5, 19, nter="M")
    assert mapping == {
        "sequence": "M" + MOTIF,
        "nter": "M",
        "isoforms": [
            {"accession": "P1", "occurrences": [{"start": 1, "stop": 15, "identity": 100}]}
        ],
    }

"""Mapping occurrences: where a mapping sequence is found on the isoforms of an interactor.

Identity is identical residues over the alignment length: the mapping plus the protein residues
facing a gap inside it (`docs/glossary.md`). Alignment: BLOSUM62, gaps -10/-2.
"""

from functools import cache
from typing import Any

from Bio import Align
from Bio.Align import substitution_matrices

MIN_IDENTITY = 90.0  # C4


def _aligner(overhang: bool) -> Any:  # Biopython is not fully typed
    # The whole mapping is aligned (global); with `overhang`, the protein may extend beyond both
    # ends of the mapping for free.
    aligner = Align.PairwiseAligner(mode="global")
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")  # type: ignore
    aligner.open_gap_score = -10
    aligner.extend_gap_score = -2  # long gaps cost more than a few mismatches
    if overhang:
        aligner.end_deletion_score = 0  # protein residues outside the mapping
    return aligner


ALIGNER: Any = _aligner(overhang=True)
SEGMENT_ALIGNER: Any = _aligner(overhang=False)  # a fixed segment: aligned end to end


@cache
def segment_identity(sequence: str, segment: str) -> float:
    """Identity of a mapping aligned end to end on the protein segment of an occurrence."""
    if sequence == segment:
        return 100.0
    alignment: Any = SEGMENT_ALIGNER.align(segment, sequence)[0]
    counts: Any = alignment.counts()
    columns = len(sequence) + counts.deletions
    return round(100 * counts.identities / columns, 5)


def best_matches(sequence: str, region: str) -> list[dict[str, Any]]:
    """Occurrences of a mapping on one sequence: every exact match, else the best alignment."""
    occurrences: list[dict[str, Any]] = []
    position = region.find(sequence)
    while position != -1:
        occurrences.append(
            {"start": position + 1, "stop": position + len(sequence), "identity": 100}
        )
        position = region.find(sequence, position + 1)
    if occurrences:
        return occurrences
    alignment: Any = ALIGNER.align(region, sequence)[0]
    counts: Any = alignment.counts()
    identity: float = round(
        100 * counts.identities / (len(sequence) + counts.internal_deletions), 5
    )
    blocks = alignment.aligned[0]  # aligned blocks on the region
    return [{"start": int(blocks[0][0]) + 1, "stop": int(blocks[-1][1]), "identity": identity}]


def map_sequence(
    sequence: str,
    isoforms: dict[str, str],
    canonical: str,
    start: int,
    stop: int,
    min_identity: float = MIN_IDENTITY,
) -> dict[str, Any]:
    """Mapping JSON for one sequence: its occurrences on each isoform of the interactor.

    Positions on the canonical isoform are relative to the region [start, stop], positions on
    other isoforms to the whole isoform (as checked by D9). On each isoform, the best matches
    are kept if they reach `min_identity`.
    """
    found: list[dict[str, Any]] = []
    for isoform, full in sorted(isoforms.items()):
        region = full[start - 1 : stop] if isoform == canonical else full
        occurrences = [o for o in best_matches(sequence, region) if o["identity"] >= min_identity]
        if occurrences:
            found.append({"accession": isoform, "occurrences": occurrences})
    return {"sequence": sequence, "isoforms": found}

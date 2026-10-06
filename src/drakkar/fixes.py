"""Corrections of the database, outside the curation route (`docs/02-data-fixes.md`).

Each function writes one fix approved by the user, and refuses rows it does not expect. Nothing is
committed: the caller commits once the user approved the write, or rolls back (dry run).
"""

import json
import re
from typing import Any, cast

from drakkar.check import OCCURRENCE_KEYS, mapping_structure

POSITION = re.compile(r"\d+")
IDENTITY = re.compile(r"\d+(\.\d+)?")

# Rows (any version, live or deleted) with an occurrence number stored as text.
TEXT_NUMBERS = """
    SELECT id, stable_id, version, deleted_at IS NULL, mapping1::text, mapping2::text
    FROM descriptions
    WHERE mapping1::text ~ '"(start|stop|identity)" *: *"'
       OR mapping2::text ~ '"(start|stop|identity)" *: *"'
    ORDER BY id
    FOR UPDATE
"""


def _compact(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _as_number(key: str, value: Any) -> tuple[Any, bool]:
    """The value as a JSON number with the same digits, and whether it was text.

    `"204"` becomes `204`, `"99.72973"` becomes `99.72973` and `"100"` becomes `100`: positions
    are integers, identities keep their digits. Refuses a text whose digits would change.
    """
    if not isinstance(value, str):
        return value, False
    pattern = IDENTITY if key == "identity" else POSITION
    if not pattern.fullmatch(value):
        raise ValueError(f"{key} {value!r} is not a number stored as text")
    number = int(value) if POSITION.fullmatch(value) else float(value)
    if json.dumps(number) != value:
        raise ValueError(f"{key} {value!r} would be written {json.dumps(number)}")
    return number, True


def _convert(text: str) -> tuple[str, int]:
    """A mapping column with its text numbers as numbers, and the count of converted values.

    Refuses a column whose JSON is not compact (the rewrite would change more than the numbers)
    or whose structure is wrong for another reason than text numbers.
    """
    mappings: Any = json.loads(text)
    if _compact(mappings) != text:
        raise ValueError("the JSON is not compact: rewriting it would change more than numbers")
    if problems := mapping_structure(mappings, strict=False):
        raise ValueError(f"malformed beyond text numbers: {problems}")
    converted = 0
    for mapping in cast(list[dict[str, Any]], mappings):
        for isoform in mapping["isoforms"]:
            for occurrence in isoform["occurrences"]:
                for key in OCCURRENCE_KEYS:
                    occurrence[key], changed = _as_number(key, occurrence[key])
                    converted += changed
    if problems := mapping_structure(mappings):
        raise ValueError(f"still malformed after the conversion: {problems}")
    return _compact(mappings), converted


def fix_mapping_numbers(cur: Any) -> list[tuple[Any, ...]]:
    """Turn occurrence numbers stored as text into numbers, in place, in every version.

    Not a revision: no new version, no other column changes (`docs/database.md` §2). The quotes
    are removed and the digits kept, so each value is written exactly as before. Returns one
    report row per rewritten column: (row id, stable ID, version, live, column, values converted,
    before, after).
    Raises `ValueError` before writing anything if a row is not as expected.
    """
    cur.execute(TEXT_NUMBERS)
    updates: list[tuple[Any, ...]] = []
    for id_, stable_id, version, live, mapping1, mapping2 in cur.fetchall():
        for column, text in (("mapping1", mapping1), ("mapping2", mapping2)):
            if text is None or not re.search(r'"(start|stop|identity)" *: *"', text):
                continue
            try:
                new, converted = _convert(text)
            except ValueError as e:
                raise ValueError(f"{stable_id} version {version} {column}: {e}") from e
            updates.append((id_, stable_id, version, live, column, converted, text, new))
    for id_, _, _, _, column, _, _, new in updates:
        cur.execute(f"UPDATE descriptions SET {column} = %s::json WHERE id = %s", (new, id_))
    return updates

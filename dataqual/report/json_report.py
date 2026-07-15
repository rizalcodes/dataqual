"""JSON report for downstream tooling."""

import json
from dataclasses import asdict
from pathlib import Path

from dataqual.checks.duplicates import DuplicateStats
from dataqual.checks.missing import MissingStats
from dataqual.checks.outliers import OutlierStats
from dataqual.checks.types import TypeStats


def build_report(
    source: str,
    missing: list[MissingStats],
    duplicates: DuplicateStats,
    types: list[TypeStats],
    outliers: list[OutlierStats],
) -> dict:
    """Assemble all check results into one JSON-serializable dict."""
    return {
        "source": source,
        "summary": {
            "missing_values": sum(s.missing_count for s in missing),
            "duplicate_rows": duplicates.duplicate_count,
            "type_mismatches": sum(s.mismatch_count for s in types),
            "outliers": sum(s.outlier_count for s in outliers),
        },
        "missing": [asdict(s) for s in missing],
        "duplicates": asdict(duplicates),
        "types": [asdict(s) for s in types],
        "outliers": [asdict(s) for s in outliers],
    }


def generate_json_report(
    source: str,
    missing: list[MissingStats],
    duplicates: DuplicateStats,
    types: list[TypeStats],
    outliers: list[OutlierStats],
    output_path: str | Path | None = None,
) -> str:
    """Serialize all check results to JSON.

    Writes to output_path when given (the primary path, matching the HTML
    report); always returns the JSON string so callers can print it instead.
    """
    text = json.dumps(
        build_report(source, missing, duplicates, types, outliers), indent=2
    )
    if output_path is not None:
        Path(output_path).write_text(text + "\n", encoding="utf-8")
    return text

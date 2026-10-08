from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data" / "thermodynamic_tables.sqlite"
EXPECTED_ROWS = {
    "saturated_water": 793,
    "superheated_compressed": 22122,
    "inference_audit": 1841,
}
REQUIRED_TABLES = set(EXPECTED_ROWS) | {"metadata"}


def missing(value: object) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return not text or text.upper().startswith("REVISAR")


def saturated_missing(connection: sqlite3.Connection) -> int:
    fields = ("T_C", "P_bar", "h_f", "h_fg", "h_g", "s_f", "s_fg", "s_g")
    json_fields = ("rho_l", "rho_g", "v_l_impreso", "v_g_impreso")
    count = 0
    for row in connection.execute("SELECT * FROM saturated_water ORDER BY id"):
        if any(missing(row[field]) for field in fields):
            count += 1
            continue
        original = json.loads(row["original_json"])["original_values"]
        if any(missing(original.get(field)) for field in json_fields):
            count += 1
    return count


def monotonic_violations(connection: sqlite3.Connection) -> int:
    rows = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM superheated_compressed ORDER BY id"
        )
    ]
    saturation_temperatures: dict[tuple[str, str], list[float]] = defaultdict(list)
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (str(row["source_pdf"]), str(row["P_bar"]))
        notes = str(row["notes"] or "")
        if "fila_saturacion_" in notes:
            saturation_temperatures[key].append(float(row["T_C"]))
        else:
            groups[key].append(row)

    saturation_temperature = {
        key: sum(values) / len(values)
        for key, values in saturation_temperatures.items()
    }
    violations = 0
    for key, group in groups.items():
        segments: list[list[dict[str, object]]] = []
        segment: list[dict[str, object]] = []
        previous_temperature: float | None = None
        for row in group:
            temperature = float(row["T_C"])
            if segment and previous_temperature is not None and temperature <= previous_temperature:
                segments.append(segment)
                segment = []
            segment.append(row)
            previous_temperature = temperature
        if segment:
            segments.append(segment)

        for segment in segments:
            boundary = saturation_temperature.get(key)
            phases = [segment]
            if boundary is not None:
                phases = [
                    [row for row in segment if float(row["T_C"]) < boundary],
                    [row for row in segment if float(row["T_C"]) >= boundary],
                ]
            for phase in phases:
                for field in ("h_kJkg", "s_kJkgK"):
                    for left, right in zip(phase, phase[1:]):
                        if float(right[field]) < float(left[field]):
                            violations += 1
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida la base termodinámica SQLite.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    database = args.database.resolve()
    if not database.is_file():
        parser.error(f"No existe la base: {database}")

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        missing_tables = sorted(REQUIRED_TABLES - tables)
        counts = {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in EXPECTED_ROWS
            if table in tables
        }
        wrong_counts = {
            table: {"expected": EXPECTED_ROWS[table], "actual": counts.get(table)}
            for table in EXPECTED_ROWS
            if counts.get(table) != EXPECTED_ROWS[table]
        }

        stage_missing = None
        saturation_missing_count = None
        monotonic_count = None
        if "superheated_compressed" in tables:
            stage_missing = connection.execute(
                """
                SELECT COUNT(*)
                FROM superheated_compressed
                WHERE T_C IS NULL OR TRIM(T_C) = '' OR UPPER(TRIM(T_C)) LIKE 'REVISAR%'
                   OR h_kJkg IS NULL OR TRIM(h_kJkg) = '' OR UPPER(TRIM(h_kJkg)) LIKE 'REVISAR%'
                   OR s_kJkgK IS NULL OR TRIM(s_kJkgK) = '' OR UPPER(TRIM(s_kJkgK)) LIKE 'REVISAR%'
                """
            ).fetchone()[0]
            monotonic_count = monotonic_violations(connection)
        if "saturated_water" in tables:
            saturation_missing_count = saturated_missing(connection)

        result = {
            "database": str(database),
            "integrity_check": integrity,
            "tables_missing": missing_tables,
            "row_counts": counts,
            "wrong_row_counts": wrong_counts,
            "missing_rows_superheated_compressed": stage_missing,
            "missing_rows_saturated_water": saturation_missing_count,
            "monotonic_violations": monotonic_count,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        valid = (
            integrity == "ok"
            and not missing_tables
            and not wrong_counts
            and stage_missing == 0
            and saturation_missing_count == 0
            and monotonic_count == 0
        )
        print("VALIDACIÓN: OK" if valid else "VALIDACIÓN: ERROR")
        return 0 if valid else 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data" / "thermodynamic_tables.sqlite"
DEFAULT_OUTPUT = ROOT / "exports"
TABLES = (
    "saturated_water",
    "superheated_compressed",
    "inference_audit",
    "metadata",
)


def export_table(connection: sqlite3.Connection, table: str, output: Path) -> int:
    cursor = connection.execute(f'SELECT * FROM "{table}"')
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    path = output / f"{table}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta las tablas SQLite a CSV.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    database = args.database.resolve()
    output = args.output.resolve()
    if not database.is_file():
        parser.error(f"No existe la base: {database}")
    output.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database)
    try:
        available = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        for table in TABLES:
            if table not in available:
                print(f"OMITIDA {table}: tabla inexistente")
                continue
            count = export_table(connection, table, output)
            print(f"EXPORTADA {table}: {count} filas")
    finally:
        connection.close()

    print(f"Destino: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

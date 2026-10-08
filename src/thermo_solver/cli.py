from __future__ import annotations

import argparse
import json
from pathlib import Path

from .database import ThermoDatabase
from .rankine import solve_rankine_ideal
from .report import rankine_text, write_lookup_report, write_rankine_report


def cmd_validate(args: argparse.Namespace) -> int:
    db = ThermoDatabase(args.database)
    with db.connect() as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        counts = {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in ("saturated_water", "superheated_compressed", "inference_audit")
        }
    print(json.dumps({"database": str(db.path), "integrity": integrity, "rows": counts}, indent=2))
    return 0 if integrity == "ok" else 1


def cmd_lookup_sat(args: argparse.Namespace) -> int:
    db = ThermoDatabase(args.database)
    result = db.saturation_by_pressure(args.pressure)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if args.output:
        write_lookup_report(
            title="Consulta de saturación",
            summary_lines=[
                f"- P = **{result.P_bar:g} bar**",
                f"- T_sat = **{result.T_C:.6g} °C**",
                f"- h_f = **{result.h_f:.6g} kJ/kg**",
                f"- h_g = **{result.h_g:.6g} kJ/kg**",
                f"- s_f = **{result.s_f:.6g} kJ/(kg·K)**",
                f"- s_g = **{result.s_g:.6g} kJ/(kg·K)**",
            ],
            events=result.events,
            output_dir=args.output,
            payload=result.to_dict(),
        )
        print(f"Reporte: {Path(args.output).resolve() / 'lookup.md'}")
    return 0


def cmd_lookup_pt(args: argparse.Namespace) -> int:
    db = ThermoDatabase(args.database)
    result = db.pt(args.pressure, args.temperature)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if args.output:
        write_lookup_report(
            title="Consulta P-T",
            summary_lines=[
                f"- P = **{result.P_bar:g} bar**",
                f"- T = **{result.T_C:g} °C**",
                f"- Fase = **{result.phase}**",
                f"- h = **{result.h_kJkg:.6g} kJ/kg**",
                f"- s = **{result.s_kJkgK:.6g} kJ/(kg·K)**",
            ],
            events=result.events,
            output_dir=args.output,
            payload=result.to_dict(),
        )
        print(f"Reporte: {Path(args.output).resolve() / 'lookup.md'}")
    return 0


def cmd_rankine(args: argparse.Namespace) -> int:
    db = ThermoDatabase(args.database)
    result = solve_rankine_ideal(
        boiler_pressure_bar=args.boiler_bar,
        condenser_pressure_bar=args.condenser_bar,
        turbine_inlet_temperature_C=args.turbine_inlet_c,
        database=db,
    )
    print(rankine_text(result))
    if args.output:
        path = write_rankine_report(result, args.output)
        print(f"\nReporte guardado en: {path.resolve()}")
    return 0



def cmd_solve_json(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    cycle = payload.get("cycle")
    if cycle != "rankine_ideal":
        raise SystemExit(f"Ciclo no soportado todavía: {cycle!r}")
    db = ThermoDatabase(args.database)
    result = solve_rankine_ideal(
        boiler_pressure_bar=float(payload["boiler_pressure_bar"]),
        condenser_pressure_bar=float(payload["condenser_pressure_bar"]),
        turbine_inlet_temperature_C=float(payload["turbine_inlet_temperature_C"]),
        database=db,
    )
    print(rankine_text(result))
    if args.output:
        path = write_rankine_report(result, args.output)
        print(f"\nReporte guardado en: {path.resolve()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thermo-solver",
        description="Consultas termodinámicas y solver Rankine sobre la base SQLite del repositorio.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Ruta alternativa a thermodynamic_tables.sqlite.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="Comprueba integridad SQLite y conteos básicos.")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("lookup-sat", help="Consulta saturación por presión.")
    p.add_argument("--pressure", type=float, required=True, help="Presión en bar.")
    p.add_argument("--output", type=Path, help="Carpeta para reporte Markdown/SVG/JSON.")
    p.set_defaults(func=cmd_lookup_sat)

    p = sub.add_parser("lookup-pt", help="Consulta propiedades mediante P y T.")
    p.add_argument("--pressure", type=float, required=True, help="Presión en bar.")
    p.add_argument("--temperature", type=float, required=True, help="Temperatura en °C.")
    p.add_argument("--output", type=Path, help="Carpeta para reporte Markdown/SVG/JSON.")
    p.set_defaults(func=cmd_lookup_pt)

    p = sub.add_parser("rankine", help="Resuelve un ciclo Rankine ideal simple.")
    p.add_argument("--boiler-bar", type=float, required=True, help="Presión de caldera en bar.")
    p.add_argument("--condenser-bar", type=float, required=True, help="Presión de condensador en bar.")
    p.add_argument("--turbine-inlet-c", type=float, required=True, help="Temperatura a la entrada de turbina en °C.")
    p.add_argument("--output", type=Path, help="Carpeta para solution.md, solution.txt, JSON y SVG.")
    p.set_defaults(func=cmd_rankine)

    p = sub.add_parser("solve-json", help="Resuelve un problema estructurado en JSON.")
    p.add_argument("--input", type=Path, required=True, help="Archivo JSON de entrada.")
    p.add_argument("--output", type=Path, help="Carpeta para solution.md, solution.txt, JSON y SVG.")
    p.set_defaults(func=cmd_solve_json)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .interpolation import InterpolationError, linear_interpolate
from .models import InterpolationEvent, PSProperties, PTProperties, SaturationProperties


class PropertyLookupError(RuntimeError):
    pass


def default_database_path() -> Path:
    env = os.environ.get("THERMO_DB_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "data" / "thermodynamic_tables.sqlite"


def _f(value: object) -> float:
    return float(str(value).strip())


class ThermoDatabase:
    """Acceso reproducible a la base SQLite incluida en el repositorio."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path).resolve() if path else default_database_path()
        if not self.path.is_file():
            raise FileNotFoundError(f"No existe la base termodinámica: {self.path}")

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _sat_from_row(row: sqlite3.Row) -> SaturationProperties:
        raw = json.loads(row["original_json"])
        original = raw.get("original_values", {})
        rho_l = original.get("rho_l")
        rho_g = original.get("rho_g")
        return SaturationProperties(
            P_bar=_f(row["P_bar"]),
            T_C=_f(row["T_C"]),
            h_f=_f(row["h_f"]),
            h_fg=_f(row["h_fg"]),
            h_g=_f(row["h_g"]),
            s_f=_f(row["s_f"]),
            s_fg=_f(row["s_fg"]),
            s_g=_f(row["s_g"]),
            rho_l=_f(rho_l) if rho_l not in (None, "") else None,
            rho_g=_f(rho_g) if rho_g not in (None, "") else None,
            method="exact",
        )

    def _saturation_row_at_pressure(self, connection: sqlite3.Connection, pressure: float) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT *
            FROM saturated_water
            WHERE ABS(CAST(P_bar AS REAL) - ?) <= ?
            ORDER BY id
            LIMIT 1
            """,
            (pressure, max(1e-10, abs(pressure) * 1e-10)),
        ).fetchone()

    def saturation_by_pressure(self, pressure_bar: float) -> SaturationProperties:
        pressure = float(pressure_bar)
        with self.connect() as connection:
            row = self._saturation_row_at_pressure(connection, pressure)
            if row is not None:
                return self._sat_from_row(row)

            lower = connection.execute(
                """
                SELECT * FROM saturated_water
                WHERE CAST(P_bar AS REAL) < ?
                ORDER BY CAST(P_bar AS REAL) DESC, id ASC
                LIMIT 1
                """,
                (pressure,),
            ).fetchone()
            upper = connection.execute(
                """
                SELECT * FROM saturated_water
                WHERE CAST(P_bar AS REAL) > ?
                ORDER BY CAST(P_bar AS REAL) ASC, id ASC
                LIMIT 1
                """,
                (pressure,),
            ).fetchone()

        if lower is None or upper is None:
            raise PropertyLookupError(
                f"P={pressure:g} bar queda fuera del rango de saturación disponible."
            )

        a = self._sat_from_row(lower)
        b = self._sat_from_row(upper)
        events: list[InterpolationEvent] = []

        def interp(name: str, y1: float, y2: float, unit: str) -> float:
            event = linear_interpolate(
                x=pressure,
                x1=a.P_bar,
                y1=y1,
                x2=b.P_bar,
                y2=y2,
                property_name=name,
                x_name="P",
                x_unit="bar",
                y_unit=unit,
                note="Tabla de saturación por presión",
            )
            events.append(event)
            return event.result

        rho_l = None
        if a.rho_l is not None and b.rho_l is not None:
            rho_l = interp("rho_l", a.rho_l, b.rho_l, "kg/m³")
        rho_g = None
        if a.rho_g is not None and b.rho_g is not None:
            rho_g = interp("rho_g", a.rho_g, b.rho_g, "kg/m³")

        return SaturationProperties(
            P_bar=pressure,
            T_C=interp("T_sat", a.T_C, b.T_C, "°C"),
            h_f=interp("h_f", a.h_f, b.h_f, "kJ/kg"),
            h_fg=interp("h_fg", a.h_fg, b.h_fg, "kJ/kg"),
            h_g=interp("h_g", a.h_g, b.h_g, "kJ/kg"),
            s_f=interp("s_f", a.s_f, b.s_f, "kJ/(kg·K)"),
            s_fg=interp("s_fg", a.s_fg, b.s_fg, "kJ/(kg·K)"),
            s_g=interp("s_g", a.s_g, b.s_g, "kJ/(kg·K)"),
            rho_l=rho_l,
            rho_g=rho_g,
            method="interpolated",
            events=events,
        )

    def _available_superheated_pressures(self, connection: sqlite3.Connection) -> list[float]:
        return [
            float(row[0])
            for row in connection.execute(
                """
                SELECT DISTINCT CAST(P_bar AS REAL) AS p
                FROM superheated_compressed
                ORDER BY p
                """
            )
        ]

    def _phase_at_pt(self, pressure: float, temperature: float) -> str:
        try:
            sat = self.saturation_by_pressure(pressure)
        except PropertyLookupError:
            return "supercritical_or_single_phase"
        tol = 1e-6
        if temperature < sat.T_C - tol:
            return "compressed_liquid"
        if temperature > sat.T_C + tol:
            return "superheated_vapor"
        return "saturation_boundary"

    def _rows_at_pressure(self, connection: sqlite3.Connection, pressure: float) -> list[sqlite3.Row]:
        rows = connection.execute(
            """
            SELECT * FROM superheated_compressed
            WHERE ABS(CAST(P_bar AS REAL) - ?) <= ?
              AND notes NOT LIKE '%fila_saturacion_%'
            ORDER BY CAST(T_C AS REAL), id
            """,
            (pressure, max(1e-10, abs(pressure) * 1e-10)),
        ).fetchall()

        # Deduplicar T conservando la primera fila del conjunto fuente.
        by_temperature: dict[float, sqlite3.Row] = {}
        for row in rows:
            by_temperature.setdefault(_f(row["T_C"]), row)
        return [by_temperature[t] for t in sorted(by_temperature)]

    def _filter_rows_for_phase(
        self,
        rows: list[sqlite3.Row],
        pressure: float,
        target_phase: str,
    ) -> list[sqlite3.Row]:
        if target_phase not in {"compressed_liquid", "superheated_vapor"}:
            return rows
        try:
            sat = self.saturation_by_pressure(pressure)
        except PropertyLookupError:
            return rows
        if target_phase == "compressed_liquid":
            return [row for row in rows if _f(row["T_C"]) < sat.T_C]
        return [row for row in rows if _f(row["T_C"]) > sat.T_C]

    def _pt_at_exact_pressure(
        self,
        connection: sqlite3.Connection,
        *,
        pressure: float,
        temperature: float,
        target_phase: str,
    ) -> PTProperties:
        rows = self._filter_rows_for_phase(
            self._rows_at_pressure(connection, pressure), pressure, target_phase
        )
        if not rows:
            raise PropertyLookupError(f"No hay filas útiles a P={pressure:g} bar.")

        tol = max(1e-9, abs(temperature) * 1e-10)
        for row in rows:
            if abs(_f(row["T_C"]) - temperature) <= tol:
                return PTProperties(
                    P_bar=pressure,
                    T_C=temperature,
                    h_kJkg=_f(row["h_kJkg"]),
                    s_kJkgK=_f(row["s_kJkgK"]),
                    phase=target_phase,
                    method="exact",
                    events=[],
                )

        lower = None
        upper = None
        for row in rows:
            t = _f(row["T_C"])
            if t < temperature:
                lower = row
            elif t > temperature and upper is None:
                upper = row
                break

        if lower is None or upper is None:
            tmin = _f(rows[0]["T_C"])
            tmax = _f(rows[-1]["T_C"])
            raise PropertyLookupError(
                f"T={temperature:g} °C queda fuera del intervalo disponible "
                f"[{tmin:g}, {tmax:g}] °C a P={pressure:g} bar."
            )

        t1, t2 = _f(lower["T_C"]), _f(upper["T_C"])
        h_event = linear_interpolate(
            x=temperature,
            x1=t1,
            y1=_f(lower["h_kJkg"]),
            x2=t2,
            y2=_f(upper["h_kJkg"]),
            property_name="h",
            x_name="T",
            x_unit="°C",
            y_unit="kJ/kg",
            note=f"P={pressure:g} bar",
        )
        s_event = linear_interpolate(
            x=temperature,
            x1=t1,
            y1=_f(lower["s_kJkgK"]),
            x2=t2,
            y2=_f(upper["s_kJkgK"]),
            property_name="s",
            x_name="T",
            x_unit="°C",
            y_unit="kJ/(kg·K)",
            note=f"P={pressure:g} bar",
        )
        return PTProperties(
            P_bar=pressure,
            T_C=temperature,
            h_kJkg=h_event.result,
            s_kJkgK=s_event.result,
            phase=target_phase,
            method="temperature_interpolation",
            events=[h_event, s_event],
        )

    def pt(self, pressure_bar: float, temperature_C: float) -> PTProperties:
        pressure = float(pressure_bar)
        temperature = float(temperature_C)
        target_phase = self._phase_at_pt(pressure, temperature)
        if target_phase == "saturation_boundary":
            raise PropertyLookupError(
                "El punto cae sobre saturación. Use saturation_by_pressure() y especifique líquido/vapor/calidad."
            )

        with self.connect() as connection:
            pressures = self._available_superheated_pressures(connection)
            exact = next(
                (p for p in pressures if abs(p - pressure) <= max(1e-10, abs(pressure) * 1e-10)),
                None,
            )
            if exact is not None:
                return self._pt_at_exact_pressure(
                    connection,
                    pressure=exact,
                    temperature=temperature,
                    target_phase=target_phase,
                )

            lower_candidates = [p for p in pressures if p < pressure]
            upper_candidates = [p for p in pressures if p > pressure]
            if not lower_candidates or not upper_candidates:
                raise PropertyLookupError(
                    f"P={pressure:g} bar queda fuera del rango de la tabla P-T."
                )

            left: PTProperties | None = None
            right: PTProperties | None = None
            left_pressure = None
            right_pressure = None

            for p in reversed(lower_candidates):
                anchor_phase = self._phase_at_pt(p, temperature)
                if target_phase in {"compressed_liquid", "superheated_vapor"} and anchor_phase != target_phase:
                    continue
                try:
                    left = self._pt_at_exact_pressure(
                        connection,
                        pressure=p,
                        temperature=temperature,
                        target_phase=target_phase,
                    )
                    left_pressure = p
                    break
                except PropertyLookupError:
                    continue

            for p in upper_candidates:
                anchor_phase = self._phase_at_pt(p, temperature)
                if target_phase in {"compressed_liquid", "superheated_vapor"} and anchor_phase != target_phase:
                    continue
                try:
                    right = self._pt_at_exact_pressure(
                        connection,
                        pressure=p,
                        temperature=temperature,
                        target_phase=target_phase,
                    )
                    right_pressure = p
                    break
                except PropertyLookupError:
                    continue

        if left is None or right is None or left_pressure is None or right_pressure is None:
            raise PropertyLookupError(
                "No se encontraron dos presiones vecinas compatibles para interpolación bilineal."
            )

        h_event = linear_interpolate(
            x=pressure,
            x1=left_pressure,
            y1=left.h_kJkg,
            x2=right_pressure,
            y2=right.h_kJkg,
            property_name="h",
            x_name="P",
            x_unit="bar",
            y_unit="kJ/kg",
            note=f"Después de evaluar T={temperature:g} °C en ambas presiones",
        )
        s_event = linear_interpolate(
            x=pressure,
            x1=left_pressure,
            y1=left.s_kJkgK,
            x2=right_pressure,
            y2=right.s_kJkgK,
            property_name="s",
            x_name="P",
            x_unit="bar",
            y_unit="kJ/(kg·K)",
            note=f"Después de evaluar T={temperature:g} °C en ambas presiones",
        )
        return PTProperties(
            P_bar=pressure,
            T_C=temperature,
            h_kJkg=h_event.result,
            s_kJkgK=s_event.result,
            phase=target_phase,
            method="bilinear_interpolation",
            events=[*left.events, *right.events, h_event, s_event],
        )

    def ps(self, pressure_bar: float, entropy_kJkgK: float) -> PSProperties:
        pressure = float(pressure_bar)
        entropy = float(entropy_kJkgK)
        sat = self.saturation_by_pressure(pressure)
        sat_events = list(sat.events)

        tol = 1e-9
        if sat.s_f - tol <= entropy <= sat.s_g + tol:
            x = (entropy - sat.s_f) / sat.s_fg
            x = min(1.0, max(0.0, x))
            h = sat.h_f + x * sat.h_fg
            return PSProperties(
                P_bar=pressure,
                s_kJkgK=entropy,
                h_kJkg=h,
                T_C=sat.T_C,
                phase="two_phase_mixture",
                x=x,
                method="quality_from_entropy",
                events=sat_events,
            )

        target_phase = "superheated_vapor" if entropy > sat.s_g else "compressed_liquid"
        with self.connect() as connection:
            rows = self._filter_rows_for_phase(
                self._rows_at_pressure(connection, pressure), pressure, target_phase
            )
        if not rows:
            raise PropertyLookupError(
                f"No hay datos P-s para P={pressure:g} bar en fase {target_phase}."
            )

        rows = sorted(rows, key=lambda row: _f(row["s_kJkgK"]))
        for row in rows:
            s = _f(row["s_kJkgK"])
            if abs(s - entropy) <= max(1e-10, abs(entropy) * 1e-10):
                return PSProperties(
                    P_bar=pressure,
                    s_kJkgK=entropy,
                    h_kJkg=_f(row["h_kJkg"]),
                    T_C=_f(row["T_C"]),
                    phase=target_phase,
                    method="exact",
                    events=sat_events,
                )

        lower = None
        upper = None
        for row in rows:
            s = _f(row["s_kJkgK"])
            if s < entropy:
                lower = row
            elif s > entropy and upper is None:
                upper = row
                break
        if lower is None or upper is None:
            raise PropertyLookupError(
                f"s={entropy:g} kJ/(kg·K) queda fuera del rango disponible a P={pressure:g} bar."
            )

        s1, s2 = _f(lower["s_kJkgK"]), _f(upper["s_kJkgK"])
        h_event = linear_interpolate(
            x=entropy,
            x1=s1,
            y1=_f(lower["h_kJkg"]),
            x2=s2,
            y2=_f(upper["h_kJkg"]),
            property_name="h",
            x_name="s",
            x_unit="kJ/(kg·K)",
            y_unit="kJ/kg",
            note=f"P={pressure:g} bar",
        )
        t_event = linear_interpolate(
            x=entropy,
            x1=s1,
            y1=_f(lower["T_C"]),
            x2=s2,
            y2=_f(upper["T_C"]),
            property_name="T",
            x_name="s",
            x_unit="kJ/(kg·K)",
            y_unit="°C",
            note=f"P={pressure:g} bar",
        )
        return PSProperties(
            P_bar=pressure,
            s_kJkgK=entropy,
            h_kJkg=h_event.result,
            T_C=t_event.result,
            phase=target_phase,
            method="entropy_interpolation",
            events=[*sat_events, h_event, t_event],
        )

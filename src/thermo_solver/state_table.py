from __future__ import annotations

from .models import StatePoint


def _fmt(value: float | None, digits: int = 6) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}g}"


def markdown_state_table(states: list[StatePoint]) -> str:
    lines = [
        "| Estado | P (bar) | T (°C) | x | h (kJ/kg) | s (kJ/kg·K) | v (m³/kg) | Fase |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for s in states:
        lines.append(
            "| {n} | {p} | {t} | {x} | {h} | {ent} | {v} | {phase} |".format(
                n=s.number,
                p=_fmt(s.P_bar),
                t=_fmt(s.T_C),
                x=_fmt(s.x),
                h=_fmt(s.h_kJkg),
                ent=_fmt(s.s_kJkgK),
                v=_fmt(s.v_m3kg),
                phase=s.phase or "—",
            )
        )
    return "\n".join(lines)


def text_state_table(states: list[StatePoint]) -> str:
    headers = ["E", "P(bar)", "T(°C)", "x", "h(kJ/kg)", "s(kJ/kgK)", "v(m3/kg)", "fase"]
    rows = [headers]
    for s in states:
        rows.append(
            [
                str(s.number),
                _fmt(s.P_bar),
                _fmt(s.T_C),
                _fmt(s.x),
                _fmt(s.h_kJkg),
                _fmt(s.s_kJkgK),
                _fmt(s.v_m3kg),
                s.phase or "—",
            ]
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    return "\n".join(
        "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) for row in rows
    )

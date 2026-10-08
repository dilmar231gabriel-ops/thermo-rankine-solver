from __future__ import annotations

import json
from pathlib import Path

from .interpolation import ascii_diagram, interpolation_text, render_svg
from .models import InterpolationEvent, PTProperties, RankineResult, SaturationProperties
from .state_table import markdown_state_table, text_state_table


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def rankine_text(result: RankineResult) -> str:
    parts = [
        "CICLO RANKINE IDEAL",
        "",
        "1) TABLA INICIAL - DATOS DEL PROBLEMA",
        text_state_table(result.initial_states),
        "",
        "2) DATOS OBTENIDOS DE TABLAS TERMODINÁMICAS",
        text_state_table(result.table_states),
        "",
        "3) ANÁLISIS ESTADO POR ESTADO",
    ]
    for i, explanation in enumerate(result.state_explanations, start=1):
        parts.append(explanation)
        events = result.events_by_state.get(i, [])
        for event in events:
            parts.extend(["", interpolation_text(event), ascii_diagram(event), ""])

    parts.extend(
        [
            "4) TABLA FINAL DE ESTADOS",
            text_state_table(result.final_states),
            "",
            "5) RESULTADOS DEL CICLO",
            f"Wt   = {_fmt(result.turbine_work_kJkg)} kJ/kg",
            f"Wb   = {_fmt(result.pump_work_kJkg)} kJ/kg",
            f"Qin  = {_fmt(result.heat_in_kJkg)} kJ/kg",
            f"Qout = {_fmt(result.heat_out_kJkg)} kJ/kg",
            f"Wnet = {_fmt(result.net_work_kJkg)} kJ/kg",
            f"eta  = {_fmt(result.thermal_efficiency * 100)} %",
        ]
    )
    return "\n".join(parts)


def write_rankine_report(result: RankineResult, output_dir: str | Path) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    figures = output / "figures"
    figures.mkdir(exist_ok=True)

    md = [
        "# Resolución — ciclo Rankine ideal",
        "",
        "## 1. Tabla inicial: datos del problema",
        "",
        markdown_state_table(result.initial_states),
        "",
        "## 2. Datos obtenidos de tablas termodinámicas",
        "",
        markdown_state_table(result.table_states),
        "",
        "## 3. Análisis estado por estado",
        "",
    ]

    figure_counter = 0
    for state_number, explanation in enumerate(result.state_explanations, start=1):
        md.extend([f"### Estado {state_number}", "", explanation, ""])
        for event in result.events_by_state.get(state_number, []):
            figure_counter += 1
            figure_name = f"interpolacion_{figure_counter:02d}.svg"
            render_svg(event, figures / figure_name)
            md.extend(
                [
                    f"**{event.method.capitalize()} — {event.property_name}**",
                    "",
                    "```text",
                    interpolation_text(event),
                    "```",
                    "",
                    f"![Interpolación representativa](figures/{figure_name})",
                    "",
                ]
            )

    md.extend(
        [
            "## 4. Tabla final de estados",
            "",
            markdown_state_table(result.final_states),
            "",
            "## 5. Resultados del ciclo",
            "",
            f"- Trabajo de turbina: **{_fmt(result.turbine_work_kJkg)} kJ/kg**",
            f"- Trabajo de bomba: **{_fmt(result.pump_work_kJkg)} kJ/kg**",
            f"- Calor de entrada: **{_fmt(result.heat_in_kJkg)} kJ/kg**",
            f"- Calor rechazado: **{_fmt(result.heat_out_kJkg)} kJ/kg**",
            f"- Trabajo neto: **{_fmt(result.net_work_kJkg)} kJ/kg**",
            f"- Rendimiento térmico: **{_fmt(result.thermal_efficiency * 100)} %**",
            "",
            "> Los diagramas de interpolación son representativos y no necesariamente están a escala.",
        ]
    )

    report_path = output / "solution.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    (output / "solution.json").write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "solution.txt").write_text(rankine_text(result), encoding="utf-8")
    return report_path


def write_lookup_report(
    *,
    title: str,
    summary_lines: list[str],
    events: list[InterpolationEvent],
    output_dir: str | Path,
    payload: dict,
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    figures = output / "figures"
    figures.mkdir(exist_ok=True)

    md = [f"# {title}", "", *summary_lines, ""]
    for index, event in enumerate(events, start=1):
        name = f"interpolacion_{index:02d}.svg"
        render_svg(event, figures / name)
        md.extend(
            [
                f"## {event.method.capitalize()}: {event.property_name}",
                "",
                "```text",
                interpolation_text(event),
                "```",
                "",
                f"![Interpolación](figures/{name})",
                "",
            ]
        )

    path = output / "lookup.md"
    path.write_text("\n".join(md), encoding="utf-8")
    (output / "lookup.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path

from __future__ import annotations

from html import escape
from pathlib import Path

from .models import InterpolationEvent


class InterpolationError(ValueError):
    pass


def linear_interpolate(
    *,
    x: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    property_name: str,
    x_name: str,
    x_unit: str = "",
    y_unit: str = "",
    allow_extrapolation: bool = False,
    note: str = "",
) -> InterpolationEvent:
    if x1 == x2:
        raise InterpolationError("No se puede interpolar con x1 = x2.")

    lo, hi = sorted((x1, x2))
    is_extrapolation = not (lo <= x <= hi)
    if is_extrapolation and not allow_extrapolation:
        raise InterpolationError(
            f"{x_name}={x} queda fuera del intervalo [{lo}, {hi}]."
        )

    result = y1 + ((x - x1) / (x2 - x1)) * (y2 - y1)
    method = "extrapolación lineal" if is_extrapolation else "interpolación lineal"
    return InterpolationEvent(
        property_name=property_name,
        x_name=x_name,
        x=float(x),
        x1=float(x1),
        y1=float(y1),
        x2=float(x2),
        y2=float(y2),
        result=float(result),
        x_unit=x_unit,
        y_unit=y_unit,
        method=method,
        note=note,
    )


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def interpolation_text(event: InterpolationEvent) -> str:
    xu = f" {event.x_unit}" if event.x_unit else ""
    yu = f" {event.y_unit}" if event.y_unit else ""
    return (
        f"{event.method.capitalize()} de {event.property_name}: "
        f"{event.x_name}={_fmt(event.x)}{xu} entre "
        f"{_fmt(event.x1)}{xu} y {_fmt(event.x2)}{xu}.\n"
        f"{event.property_name} = {_fmt(event.y1)} + "
        f"(({_fmt(event.x)} - {_fmt(event.x1)}) / "
        f"({_fmt(event.x2)} - {_fmt(event.x1)})) "
        f"({_fmt(event.y2)} - {_fmt(event.y1)})\n"
        f"Resultado: {event.property_name} = {_fmt(event.result)}{yu}"
    )


def ascii_diagram(event: InterpolationEvent) -> str:
    """Esquema deliberadamente representativo, no a escala."""
    left = (event.x1, event.y1, "1")
    right = (event.x2, event.y2, "2")
    target = (event.x, event.result, "*")

    if min(event.x1, event.x2) <= event.x <= max(event.x1, event.x2):
        ordered = [left, target, right] if event.x1 <= event.x2 else [right, target, left]
    elif event.x < min(event.x1, event.x2):
        ordered = [target, left, right] if event.x1 <= event.x2 else [target, right, left]
    else:
        ordered = [left, right, target] if event.x1 <= event.x2 else [right, left, target]

    labels = []
    for xv, yv, tag in ordered:
        if tag == "*":
            labels.append(f"● {_fmt(xv)} → {event.property_name}={_fmt(yv)}")
        else:
            labels.append(f"● {_fmt(xv)} → {_fmt(yv)}")

    return "\n".join(
        [
            f"{event.property_name}",
            "↑",
            "│                              ●",
            "│                         ／",
            "│                    ●",
            "│               ／",
            "│          ●",
            "└────────────────────────────────→ " + event.x_name,
            "   " + "        ".join(_fmt(item[0]) for item in ordered),
            "",
            "Esquema representativo (no necesariamente a escala):",
            "   " + " | ".join(labels),
        ]
    )


def render_svg(event: InterpolationEvent, path: Path, *, title: str | None = None) -> Path:
    """Genera un SVG simple y representativo, sin dependencias externas."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Posiciones representativas. El objetivo didáctico es mostrar el orden,
    # no reproducir una escala de ingeniería.
    if min(event.x1, event.x2) <= event.x <= max(event.x1, event.x2):
        x_positions = {"a": 110.0, "t": 330.0, "b": 550.0}
    elif event.x < min(event.x1, event.x2):
        x_positions = {"t": 90.0, "a": 320.0, "b": 550.0}
    else:
        x_positions = {"a": 90.0, "b": 320.0, "t": 550.0}

    # Una recta ascendente o descendente según los valores extremos.
    if event.y2 >= event.y1:
        y_a, y_b = 300.0, 100.0
    else:
        y_a, y_b = 100.0, 300.0

    # El punto objetivo cae sobre la recta representativa entre/extensión.
    xa, xb, xt = x_positions["a"], x_positions["b"], x_positions["t"]
    if xb == xa:
        yt = (y_a + y_b) / 2
    else:
        yt = y_a + ((xt - xa) / (xb - xa)) * (y_b - y_a)
    yt = max(60.0, min(330.0, yt))

    chart_title = title or f"{event.method.capitalize()}: {event.property_name}"
    xu = f" {event.x_unit}" if event.x_unit else ""
    yu = f" {event.y_unit}" if event.y_unit else ""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="680" height="410" viewBox="0 0 680 410">
  <rect width="680" height="410" fill="white"/>
  <text x="340" y="28" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700">{escape(chart_title)}</text>
  <text x="340" y="49" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">Esquema representativo · no necesariamente a escala</text>
  <line x1="70" y1="335" x2="610" y2="335" stroke="#222" stroke-width="2"/>
  <line x1="70" y1="335" x2="70" y2="65" stroke="#222" stroke-width="2"/>
  <polygon points="610,335 598,329 598,341" fill="#222"/>
  <polygon points="70,65 64,77 76,77" fill="#222"/>
  <text x="625" y="340" font-family="Arial, sans-serif" font-size="14">{escape(event.x_name)}</text>
  <text x="50" y="58" font-family="Arial, sans-serif" font-size="14">{escape(event.property_name)}</text>
  <line x1="{xa}" y1="{y_a}" x2="{xb}" y2="{y_b}" stroke="#3b3b3b" stroke-width="3"/>
  <line x1="{min(xa, xb, xt)}" y1="{max(y_a, y_b, yt)}" x2="{max(xa, xb, xt)}" y2="{min(y_a, y_b, yt)}" stroke="#3b3b3b" stroke-width="3" opacity="0.35"/>
  <circle cx="{xa}" cy="{y_a}" r="7" fill="#111"/>
  <circle cx="{xb}" cy="{y_b}" r="7" fill="#111"/>
  <circle cx="{xt}" cy="{yt}" r="8" fill="#111"/>
  <line x1="{xt}" y1="{yt}" x2="{xt}" y2="335" stroke="#777" stroke-dasharray="5 5"/>
  <text x="{xa}" y="360" text-anchor="middle" font-family="Arial, sans-serif" font-size="13">{_fmt(event.x1)}{escape(xu)}</text>
  <text x="{xb}" y="360" text-anchor="middle" font-family="Arial, sans-serif" font-size="13">{_fmt(event.x2)}{escape(xu)}</text>
  <text x="{xt}" y="385" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700">{_fmt(event.x)}{escape(xu)}</text>
  <text x="{xa + 12}" y="{y_a - 12}" font-family="Arial, sans-serif" font-size="12">{escape(event.property_name)}₁={_fmt(event.y1)}{escape(yu)}</text>
  <text x="{xb + 12}" y="{y_b - 12}" font-family="Arial, sans-serif" font-size="12">{escape(event.property_name)}₂={_fmt(event.y2)}{escape(yu)}</text>
  <text x="{xt + 12}" y="{yt + 22}" font-family="Arial, sans-serif" font-size="13" font-weight="700">{escape(event.property_name)}={_fmt(event.result)}{escape(yu)}</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")
    return path

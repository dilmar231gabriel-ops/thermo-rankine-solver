from __future__ import annotations

from copy import deepcopy

from .database import ThermoDatabase
from .models import RankineResult, StatePoint


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _phase_es(phase: str) -> str:
    return {
        "compressed_liquid": "líquido comprimido",
        "superheated_vapor": "vapor sobrecalentado",
        "two_phase_mixture": "mezcla saturada",
        "supercritical_or_single_phase": "fluido monofásico/supercrítico",
        "saturation_boundary": "frontera de saturación",
    }.get(phase, phase)


def solve_rankine_ideal(
    *,
    boiler_pressure_bar: float,
    condenser_pressure_bar: float,
    turbine_inlet_temperature_C: float,
    database: ThermoDatabase | None = None,
) -> RankineResult:
    """Resuelve un ciclo Rankine ideal simple de cuatro estados.

    Convención:
    1 = salida del condensador / entrada de bomba
    2 = salida de bomba / entrada de caldera
    3 = salida de caldera / entrada de turbina
    4 = salida de turbina / entrada de condensador
    """
    db = database or ThermoDatabase()
    p_high = float(boiler_pressure_bar)
    p_low = float(condenser_pressure_bar)
    t3 = float(turbine_inlet_temperature_C)

    if p_high <= p_low:
        raise ValueError("La presión de caldera debe ser mayor que la del condensador.")

    initial = [
        StatePoint(1, P_bar=p_low, note="Dato del problema"),
        StatePoint(2, P_bar=p_high, note="Presión de caldera"),
        StatePoint(3, P_bar=p_high, T_C=t3, note="Datos del problema"),
        StatePoint(4, P_bar=p_low, note="Presión del condensador"),
    ]

    states = deepcopy(initial)
    events_by_state: dict[int, list] = {1: [], 2: [], 3: [], 4: []}

    # Estado 1: líquido saturado a la salida del condensador.
    sat1 = db.saturation_by_pressure(p_low)
    if sat1.v_f is None:
        raise RuntimeError("No se pudo obtener v_f a partir de la densidad de líquido saturado.")
    states[0].T_C = sat1.T_C
    states[0].x = 0.0
    states[0].h_kJkg = sat1.h_f
    states[0].s_kJkgK = sat1.s_f
    states[0].v_m3kg = sat1.v_f
    states[0].phase = "líquido saturado"
    events_by_state[1].extend(sat1.events)

    # Estado 3: consulta P-T en la tabla de líquido comprimido/vapor sobrecalentado.
    pt3 = db.pt(p_high, t3)
    states[2].h_kJkg = pt3.h_kJkg
    states[2].s_kJkgK = pt3.s_kJkgK
    states[2].phase = _phase_es(pt3.phase)
    events_by_state[3].extend(pt3.events)

    # Foto intermedia: lo que se obtuvo directamente de tablas antes de balances.
    table_states = deepcopy(states)

    # Estado 2: bomba ideal; aproximación de líquido incompresible.
    h1 = states[0].h_kJkg
    v1 = states[0].v_m3kg
    assert h1 is not None and v1 is not None
    delta_p_kpa = (p_high - p_low) * 100.0  # 1 bar = 100 kPa
    wb = v1 * delta_p_kpa
    h2 = h1 + wb
    states[1].h_kJkg = h2
    states[1].s_kJkgK = states[0].s_kJkgK
    states[1].phase = "líquido comprimido"

    # Estado 4: turbina ideal, s4 = s3.
    s3 = states[2].s_kJkgK
    assert s3 is not None
    ps4 = db.ps(p_low, s3)
    states[3].T_C = ps4.T_C
    states[3].x = ps4.x
    states[3].h_kJkg = ps4.h_kJkg
    states[3].s_kJkgK = s3
    states[3].phase = _phase_es(ps4.phase)
    events_by_state[4].extend(ps4.events)

    h3 = states[2].h_kJkg
    h4 = states[3].h_kJkg
    assert h3 is not None and h4 is not None

    wt = h3 - h4
    qin = h3 - h2
    qout = h4 - h1
    wnet = wt - wb
    if qin <= 0:
        raise RuntimeError("El calor de entrada calculado no es positivo; revise los datos del ciclo.")
    eta = wnet / qin

    explanations = [
        (
            f"Estado 1: a P1={_fmt(p_low)} bar se toma líquido saturado de la tabla: "
            f"h1={_fmt(h1)} kJ/kg, s1={_fmt(states[0].s_kJkgK or 0)} kJ/(kg·K)."
        ),
        (
            f"Estado 2: bomba ideal. Se usa h2=h1+v1(P2-P1), obteniendo "
            f"h2={_fmt(h2)} kJ/kg."
        ),
        (
            f"Estado 3: con P3={_fmt(p_high)} bar y T3={_fmt(t3)} °C se consulta la tabla P-T; "
            f"h3={_fmt(h3)} kJ/kg y s3={_fmt(s3)} kJ/(kg·K)."
        ),
        (
            f"Estado 4: turbina ideal, por tanto s4=s3. A P4={_fmt(p_low)} bar se obtiene "
            + (f"x4={_fmt(ps4.x)} y " if ps4.x is not None else "")
            + f"h4={_fmt(h4)} kJ/kg."
        ),
    ]

    return RankineResult(
        inputs={
            "boiler_pressure_bar": p_high,
            "condenser_pressure_bar": p_low,
            "turbine_inlet_temperature_C": t3,
        },
        initial_states=initial,
        table_states=table_states,
        final_states=states,
        state_explanations=explanations,
        events_by_state=events_by_state,
        turbine_work_kJkg=wt,
        pump_work_kJkg=wb,
        heat_in_kJkg=qin,
        heat_out_kJkg=qout,
        net_work_kJkg=wnet,
        thermal_efficiency=eta,
    )

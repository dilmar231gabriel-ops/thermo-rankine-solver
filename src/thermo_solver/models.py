from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class InterpolationEvent:
    property_name: str
    x_name: str
    x: float
    x1: float
    y1: float
    x2: float
    y2: float
    result: float
    x_unit: str = ""
    y_unit: str = ""
    method: str = "interpolación lineal"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SaturationProperties:
    P_bar: float
    T_C: float
    h_f: float
    h_fg: float
    h_g: float
    s_f: float
    s_fg: float
    s_g: float
    rho_l: float | None = None
    rho_g: float | None = None
    method: str = "exact"
    source: str = "saturated_water"
    events: list[InterpolationEvent] = field(default_factory=list)

    @property
    def v_f(self) -> float | None:
        if self.rho_l is None or self.rho_l == 0:
            return None
        return 1.0 / self.rho_l

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["v_f"] = self.v_f
        return data


@dataclass
class PTProperties:
    P_bar: float
    T_C: float
    h_kJkg: float
    s_kJkgK: float
    phase: str
    method: str
    source: str = "superheated_compressed"
    events: list[InterpolationEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PSProperties:
    P_bar: float
    s_kJkgK: float
    h_kJkg: float
    T_C: float | None
    phase: str
    x: float | None = None
    method: str = "derived"
    source: str = "thermodynamic_tables.sqlite"
    events: list[InterpolationEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StatePoint:
    number: int
    P_bar: float | None = None
    T_C: float | None = None
    x: float | None = None
    h_kJkg: float | None = None
    s_kJkgK: float | None = None
    v_m3kg: float | None = None
    phase: str | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankineResult:
    inputs: dict[str, float]
    initial_states: list[StatePoint]
    table_states: list[StatePoint]
    final_states: list[StatePoint]
    state_explanations: list[str]
    events_by_state: dict[int, list[InterpolationEvent]]
    turbine_work_kJkg: float
    pump_work_kJkg: float
    heat_in_kJkg: float
    heat_out_kJkg: float
    net_work_kJkg: float
    thermal_efficiency: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "inputs": self.inputs,
            "initial_states": [s.to_dict() for s in self.initial_states],
            "table_states": [s.to_dict() for s in self.table_states],
            "final_states": [s.to_dict() for s in self.final_states],
            "state_explanations": self.state_explanations,
            "events_by_state": {
                str(k): [event.to_dict() for event in v]
                for k, v in self.events_by_state.items()
            },
            "cycle": {
                "turbine_work_kJkg": self.turbine_work_kJkg,
                "pump_work_kJkg": self.pump_work_kJkg,
                "heat_in_kJkg": self.heat_in_kJkg,
                "heat_out_kJkg": self.heat_out_kJkg,
                "net_work_kJkg": self.net_work_kJkg,
                "thermal_efficiency": self.thermal_efficiency,
                "thermal_efficiency_percent": self.thermal_efficiency * 100.0,
            },
        }

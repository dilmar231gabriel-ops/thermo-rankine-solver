from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from thermo_solver.database import ThermoDatabase
from thermo_solver.rankine import solve_rankine_ideal


class RankineTests(unittest.TestCase):
    def test_rankine_ideal_smoke(self) -> None:
        db = ThermoDatabase(ROOT / "data" / "thermodynamic_tables.sqlite")
        result = solve_rankine_ideal(
            boiler_pressure_bar=80.0,
            condenser_pressure_bar=0.1,
            turbine_inlet_temperature_C=480.0,
            database=db,
        )
        self.assertEqual(len(result.final_states), 4)
        self.assertGreater(result.turbine_work_kJkg, 0)
        self.assertGreater(result.heat_in_kJkg, 0)
        self.assertGreater(result.thermal_efficiency, 0)
        self.assertLess(result.thermal_efficiency, 1)


if __name__ == "__main__":
    unittest.main()

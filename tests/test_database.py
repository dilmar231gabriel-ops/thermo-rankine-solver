from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from thermo_solver.database import ThermoDatabase


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = ThermoDatabase(ROOT / "data" / "thermodynamic_tables.sqlite")

    def test_exact_saturation(self) -> None:
        sat = self.db.saturation_by_pressure(0.1)
        self.assertAlmostEqual(sat.T_C, 45.817, places=3)
        self.assertGreater(sat.h_g, sat.h_f)
        self.assertIsNotNone(sat.v_f)

    def test_temperature_interpolation(self) -> None:
        pt = self.db.pt(7.0, 202.5)
        self.assertEqual(pt.method, "temperature_interpolation")
        self.assertAlmostEqual(pt.h_kJkg, (2844.3 + 2855.4) / 2, places=6)
        self.assertEqual(len(pt.events), 2)

    def test_pressure_temperature_bilinear(self) -> None:
        pt = self.db.pt(7.25, 202.5)
        self.assertEqual(pt.method, "bilinear_interpolation")
        self.assertGreater(len(pt.events), 2)
        self.assertGreater(pt.h_kJkg, 2800)


if __name__ == "__main__":
    unittest.main()

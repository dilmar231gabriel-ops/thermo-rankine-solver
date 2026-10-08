from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from thermo_solver.interpolation import InterpolationError, linear_interpolate


class InterpolationTests(unittest.TestCase):
    def test_linear_interpolation(self) -> None:
        event = linear_interpolate(
            x=7.4,
            x1=7.0,
            y1=2763.0,
            x2=8.0,
            y2=2778.0,
            property_name="h",
            x_name="P",
        )
        self.assertAlmostEqual(event.result, 2769.0, places=9)
        self.assertEqual(event.method, "interpolación lineal")

    def test_extrapolation_blocked(self) -> None:
        with self.assertRaises(InterpolationError):
            linear_interpolate(
                x=9.0,
                x1=7.0,
                y1=1.0,
                x2=8.0,
                y2=2.0,
                property_name="y",
                x_name="x",
            )


if __name__ == "__main__":
    unittest.main()

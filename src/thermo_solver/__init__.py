"""Motor determinista para consultar tablas termodinámicas y resolver ciclos Rankine."""

from .database import ThermoDatabase
from .rankine import solve_rankine_ideal

__all__ = ["ThermoDatabase", "solve_rankine_ideal"]
__version__ = "0.1.0"

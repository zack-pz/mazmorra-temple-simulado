from __future__ import annotations

from dataclasses import dataclass

from mazmorra.evaluacion import EstadoMazmorra


@dataclass
class ConfiguracionGenerador:
    semilla: int = 42
    iteraciones: int = 600
    temperatura_inicial: float = 18.0
    temperatura_final: float = 0.15


@dataclass
class ResultadoGeneracion:
    estado: EstadoMazmorra
    evaluacion: dict
    semilla: int
    iteraciones: int
    energia_inicial: float
    energia_final: float

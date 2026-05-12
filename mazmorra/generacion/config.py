from __future__ import annotations

from dataclasses import dataclass, field

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
    evaluacion_inicial: dict = field(default_factory=dict)
    estadisticas_recocido: dict = field(default_factory=dict)

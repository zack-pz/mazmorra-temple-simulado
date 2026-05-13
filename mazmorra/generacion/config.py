from __future__ import annotations

from dataclasses import dataclass, field

from mazmorra.evaluacion import EstadoMazmorra


@dataclass
class ConfiguracionGenerador:
    semilla: int = 10
    iteraciones: int = 600
    temperatura_inicial: float = 8.0
    temperatura_final: float = 0.06


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

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


TILE_PARED = 0
TILE_PISO = 1
TILE_INICIO = 2
TILE_SALIDA = 3
TILE_TESORO = 4
TILE_BOSS = 5

TILES_CAMINABLES = {TILE_PISO, TILE_INICIO, TILE_SALIDA, TILE_TESORO, TILE_BOSS}
TIPOS_SALA_COMBATE = {"combate", "tesoro", "boss"}


@dataclass(frozen=True)
class EstadoMazmorra:
    """Representación mínima para evaluar una mazmorra híbrida."""

    habitaciones: dict[str, dict]
    conexiones: list[tuple[str, str]]
    habitacion_inicio: str
    habitacion_salida: str
    habitacion_boss: str | None = None
    habitaciones_tesoro: list[str] = field(default_factory=list)
    cantidad_enemigos: int = 0
    grid: np.ndarray | None = None
    semilla: int | None = None


@dataclass(frozen=True)
class PesosObjetivo:
    conectividad_dura: float = 1200.0
    secuencia_boss_salida_dura: float = 1000.0
    grados_habitaciones_dura: float = 950.0
    cantidad_habitaciones_dura: float = 500.0
    cantidad_tesoros_dura: float = 700.0
    cantidad_descanso_dura: float = 450.0
    tesoros_bloqueados_dura: float = 900.0
    salida_lejos_suave: float = 70.0
    interes_tesoros_suave: float = 45.0
    progresion_dificultad_suave: float = 80.0
    salas_vacias_suave: float = 55.0
    proporcion_piso_suave: float = 30.0
    dispersion_cuadricula_suave: float = 60.0
    ocupacion_cuadricula_suave: float = 50.0
    ramificacion_util_suave: float = 75.0
    lineas_excesivas_suave: float = 65.0

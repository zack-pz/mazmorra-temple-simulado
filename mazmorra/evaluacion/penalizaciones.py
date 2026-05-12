from __future__ import annotations

from math import inf
from typing import Iterable

import numpy as np

from mazmorra.evaluacion.grafo import camino_mas_corto, distancias_bfs, tipo_habitacion
from mazmorra.evaluacion.modelo import TIPOS_SALA_COMBATE, TILES_CAMINABLES, EstadoMazmorra


def minimos_tesoro_por_tamano(cantidad_habitaciones: int) -> int:
    if cantidad_habitaciones <= 11:
        return 2
    if cantidad_habitaciones <= 15:
        return 3
    return 5


def contar_tiles_piso(grid: np.ndarray | None) -> int:
    if grid is None:
        return 0
    return int(np.isin(grid, list(TILES_CAMINABLES)).sum())


def proporcion_piso(grid: np.ndarray | None) -> float:
    if grid is None or grid.size == 0:
        return 0.0
    return contar_tiles_piso(grid) / float(grid.size)


def penalizacion_rango(valor: float, minimo: float, maximo: float) -> float:
    if valor < minimo:
        return (minimo - valor) / max(1.0, maximo - minimo)
    if valor > maximo:
        return (valor - maximo) / max(1.0, maximo - minimo)
    return 0.0


def penalizacion_faltante_normalizada(valor: float, objetivo: float) -> float:
    if objetivo <= 0:
        return 0.0
    return max(0.0, objetivo - valor) / objetivo


def habitaciones_tesoro_desde_estado(estado: EstadoMazmorra) -> list[str]:
    if estado.habitaciones_tesoro:
        return list(estado.habitaciones_tesoro)

    return [nombre for nombre, habitacion in estado.habitaciones.items() if tipo_habitacion(habitacion) == "tesoro"]


def obtener_boss(estado: EstadoMazmorra) -> str | None:
    if estado.habitacion_boss is not None:
        return estado.habitacion_boss

    for nombre, habitacion in estado.habitaciones.items():
        if tipo_habitacion(habitacion) == "boss":
            return nombre

    return None


def penalizacion_interes_tesoros(
    adyacencias: dict[str, set[str]],
    habitacion_inicio: str,
    habitacion_salida: str,
    habitaciones_tesoro: Iterable[str],
    distancia_salida_ideal: int,
) -> float:
    tesoros = list(habitaciones_tesoro)
    if not tesoros:
        return 1.0

    distancias_desde_inicio = distancias_bfs(adyacencias, habitacion_inicio)
    camino_principal = set(camino_mas_corto(adyacencias, habitacion_inicio, habitacion_salida))
    penalizaciones: list[float] = []

    for habitacion_tesoro in tesoros:
        distancia = distancias_desde_inicio.get(habitacion_tesoro)
        if distancia is None:
            penalizaciones.append(1.0)
            continue

        penalizacion_profundidad = 1.0 - min(distancia / max(1, distancia_salida_ideal), 1.0)
        penalizacion_camino_principal = 1.0 if habitacion_tesoro in camino_principal else 0.0
        penalizaciones.append(0.6 * penalizacion_profundidad + 0.4 * penalizacion_camino_principal)

    return sum(penalizaciones) / len(penalizaciones)


def penalizacion_progresion_dificultad(
    habitaciones: dict[str, dict],
    distancias_desde_inicio: dict[str, int],
) -> float:
    salas_ordenadas = [
        (distancias_desde_inicio[nombre], habitacion.get("enemigos", 0), tipo_habitacion(habitacion))
        for nombre, habitacion in habitaciones.items()
        if nombre in distancias_desde_inicio and tipo_habitacion(habitacion) in TIPOS_SALA_COMBATE
    ]
    salas_ordenadas.sort(key=lambda item: (item[0], item[1]))

    if len(salas_ordenadas) < 2:
        return 0.0

    maximo_enemigos = max(enemigos for _, enemigos, _ in salas_ordenadas) or 1
    penalizaciones: list[float] = []

    for indice in range(1, len(salas_ordenadas)):
        enemigos_previos = salas_ordenadas[indice - 1][1]
        enemigos_actuales = salas_ordenadas[indice][1]
        caida = max(0, enemigos_previos - enemigos_actuales)
        penalizaciones.append(caida / maximo_enemigos)

    if salas_ordenadas[-1][2] == "boss" and salas_ordenadas[-1][1] < maximo_enemigos:
        penalizaciones.append((maximo_enemigos - salas_ordenadas[-1][1]) / maximo_enemigos)

    return sum(penalizaciones) / max(1, len(penalizaciones))


def penalizacion_salas_vacias(habitaciones: dict[str, dict]) -> float:
    candidatas = [habitacion for habitacion in habitaciones.values() if tipo_habitacion(habitacion) in {"combate", "tesoro"}]
    if not candidatas:
        return 0.0

    vacias = [habitacion for habitacion in candidatas if habitacion.get("enemigos", 0) <= 0 and habitacion.get("cofres", 0) <= 0]
    return len(vacias) / len(candidatas)

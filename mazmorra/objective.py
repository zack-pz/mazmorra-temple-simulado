from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import inf
from typing import Iterable

import numpy as np


TILE_PARED = 0
TILE_PISO = 1
TILE_INICIO = 2
TILE_SALIDA = 3
TILE_TESORO = 4
TILE_BOSS = 5

TILES_CAMINABLES = {TILE_PISO, TILE_INICIO, TILE_SALIDA, TILE_TESORO, TILE_BOSS}


@dataclass(frozen=True)
class EstadoMazmorra:
    """Representación mínima para evaluar una mazmorra híbrida."""

    habitaciones: dict[str, dict]
    conexiones: list[tuple[str, str]]
    habitacion_inicio: str
    habitacion_salida: str
    habitaciones_tesoro: list[str] = field(default_factory=list)
    cantidad_enemigos: int = 0
    grid: np.ndarray | None = None


@dataclass(frozen=True)
class PesosObjetivo:
    """Pesos por defecto para versión 1."""

    conectividad_dura: float = 1000.0
    distancia_salida_dura: float = 500.0
    cantidad_habitaciones_dura: float = 300.0
    tesoros_bloqueados_dura: float = 800.0
    cantidad_tesoros_suave: float = 30.0
    cantidad_enemigos_suave: float = 30.0
    proporcion_piso_suave: float = 25.0
    salida_lejos_suave: float = 40.0
    interes_tesoros_suave: float = 35.0


def construir_adyacencias(conexiones: Iterable[tuple[str, str]]) -> dict[str, set[str]]:
    adyacencias: dict[str, set[str]] = {}
    for origen, destino in conexiones:
        adyacencias.setdefault(origen, set()).add(destino)
        adyacencias.setdefault(destino, set()).add(origen)
    return adyacencias


def distancias_bfs(adyacencias: dict[str, set[str]], inicio: str) -> dict[str, int]:
    if inicio not in adyacencias:
        return {inicio: 0}

    distancias = {inicio: 0}
    cola = deque([inicio])

    while cola:
        actual = cola.popleft()
        for vecino in adyacencias[actual]:
            if vecino in distancias:
                continue
            distancias[vecino] = distancias[actual] + 1
            cola.append(vecino)

    return distancias


def camino_mas_corto(adyacencias: dict[str, set[str]], inicio: str, meta: str) -> list[str]:
    if inicio == meta:
        return [inicio]
    if inicio not in adyacencias or meta not in adyacencias:
        return []

    padres: dict[str, str | None] = {inicio: None}
    cola = deque([inicio])

    while cola:
        actual = cola.popleft()
        for vecino in adyacencias[actual]:
            if vecino in padres:
                continue
            padres[vecino] = actual
            if vecino == meta:
                camino = [meta]
                cursor = meta
                while padres[cursor] is not None:
                    cursor = padres[cursor]
                    camino.append(cursor)
                camino.reverse()
                return camino
            cola.append(vecino)

    return []


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


def evaluar_mazmorra(
    estado: EstadoMazmorra,
    pesos: PesosObjetivo | None = None,
    distancia_salida_minima: int = 4,
    distancia_salida_ideal: int = 7,
) -> dict:
    """
    Evalúa la versión 1 de la función objetivo.

    Reglas duras:
    1. Debe existir camino entre inicio y salida.
    2. La distancia topológica entre inicio y salida debe ser al menos 4 habitaciones.
    3. La cantidad total de habitaciones debe estar entre 5 y 20.
    4. Todo tesoro debe ser alcanzable desde el inicio.

    Objetivos suaves:
    1. Mantener entre 3 y 7 tesoros.
    2. Mantener entre 5 y 20 enemigos.
    3. Mantener el porcentaje de piso entre 35% y 50%.
    4. Favorecer que la salida esté más lejos que el mínimo requerido.
    5. Favorecer tesoros profundos y fuera de la ruta principal.
    """

    pesos = pesos or PesosObjetivo()
    adyacencias = construir_adyacencias(estado.conexiones)

    for nombre_habitacion in estado.habitaciones:
        adyacencias.setdefault(nombre_habitacion, set())

    distancias_desde_inicio = distancias_bfs(adyacencias, estado.habitacion_inicio)
    distancia_salida = distancias_desde_inicio.get(estado.habitacion_salida, inf)
    cantidad_habitaciones = len(estado.habitaciones)
    cantidad_tesoros = len(estado.habitaciones_tesoro)
    tesoros_bloqueados = sum(1 for habitacion in estado.habitaciones_tesoro if habitacion not in distancias_desde_inicio)
    proporcion_actual_piso = proporcion_piso(estado.grid)

    penalizacion_dura_conectividad = 0.0 if distancia_salida != inf else 1.0
    penalizacion_dura_distancia_salida = 1.0 if distancia_salida == inf else penalizacion_faltante_normalizada(distancia_salida, distancia_salida_minima)
    penalizacion_dura_cantidad_habitaciones = penalizacion_rango(cantidad_habitaciones, 5, 20)
    penalizacion_dura_tesoros_bloqueados = tesoros_bloqueados / max(1, cantidad_tesoros)

    penalizacion_suave_cantidad_tesoros = penalizacion_rango(cantidad_tesoros, 3, 7)
    penalizacion_suave_cantidad_enemigos = penalizacion_rango(estado.cantidad_enemigos, 5, 20)
    penalizacion_suave_proporcion_piso = penalizacion_rango(proporcion_actual_piso, 0.35, 0.50)
    penalizacion_suave_salida_lejos = 1.0 if distancia_salida == inf else penalizacion_faltante_normalizada(distancia_salida, distancia_salida_ideal)
    penalizacion_suave_interes_tesoros = penalizacion_interes_tesoros(
        adyacencias=adyacencias,
        habitacion_inicio=estado.habitacion_inicio,
        habitacion_salida=estado.habitacion_salida,
        habitaciones_tesoro=estado.habitaciones_tesoro,
        distancia_salida_ideal=distancia_salida_ideal,
    )

    penalizaciones = {
        "conectividad_dura": penalizacion_dura_conectividad,
        "distancia_salida_dura": penalizacion_dura_distancia_salida,
        "cantidad_habitaciones_dura": penalizacion_dura_cantidad_habitaciones,
        "tesoros_bloqueados_dura": penalizacion_dura_tesoros_bloqueados,
        "cantidad_tesoros_suave": penalizacion_suave_cantidad_tesoros,
        "cantidad_enemigos_suave": penalizacion_suave_cantidad_enemigos,
        "proporcion_piso_suave": penalizacion_suave_proporcion_piso,
        "salida_lejos_suave": penalizacion_suave_salida_lejos,
        "interes_tesoros_suave": penalizacion_suave_interes_tesoros,
    }

    terminos_ponderados = {
        "conectividad_dura": penalizaciones["conectividad_dura"] * pesos.conectividad_dura,
        "distancia_salida_dura": penalizaciones["distancia_salida_dura"] * pesos.distancia_salida_dura,
        "cantidad_habitaciones_dura": penalizaciones["cantidad_habitaciones_dura"] * pesos.cantidad_habitaciones_dura,
        "tesoros_bloqueados_dura": penalizaciones["tesoros_bloqueados_dura"] * pesos.tesoros_bloqueados_dura,
        "cantidad_tesoros_suave": penalizaciones["cantidad_tesoros_suave"] * pesos.cantidad_tesoros_suave,
        "cantidad_enemigos_suave": penalizaciones["cantidad_enemigos_suave"] * pesos.cantidad_enemigos_suave,
        "proporcion_piso_suave": penalizaciones["proporcion_piso_suave"] * pesos.proporcion_piso_suave,
        "salida_lejos_suave": penalizaciones["salida_lejos_suave"] * pesos.salida_lejos_suave,
        "interes_tesoros_suave": penalizaciones["interes_tesoros_suave"] * pesos.interes_tesoros_suave,
    }

    return {
        "energia": sum(terminos_ponderados.values()),
        "factible": all(
            penalizaciones[clave] == 0.0
            for clave in (
                "conectividad_dura",
                "distancia_salida_dura",
                "cantidad_habitaciones_dura",
                "tesoros_bloqueados_dura",
            )
        ),
        "metricas": {
            "cantidad_habitaciones": cantidad_habitaciones,
            "cantidad_tesoros": cantidad_tesoros,
            "cantidad_enemigos": estado.cantidad_enemigos,
            "distancia_salida": None if distancia_salida == inf else distancia_salida,
            "tesoros_bloqueados": tesoros_bloqueados,
            "proporcion_piso": proporcion_actual_piso,
        },
        "penalizaciones": penalizaciones,
        "terminos_ponderados": terminos_ponderados,
    }

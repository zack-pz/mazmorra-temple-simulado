from __future__ import annotations

from collections import Counter, deque
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
    cantidad_habitaciones_dura: float = 500.0
    cantidad_tesoros_dura: float = 700.0
    cantidad_descanso_dura: float = 450.0
    tesoros_bloqueados_dura: float = 900.0
    salida_lejos_suave: float = 70.0
    interes_tesoros_suave: float = 45.0
    progresion_dificultad_suave: float = 80.0
    salas_vacias_suave: float = 55.0
    proporcion_piso_suave: float = 30.0


def minimos_tesoro_por_tamano(cantidad_habitaciones: int) -> int:
    if cantidad_habitaciones <= 11:
        return 2
    if cantidad_habitaciones <= 15:
        return 3
    return 5


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


def tipo_habitacion(habitacion: dict) -> str:
    return habitacion.get("tipo", "combate")


def contar_tipos(habitaciones: dict[str, dict]) -> Counter:
    return Counter(tipo_habitacion(habitacion) for habitacion in habitaciones.values())


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
    candidatas = [
        habitacion
        for habitacion in habitaciones.values()
        if tipo_habitacion(habitacion) in {"combate", "tesoro"}
    ]
    if not candidatas:
        return 0.0

    vacias = [
        habitacion
        for habitacion in candidatas
        if habitacion.get("enemigos", 0) <= 0 and habitacion.get("cofres", 0) <= 0
    ]
    return len(vacias) / len(candidatas)


def evaluar_mazmorra(
    estado: EstadoMazmorra,
    pesos: PesosObjetivo | None = None,
    distancia_salida_ideal: int = 9,
) -> dict:
    pesos = pesos or PesosObjetivo()
    adyacencias = construir_adyacencias(estado.conexiones)

    for nombre_habitacion in estado.habitaciones:
        adyacencias.setdefault(nombre_habitacion, set())

    distancias_desde_inicio = distancias_bfs(adyacencias, estado.habitacion_inicio)
    distancia_salida = distancias_desde_inicio.get(estado.habitacion_salida, inf)
    cantidad_habitaciones = len(estado.habitaciones)
    habitaciones_tesoro = habitaciones_tesoro_desde_estado(estado)
    cantidad_tesoros = len(habitaciones_tesoro)
    tesoros_bloqueados = sum(1 for habitacion in habitaciones_tesoro if habitacion not in distancias_desde_inicio)
    proporcion_actual_piso = proporcion_piso(estado.grid)
    boss = obtener_boss(estado)
    distancias_desde_boss = distancias_bfs(adyacencias, boss) if boss is not None else {}
    distancia_boss = distancias_desde_inicio.get(boss, inf) if boss is not None else inf
    distancia_boss_a_salida = distancias_desde_boss.get(estado.habitacion_salida, inf) if boss is not None else inf
    tipos = contar_tipos(estado.habitaciones)
    minimo_tesoros = minimos_tesoro_por_tamano(cantidad_habitaciones)
    penalizacion_min_tesoros = penalizacion_faltante_normalizada(cantidad_tesoros, minimo_tesoros)
    cantidad_descanso = tipos.get("descanso", 0)
    camino_principal = camino_mas_corto(adyacencias, estado.habitacion_inicio, estado.habitacion_salida)
    boss_en_camino = boss in camino_principal if boss is not None else False

    penalizacion_dura_conectividad = 0.0 if distancia_salida != inf else 1.0
    secuencia_valida = (
        boss is not None
        and distancia_boss != inf
        and distancia_boss_a_salida != inf
        and distancia_salida > distancia_boss
        and boss_en_camino
    )
    penalizacion_dura_secuencia_boss_salida = 0.0 if secuencia_valida else 1.0
    penalizacion_dura_cantidad_habitaciones = penalizacion_rango(cantidad_habitaciones, 8, 20)
    penalizacion_dura_cantidad_tesoros = penalizacion_min_tesoros
    penalizacion_dura_cantidad_descanso = max(0.0, cantidad_descanso - 2) / 2.0
    penalizacion_dura_tesoros_bloqueados = tesoros_bloqueados / max(1, cantidad_tesoros)

    ideal_salida = min(distancia_salida_ideal, max(6, cantidad_habitaciones - 1))
    penalizacion_suave_salida_lejos = 1.0 if distancia_salida == inf else penalizacion_faltante_normalizada(distancia_salida, ideal_salida)
    penalizacion_suave_interes_tesoros = penalizacion_interes_tesoros(
        adyacencias=adyacencias,
        habitacion_inicio=estado.habitacion_inicio,
        habitacion_salida=estado.habitacion_salida,
        habitaciones_tesoro=habitaciones_tesoro,
        distancia_salida_ideal=ideal_salida,
    )
    penalizacion_suave_progresion_dificultad = penalizacion_progresion_dificultad(estado.habitaciones, distancias_desde_inicio)
    penalizacion_suave_salas_vacias = penalizacion_salas_vacias(estado.habitaciones)
    penalizacion_suave_proporcion_piso = penalizacion_rango(proporcion_actual_piso, 0.22, 0.50)

    penalizaciones = {
        "conectividad_dura": penalizacion_dura_conectividad,
        "secuencia_boss_salida_dura": penalizacion_dura_secuencia_boss_salida,
        "cantidad_habitaciones_dura": penalizacion_dura_cantidad_habitaciones,
        "cantidad_tesoros_dura": penalizacion_dura_cantidad_tesoros,
        "cantidad_descanso_dura": penalizacion_dura_cantidad_descanso,
        "tesoros_bloqueados_dura": penalizacion_dura_tesoros_bloqueados,
        "salida_lejos_suave": penalizacion_suave_salida_lejos,
        "interes_tesoros_suave": penalizacion_suave_interes_tesoros,
        "progresion_dificultad_suave": penalizacion_suave_progresion_dificultad,
        "salas_vacias_suave": penalizacion_suave_salas_vacias,
        "proporcion_piso_suave": penalizacion_suave_proporcion_piso,
    }

    terminos_ponderados = {
        "conectividad_dura": penalizaciones["conectividad_dura"] * pesos.conectividad_dura,
        "secuencia_boss_salida_dura": penalizaciones["secuencia_boss_salida_dura"] * pesos.secuencia_boss_salida_dura,
        "cantidad_habitaciones_dura": penalizaciones["cantidad_habitaciones_dura"] * pesos.cantidad_habitaciones_dura,
        "cantidad_tesoros_dura": penalizaciones["cantidad_tesoros_dura"] * pesos.cantidad_tesoros_dura,
        "cantidad_descanso_dura": penalizaciones["cantidad_descanso_dura"] * pesos.cantidad_descanso_dura,
        "tesoros_bloqueados_dura": penalizaciones["tesoros_bloqueados_dura"] * pesos.tesoros_bloqueados_dura,
        "salida_lejos_suave": penalizaciones["salida_lejos_suave"] * pesos.salida_lejos_suave,
        "interes_tesoros_suave": penalizaciones["interes_tesoros_suave"] * pesos.interes_tesoros_suave,
        "progresion_dificultad_suave": penalizaciones["progresion_dificultad_suave"] * pesos.progresion_dificultad_suave,
        "salas_vacias_suave": penalizaciones["salas_vacias_suave"] * pesos.salas_vacias_suave,
        "proporcion_piso_suave": penalizaciones["proporcion_piso_suave"] * pesos.proporcion_piso_suave,
    }

    return {
        "energia": sum(terminos_ponderados.values()),
        "factible": all(
            penalizaciones[clave] == 0.0
            for clave in (
                "conectividad_dura",
                "secuencia_boss_salida_dura",
                "cantidad_habitaciones_dura",
                "cantidad_tesoros_dura",
                "cantidad_descanso_dura",
                "tesoros_bloqueados_dura",
            )
        ),
        "metricas": {
            "cantidad_habitaciones": cantidad_habitaciones,
            "cantidad_tesoros": cantidad_tesoros,
            "tesoros_minimos_requeridos": minimo_tesoros,
            "cantidad_descanso": cantidad_descanso,
            "cantidad_enemigos": estado.cantidad_enemigos,
            "distancia_boss": None if distancia_boss == inf else distancia_boss,
            "distancia_salida": None if distancia_salida == inf else distancia_salida,
            "distancia_boss_a_salida": None if distancia_boss_a_salida == inf else distancia_boss_a_salida,
            "tesoros_bloqueados": tesoros_bloqueados,
            "proporcion_piso": proporcion_actual_piso,
            "boss_en_camino_principal": boss_en_camino,
            "tipos_sala": dict(tipos),
        },
        "penalizaciones": penalizaciones,
        "terminos_ponderados": terminos_ponderados,
    }

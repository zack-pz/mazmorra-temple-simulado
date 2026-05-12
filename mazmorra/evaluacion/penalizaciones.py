from __future__ import annotations

from math import ceil, inf
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


def resumen_cuadricula_logica(habitaciones: dict[str, dict]) -> dict[str, float]:
    celdas = [
        (habitacion.get("fila"), habitacion.get("columna"))
        for habitacion in habitaciones.values()
        if habitacion.get("fila") is not None and habitacion.get("columna") is not None
    ]
    if not celdas:
        return {
            "cantidad_habitaciones": 0,
            "filas_usadas": 0,
            "columnas_usadas": 0,
            "alto_caja": 0,
            "ancho_caja": 0,
            "area_caja": 0,
            "densidad_caja": 0.0,
            "aspecto_caja": 0.0,
        }

    filas = sorted({fila for fila, _ in celdas})
    columnas = sorted({columna for _, columna in celdas})
    min_fila = min(fila for fila, _ in celdas)
    max_fila = max(fila for fila, _ in celdas)
    min_columna = min(columna for _, columna in celdas)
    max_columna = max(columna for _, columna in celdas)
    alto_caja = max_fila - min_fila + 1
    ancho_caja = max_columna - min_columna + 1
    area_caja = alto_caja * ancho_caja
    densidad_caja = len(celdas) / area_caja if area_caja > 0 else 0.0
    lado_menor = max(1, min(alto_caja, ancho_caja))
    aspecto_caja = max(alto_caja, ancho_caja) / lado_menor

    return {
        "cantidad_habitaciones": len(celdas),
        "filas_usadas": len(filas),
        "columnas_usadas": len(columnas),
        "alto_caja": alto_caja,
        "ancho_caja": ancho_caja,
        "area_caja": area_caja,
        "densidad_caja": densidad_caja,
        "aspecto_caja": aspecto_caja,
    }


def penalizacion_dispersion_cuadricula(habitaciones: dict[str, dict]) -> float:
    resumen = resumen_cuadricula_logica(habitaciones)
    cantidad_habitaciones = int(resumen["cantidad_habitaciones"])
    if cantidad_habitaciones <= 1:
        return 0.0

    objetivo_area = min(36, max(cantidad_habitaciones, ceil(cantidad_habitaciones * 1.45)))
    objetivo_eje = 3 if cantidad_habitaciones <= 10 else 4
    penalizacion_area = penalizacion_faltante_normalizada(resumen["area_caja"], objetivo_area)
    penalizacion_filas = penalizacion_faltante_normalizada(resumen["filas_usadas"], objetivo_eje)
    penalizacion_columnas = penalizacion_faltante_normalizada(resumen["columnas_usadas"], objetivo_eje)
    penalizacion_ejes = (penalizacion_filas + penalizacion_columnas) / 2.0
    return (penalizacion_area + penalizacion_ejes) / 2.0


def penalizacion_ocupacion_cuadricula(habitaciones: dict[str, dict]) -> float:
    resumen = resumen_cuadricula_logica(habitaciones)
    if resumen["area_caja"] <= 0:
        return 0.0
    return penalizacion_rango(resumen["densidad_caja"], 0.55, 0.9)


def penalizacion_ramificacion_util(
    adyacencias: dict[str, set[str]],
    camino_principal: list[str],
) -> float:
    cantidad_habitaciones = len(adyacencias)
    if cantidad_habitaciones <= 2:
        return 0.0

    habitaciones_fuera_camino = max(0, cantidad_habitaciones - len(camino_principal))
    proporcion_fuera_camino = habitaciones_fuera_camino / cantidad_habitaciones
    if cantidad_habitaciones <= 10:
        objetivo_fuera_camino = 0.12
    elif cantidad_habitaciones <= 15:
        objetivo_fuera_camino = 0.18
    else:
        objetivo_fuera_camino = 0.24

    cantidad_bifurcaciones = sum(1 for vecinos in adyacencias.values() if len(vecinos) == 3)
    proporcion_bifurcaciones = cantidad_bifurcaciones / cantidad_habitaciones
    minimo_bifurcaciones = 0.0 if cantidad_habitaciones < 10 else 0.05
    penalizacion_camino = penalizacion_faltante_normalizada(proporcion_fuera_camino, objetivo_fuera_camino)
    penalizacion_bifurcaciones = penalizacion_rango(proporcion_bifurcaciones, minimo_bifurcaciones, 0.28)
    return (penalizacion_camino + penalizacion_bifurcaciones) / 2.0


def penalizacion_lineas_excesivas(habitaciones: dict[str, dict]) -> float:
    resumen = resumen_cuadricula_logica(habitaciones)
    aspecto = resumen["aspecto_caja"]
    if aspecto <= 2.2:
        return 0.0
    return min(1.0, (aspecto - 2.2) / (6.0 - 2.2))

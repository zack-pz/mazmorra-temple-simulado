from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from mazmorra.evaluacion import EstadoMazmorra
from mazmorra.generacion.constantes import TILE_BOSS, TILE_INICIO, TILE_PARED, TILE_PISO, TILE_SALIDA, TILE_TESORO
from mazmorra.generacion.topologia import COLUMNAS_CUADRICULA_LOGICA, FILAS_CUADRICULA_LOGICA, validar_cuadricula_logica


ANCHO_CELDA_RENDER = 12
ALTO_CELDA_RENDER = 10
MARGEN_EXTERIOR_RENDER = 3


def materializar_estado(mazmorra: dict) -> EstadoMazmorra:
    from copy import deepcopy

    validar_cuadricula_logica(mazmorra)
    habitaciones = deepcopy(mazmorra["habitaciones"])
    asignar_layout_desde_cuadricula(habitaciones)
    grid = construir_grid(
        habitaciones,
        mazmorra["conexiones"],
        mazmorra["habitacion_inicio"],
        mazmorra["habitacion_boss"],
        mazmorra["habitacion_salida"],
    )
    habitaciones_tesoro = [nombre for nombre, habitacion in habitaciones.items() if habitacion["tipo"] == "tesoro"]
    cantidad_enemigos = sum(habitacion.get("enemigos", 0) for habitacion in habitaciones.values())

    return EstadoMazmorra(
        habitaciones=habitaciones,
        conexiones=list(mazmorra["conexiones"]),
        habitacion_inicio=mazmorra["habitacion_inicio"],
        habitacion_boss=mazmorra["habitacion_boss"],
        habitacion_salida=mazmorra["habitacion_salida"],
        habitaciones_tesoro=habitaciones_tesoro,
        cantidad_enemigos=cantidad_enemigos,
        grid=grid,
        semilla=mazmorra["semilla"],
    )


def asignar_layout_desde_cuadricula(habitaciones: dict[str, dict]) -> None:
    for habitacion in habitaciones.values():
        fila = habitacion["fila"]
        columna = habitacion["columna"]
        origen_x = MARGEN_EXTERIOR_RENDER + columna * ANCHO_CELDA_RENDER
        origen_y = MARGEN_EXTERIOR_RENDER + fila * ALTO_CELDA_RENDER
        offset_x = max(1, (ANCHO_CELDA_RENDER - habitacion["w"]) // 2)
        offset_y = max(1, (ALTO_CELDA_RENDER - habitacion["h"]) // 2)

        habitacion["x"] = origen_x + offset_x
        habitacion["y"] = origen_y + offset_y
        habitacion["center"] = (
            habitacion["x"] + habitacion["w"] // 2,
            habitacion["y"] + habitacion["h"] // 2,
        )


def construir_grid(
    habitaciones: dict[str, dict],
    conexiones: list[tuple[str, str]],
    habitacion_inicio: str,
    habitacion_boss: str,
    habitacion_salida: str,
) -> np.ndarray:
    ancho = MARGEN_EXTERIOR_RENDER * 2 + COLUMNAS_CUADRICULA_LOGICA * ANCHO_CELDA_RENDER
    alto = MARGEN_EXTERIOR_RENDER * 2 + FILAS_CUADRICULA_LOGICA * ALTO_CELDA_RENDER
    grid = np.full((alto, ancho), TILE_PARED, dtype=int)

    for nombre, habitacion in habitaciones.items():
        grid[habitacion["y"] : habitacion["y"] + habitacion["h"], habitacion["x"] : habitacion["x"] + habitacion["w"]] = TILE_PISO

        centro_x, centro_y = habitacion["center"]
        if nombre == habitacion_inicio:
            grid[centro_y, centro_x] = TILE_INICIO
        elif nombre == habitacion_boss:
            grid[centro_y, centro_x] = TILE_BOSS
        elif nombre == habitacion_salida:
            grid[centro_y, centro_x] = TILE_SALIDA
        elif habitacion["tipo"] == "tesoro":
            grid[centro_y, centro_x] = TILE_TESORO

    for origen, destino in conexiones:
        tallar_pasillo(grid, habitaciones[origen]["center"], habitaciones[destino]["center"])

    return grid


def tallar_pasillo(grid: np.ndarray, inicio: tuple[int, int], fin: tuple[int, int]) -> None:
    x1, y1 = inicio
    x2, y2 = fin

    x_min, x_max = sorted((x1, x2))
    y_min, y_max = sorted((y1, y2))

    grid[y1, x_min : x_max + 1] = TILE_PISO
    grid[y_min : y_max + 1, x2] = TILE_PISO


def guardar_visualizaciones(estado: EstadoMazmorra, ruta_logica: str, ruta_espacial: str) -> None:
    guardar_visualizacion_logica(estado, ruta_logica)
    guardar_visualizacion_espacial(estado, ruta_espacial)


def guardar_visualizacion_logica(estado: EstadoMazmorra, ruta_salida: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    fig.suptitle(f"Estructura lógica · seed={estado.semilla}", fontsize=14, weight="bold")
    dibujar_grafo(ax, estado)
    plt.savefig(ruta_salida, dpi=180, bbox_inches="tight")
    plt.close(fig)


def guardar_visualizacion_espacial(estado: EstadoMazmorra, ruta_salida: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    fig.suptitle(f"Mapa espacial · seed={estado.semilla}", fontsize=14, weight="bold")
    dibujar_grid(ax, estado.grid)
    plt.savefig(ruta_salida, dpi=180, bbox_inches="tight")
    plt.close(fig)


def dibujar_grafo(ax, estado: EstadoMazmorra) -> None:
    colores = {
        "inicio": "#22c55e",
        "combate": "#ef4444",
        "tesoro": "#f59e0b",
        "descanso": "#60a5fa",
        "boss": "#7c3aed",
        "salida": "#14b8a6",
    }

    ax.set_title("Estructura lógica generada")
    ax.set_xticks(np.arange(MARGEN_EXTERIOR_RENDER, MARGEN_EXTERIOR_RENDER + COLUMNAS_CUADRICULA_LOGICA * ANCHO_CELDA_RENDER + 1, ANCHO_CELDA_RENDER))
    ax.set_yticks(np.arange(MARGEN_EXTERIOR_RENDER, MARGEN_EXTERIOR_RENDER + FILAS_CUADRICULA_LOGICA * ALTO_CELDA_RENDER + 1, ALTO_CELDA_RENDER))

    for origen, destino in estado.conexiones:
        x1, y1 = estado.habitaciones[origen]["center"]
        x2, y2 = estado.habitaciones[destino]["center"]
        ax.plot([x1, x2], [y1, y2], color="#94a3b8", linewidth=2, zorder=1)

    for nombre, habitacion in estado.habitaciones.items():
        x, y = habitacion["center"]
        etiqueta = f"{nombre}\nE:{habitacion.get('enemigos', 0)} C:{habitacion.get('cofres', 0)}"
        ax.scatter(x, y, s=700, color=colores.get(habitacion["tipo"], "#cbd5e1"), edgecolor="#0f172a", zorder=2)
        ax.text(x, y, etiqueta, ha="center", va="center", fontsize=7, weight="bold")

    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.grid(alpha=0.3)


def dibujar_grid(ax, grid: np.ndarray | None) -> None:
    cmap = ListedColormap(
        [
            "#111827",
            "#e5e7eb",
            "#22c55e",
            "#14b8a6",
            "#f59e0b",
            "#7c3aed",
        ]
    )
    ax.set_title("Mapa espacial generado")
    if grid is None:
        return

    ax.imshow(grid, cmap=cmap, interpolation="nearest", vmin=0, vmax=5)
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="#cbd5e1", linewidth=0.35)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

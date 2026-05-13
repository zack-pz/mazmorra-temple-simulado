from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle

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

    for _, habitacion in habitaciones.items():
        grid[habitacion["y"] : habitacion["y"] + habitacion["h"], habitacion["x"] : habitacion["x"] + habitacion["w"]] = TILE_PISO

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
    dibujar_marcadores_contenido(ax, estado)
    dibujar_leyenda_contenido(ax)
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


def dibujar_marcadores_contenido(ax, estado: EstadoMazmorra) -> None:
    for nombre, habitacion in estado.habitaciones.items():
        marcadores = construir_marcadores_habitacion(nombre, habitacion, estado)
        if not marcadores:
            continue

        slots = calcular_slots_marcadores(habitacion)
        if not slots:
            continue

        marcadores_visibles = compactar_marcadores_si_hace_falta(marcadores, len(slots))

        for marcador, (x, y) in zip(marcadores_visibles, slots):
            dibujar_marcador(ax, x, y, marcador)


def construir_marcadores_habitacion(nombre: str, habitacion: dict, estado: EstadoMazmorra) -> list[dict[str, str | int]]:
    marcadores: list[dict[str, str | int]] = []

    if nombre == estado.habitacion_inicio:
        marcadores.append(crear_marcador("inicio", "#22c55e"))
    if nombre == estado.habitacion_boss:
        marcadores.append(crear_marcador("boss", "#7c3aed"))
    if nombre == estado.habitacion_salida:
        marcadores.append(crear_marcador("salida", "#14b8a6"))
    if habitacion["tipo"] == "descanso":
        marcadores.append(crear_marcador("descanso", "#60a5fa"))

    for _ in range(habitacion.get("cofres", 0)):
        marcadores.append(crear_marcador("cofre", "#f59e0b"))

    for _ in range(habitacion.get("enemigos", 0)):
        marcadores.append(crear_marcador("enemigo", "#ef4444"))

    return marcadores


def crear_marcador(tipo: str, color: str, texto: str = "") -> dict[str, str | int]:
    return {
        "tipo": tipo,
        "color": color,
        "texto": texto,
    }


def calcular_slots_marcadores(habitacion: dict) -> list[tuple[float, float]]:
    x_inicio = habitacion["x"] + 1
    x_fin = habitacion["x"] + habitacion["w"] - 2
    y_inicio = habitacion["y"] + 1
    y_fin = habitacion["y"] + habitacion["h"] - 2

    if x_inicio > x_fin or y_inicio > y_fin:
        centro_x, centro_y = habitacion["center"]
        return [(float(centro_x), float(centro_y))]

    slots = [(float(x), float(y)) for y in range(y_inicio, y_fin + 1) for x in range(x_inicio, x_fin + 1)]
    centro_x, centro_y = habitacion["center"]
    slots.sort(key=lambda slot: (abs(slot[0] - centro_x) + abs(slot[1] - centro_y), slot[1], slot[0]))
    return slots


def compactar_marcadores_si_hace_falta(marcadores: list[dict[str, str | int]], capacidad: int) -> list[dict[str, str | int]]:
    if len(marcadores) <= capacidad:
        return marcadores

    conteos: dict[str, int] = {}
    colores: dict[str, str] = {}
    orden_tipos: list[str] = []

    for marcador in marcadores:
        tipo = str(marcador["tipo"])
        if tipo not in conteos:
            conteos[tipo] = 0
            colores[tipo] = str(marcador["color"])
            orden_tipos.append(tipo)
        conteos[tipo] += 1

    compactados: list[dict[str, str | int]] = []
    for tipo in orden_tipos:
        cantidad = conteos[tipo]
        texto = "" if cantidad == 1 else str(cantidad)
        compactados.append(crear_marcador(tipo, colores[tipo], texto=texto))

    if len(compactados) <= capacidad:
        return compactados

    visibles = compactados[: max(1, capacidad - 1)]
    ocultos = len(compactados) - len(visibles)
    visibles.append(crear_marcador("extra", "#94a3b8", texto=f"+{ocultos}"))
    return visibles[:capacidad]


def dibujar_marcador(ax, x: float, y: float, marcador: dict[str, str | int]) -> None:
    lado = 0.72
    esquina_x = x - lado / 2
    esquina_y = y - lado / 2
    rectangulo = Rectangle(
        (esquina_x, esquina_y),
        lado,
        lado,
        facecolor=str(marcador["color"]),
        edgecolor="#0f172a",
        linewidth=0.6,
        zorder=4,
    )
    ax.add_patch(rectangulo)

    texto = str(marcador.get("texto", ""))
    if texto:
        ax.text(x, y, texto, ha="center", va="center", fontsize=5.5, color="#f8fafc", weight="bold", zorder=5)


def dibujar_leyenda_contenido(ax) -> None:
    leyenda = [
        Patch(facecolor="#22c55e", edgecolor="#0f172a", label="Inicio"),
        Patch(facecolor="#14b8a6", edgecolor="#0f172a", label="Salida"),
        Patch(facecolor="#7c3aed", edgecolor="#0f172a", label="Boss"),
        Patch(facecolor="#60a5fa", edgecolor="#0f172a", label="Descanso"),
        Patch(facecolor="#f59e0b", edgecolor="#0f172a", label="Cofre"),
        Patch(facecolor="#ef4444", edgecolor="#0f172a", label="Enemigo"),
    ]
    ax.legend(handles=leyenda, loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=True, title="Contenido")

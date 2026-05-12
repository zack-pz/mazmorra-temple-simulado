from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
from math import exp
import random

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from mazmorra.objective import EstadoMazmorra, evaluar_mazmorra, minimos_tesoro_por_tamano


TIPOS_SALA_MUTABLES = ("combate", "tesoro", "descanso")
TIPOS_SALA_COMBATE = {"combate", "tesoro", "boss"}

TILE_PARED = 0
TILE_PISO = 1
TILE_INICIO = 2
TILE_SALIDA = 3
TILE_TESORO = 4
TILE_BOSS = 5


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


def generar_mazmorra(configuracion: ConfiguracionGenerador | None = None) -> ResultadoGeneracion:
    configuracion = configuracion or ConfiguracionGenerador()
    aleatorio = random.Random(configuracion.semilla)

    actual = crear_mazmorra_inicial(aleatorio, configuracion.semilla)
    estado_actual = materializar_estado(actual)
    evaluacion_actual = evaluar_mazmorra(estado_actual)

    mejor = deepcopy(actual)
    mejor_estado = estado_actual
    mejor_evaluacion = evaluacion_actual
    energia_inicial = evaluacion_actual["energia"]

    for iteracion in range(configuracion.iteraciones):
        temperatura = interpolar_temperatura(
            paso=iteracion,
            total_pasos=configuracion.iteraciones,
            temperatura_inicial=configuracion.temperatura_inicial,
            temperatura_final=configuracion.temperatura_final,
        )

        vecino = mutar_mazmorra(actual, aleatorio)
        estado_vecino = materializar_estado(vecino)
        evaluacion_vecino = evaluar_mazmorra(estado_vecino)

        if aceptar_vecino(
            energia_actual=evaluacion_actual["energia"],
            energia_vecino=evaluacion_vecino["energia"],
            temperatura=temperatura,
            aleatorio=aleatorio,
        ):
            actual = vecino
            estado_actual = estado_vecino
            evaluacion_actual = evaluacion_vecino

        if evaluacion_actual["energia"] < mejor_evaluacion["energia"]:
            mejor = deepcopy(actual)
            mejor_estado = estado_actual
            mejor_evaluacion = evaluacion_actual

    return ResultadoGeneracion(
        estado=mejor_estado,
        evaluacion=mejor_evaluacion,
        semilla=configuracion.semilla,
        iteraciones=configuracion.iteraciones,
        energia_inicial=energia_inicial,
        energia_final=mejor_evaluacion["energia"],
    )


def interpolar_temperatura(
    paso: int,
    total_pasos: int,
    temperatura_inicial: float,
    temperatura_final: float,
) -> float:
    if total_pasos <= 1:
        return temperatura_final

    proporcion = paso / float(total_pasos - 1)
    return temperatura_inicial * ((temperatura_final / temperatura_inicial) ** proporcion)


def aceptar_vecino(
    energia_actual: float,
    energia_vecino: float,
    temperatura: float,
    aleatorio: random.Random,
) -> bool:
    if energia_vecino <= energia_actual:
        return True

    if temperatura <= 0:
        return False

    probabilidad = exp(-(energia_vecino - energia_actual) / temperatura)
    return aleatorio.random() < probabilidad


def crear_mazmorra_inicial(aleatorio: random.Random, semilla: int) -> dict:
    cantidad_habitaciones = aleatorio.randint(8, 20)
    cantidad_tesoros = minimos_tesoro_por_tamano(cantidad_habitaciones)
    cantidad_descanso = aleatorio.randint(0, min(2, max(0, cantidad_habitaciones - 7)))
    cantidad_combate = cantidad_habitaciones - 3 - cantidad_tesoros - cantidad_descanso

    if cantidad_combate < 1:
        cantidad_descanso = max(0, cantidad_descanso - (1 - cantidad_combate))
        cantidad_combate = cantidad_habitaciones - 3 - cantidad_tesoros - cantidad_descanso

    nombres_por_tipo: dict[str, int] = defaultdict(int)
    habitaciones: dict[str, dict] = {}

    def crear_habitacion(tipo: str) -> str:
        if tipo in {"inicio", "boss", "salida"}:
            nombre = tipo
        else:
            nombres_por_tipo[tipo] += 1
            nombre = f"{tipo}_{nombres_por_tipo[tipo]}"

        habitaciones[nombre] = {
            "tipo": tipo,
            "enemigos": 0,
            "cofres": 0,
            "w": aleatorio.randint(4, 7),
            "h": aleatorio.randint(4, 6),
        }
        return nombre

    inicio = crear_habitacion("inicio")
    boss = crear_habitacion("boss")
    salida = crear_habitacion("salida")

    salas_intermedias = [crear_habitacion("combate") for _ in range(cantidad_combate)]
    salas_intermedias += [crear_habitacion("tesoro") for _ in range(cantidad_tesoros)]
    salas_intermedias += [crear_habitacion("descanso") for _ in range(cantidad_descanso)]
    aleatorio.shuffle(salas_intermedias)

    cantidad_camino_principal = min(len(salas_intermedias), aleatorio.randint(3, max(3, len(salas_intermedias))))
    camino_principal = [inicio, *salas_intermedias[:cantidad_camino_principal], boss, salida]

    conexiones: list[tuple[str, str]] = []
    for indice in range(len(camino_principal) - 1):
        conexiones.append((camino_principal[indice], camino_principal[indice + 1]))

    restantes = salas_intermedias[cantidad_camino_principal:]
    while restantes:
        longitud_rama = min(len(restantes), aleatorio.randint(1, 3))
        padre = aleatorio.choice(camino_principal[:-1])
        rama = [restantes.pop() for _ in range(longitud_rama)]
        conexiones.append((padre, rama[0]))
        for indice in range(len(rama) - 1):
            conexiones.append((rama[indice], rama[indice + 1]))

    mazmorra = {
        "habitaciones": habitaciones,
        "conexiones": conexiones,
        "habitacion_inicio": inicio,
        "habitacion_boss": boss,
        "habitacion_salida": salida,
        "semilla": semilla,
    }
    recalibrar_atributos(mazmorra, aleatorio)
    return mazmorra


def recalibrar_atributos(mazmorra: dict, aleatorio: random.Random) -> None:
    profundidades = calcular_profundidades(mazmorra["conexiones"], mazmorra["habitacion_inicio"])

    for nombre, habitacion in mazmorra["habitaciones"].items():
        tipo = habitacion["tipo"]
        profundidad = profundidades.get(nombre, 0)

        if tipo == "inicio":
            habitacion["enemigos"] = 0
            habitacion["cofres"] = 0
        elif tipo == "combate":
            habitacion["enemigos"] = max(1, 2 + profundidad // 2 + aleatorio.randint(0, 2))
            habitacion["cofres"] = 1 if aleatorio.random() < 0.15 else 0
        elif tipo == "tesoro":
            habitacion["enemigos"] = max(1, 1 + profundidad // 3 + aleatorio.randint(0, 1))
            habitacion["cofres"] = aleatorio.randint(1, 2)
        elif tipo == "descanso":
            habitacion["enemigos"] = 0
            habitacion["cofres"] = 1 if aleatorio.random() < 0.35 else 0
        elif tipo == "boss":
            habitacion["enemigos"] = max(6, 7 + profundidad // 2 + aleatorio.randint(0, 2))
            habitacion["cofres"] = 0
        elif tipo == "salida":
            habitacion["enemigos"] = 0
            habitacion["cofres"] = 0


def calcular_profundidades(conexiones: list[tuple[str, str]], inicio: str) -> dict[str, int]:
    adyacencias: dict[str, set[str]] = defaultdict(set)
    for origen, destino in conexiones:
        adyacencias[origen].add(destino)
        adyacencias[destino].add(origen)

    profundidades = {inicio: 0}
    cola = deque([inicio])

    while cola:
        actual = cola.popleft()
        for vecino in adyacencias[actual]:
            if vecino in profundidades:
                continue
            profundidades[vecino] = profundidades[actual] + 1
            cola.append(vecino)

    return profundidades


def mutar_mazmorra(mazmorra: dict, aleatorio: random.Random) -> dict:
    mutada = deepcopy(mazmorra)
    operador = aleatorio.choice(
        (
            mutar_tipo_sala,
            mutar_enemigos,
            mutar_cofres,
            mutar_conexion_hoja,
            mutar_tamano_sala,
        )
    )
    operador(mutada, aleatorio)
    recalibrar_atributos(mutada, aleatorio)
    return mutada


def mutar_tipo_sala(mazmorra: dict, aleatorio: random.Random) -> None:
    candidatas = [
        nombre
        for nombre, habitacion in mazmorra["habitaciones"].items()
        if habitacion["tipo"] in TIPOS_SALA_MUTABLES
    ]
    if not candidatas:
        return

    nombre = aleatorio.choice(candidatas)
    tipo_actual = mazmorra["habitaciones"][nombre]["tipo"]
    tipos_disponibles = [tipo for tipo in TIPOS_SALA_MUTABLES if tipo != tipo_actual]
    mazmorra["habitaciones"][nombre]["tipo"] = aleatorio.choice(tipos_disponibles)


def mutar_enemigos(mazmorra: dict, aleatorio: random.Random) -> None:
    candidatas = [
        nombre
        for nombre, habitacion in mazmorra["habitaciones"].items()
        if habitacion["tipo"] in TIPOS_SALA_COMBATE
    ]
    if not candidatas:
        return

    nombre = aleatorio.choice(candidatas)
    delta = aleatorio.choice((-2, -1, 1, 2))
    mazmorra["habitaciones"][nombre]["enemigos"] = max(0, mazmorra["habitaciones"][nombre]["enemigos"] + delta)


def mutar_cofres(mazmorra: dict, aleatorio: random.Random) -> None:
    candidatas = [
        nombre
        for nombre, habitacion in mazmorra["habitaciones"].items()
        if habitacion["tipo"] in {"combate", "tesoro", "descanso"}
    ]
    if not candidatas:
        return

    nombre = aleatorio.choice(candidatas)
    delta = aleatorio.choice((-1, 1))
    mazmorra["habitaciones"][nombre]["cofres"] = max(0, mazmorra["habitaciones"][nombre]["cofres"] + delta)


def mutar_tamano_sala(mazmorra: dict, aleatorio: random.Random) -> None:
    nombre = aleatorio.choice(list(mazmorra["habitaciones"].keys()))
    habitacion = mazmorra["habitaciones"][nombre]
    habitacion["w"] = min(8, max(4, habitacion["w"] + aleatorio.choice((-1, 1))))
    habitacion["h"] = min(7, max(4, habitacion["h"] + aleatorio.choice((-1, 1))))


def mutar_conexion_hoja(mazmorra: dict, aleatorio: random.Random) -> None:
    grados = calcular_grados(mazmorra["conexiones"])
    hoja_candidata = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if grados.get(nombre, 0) == 1 and nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
    ]
    if not hoja_candidata:
        return

    hoja = aleatorio.choice(hoja_candidata)
    origen_actual = next(
        origen if destino == hoja else destino
        for origen, destino in mazmorra["conexiones"]
        if origen == hoja or destino == hoja
    )
    posibles_padres = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if nombre not in {hoja, origen_actual, mazmorra["habitacion_salida"]}
    ]
    if not posibles_padres:
        return

    nuevo_padre = aleatorio.choice(posibles_padres)
    nueva_conexion = tuple(sorted((hoja, nuevo_padre)))
    conexiones_existentes = {tuple(sorted(conexion)) for conexion in mazmorra["conexiones"]}
    if nueva_conexion in conexiones_existentes:
        return

    nuevas_conexiones = [
        conexion
        for conexion in mazmorra["conexiones"]
        if hoja not in conexion
    ]
    nuevas_conexiones.append((hoja, nuevo_padre))
    mazmorra["conexiones"] = nuevas_conexiones


def calcular_grados(conexiones: list[tuple[str, str]]) -> dict[str, int]:
    grados: dict[str, int] = defaultdict(int)
    for origen, destino in conexiones:
        grados[origen] += 1
        grados[destino] += 1
    return grados


def materializar_estado(mazmorra: dict) -> EstadoMazmorra:
    habitaciones = deepcopy(mazmorra["habitaciones"])
    asignar_layout(habitaciones, mazmorra["conexiones"], mazmorra["habitacion_inicio"])
    grid = construir_grid(habitaciones, mazmorra["conexiones"], mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"])
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


def asignar_layout(habitaciones: dict[str, dict], conexiones: list[tuple[str, str]], inicio: str) -> None:
    profundidades = calcular_profundidades(conexiones, inicio)
    capas: dict[int, list[str]] = defaultdict(list)
    for nombre in habitaciones:
        capas[profundidades.get(nombre, 0)].append(nombre)

    distancia_x = 12
    padding_y = 3

    for profundidad in sorted(capas):
        nombres = sorted(capas[profundidad])
        cursor_y = 2
        for nombre in nombres:
            habitacion = habitaciones[nombre]
            habitacion["x"] = 2 + profundidad * distancia_x
            habitacion["y"] = cursor_y
            habitacion["center"] = (
                habitacion["x"] + habitacion["w"] // 2,
                habitacion["y"] + habitacion["h"] // 2,
            )
            cursor_y += habitacion["h"] + padding_y


def construir_grid(
    habitaciones: dict[str, dict],
    conexiones: list[tuple[str, str]],
    habitacion_inicio: str,
    habitacion_boss: str,
    habitacion_salida: str,
) -> np.ndarray:
    ancho = max(habitacion["x"] + habitacion["w"] for habitacion in habitaciones.values()) + 3
    alto = max(habitacion["y"] + habitacion["h"] for habitacion in habitaciones.values()) + 3
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


def guardar_visualizacion(estado: EstadoMazmorra, ruta_salida: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), constrained_layout=True)
    fig.suptitle(f"Mazmorra generada con temple simulado · seed={estado.semilla}", fontsize=14, weight="bold")

    dibujar_grafo(axes[0], estado)
    dibujar_grid(axes[1], estado.grid)

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
    ax.grid(alpha=0.2)


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

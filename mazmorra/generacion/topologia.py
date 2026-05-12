from __future__ import annotations

from collections import defaultdict, deque
import random

from mazmorra.evaluacion import minimos_tesoro_por_tamano


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


def calcular_grados(conexiones: list[tuple[str, str]]) -> dict[str, int]:
    grados: dict[str, int] = defaultdict(int)
    for origen, destino in conexiones:
        grados[origen] += 1
        grados[destino] += 1
    return grados

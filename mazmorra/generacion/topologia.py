from __future__ import annotations

from collections import defaultdict, deque
import random

from mazmorra.evaluacion import minimos_tesoro_por_tamano


FILAS_CUADRICULA_LOGICA = 6
COLUMNAS_CUADRICULA_LOGICA = 6
MAXIMO_CELDAS_LOGICAS = FILAS_CUADRICULA_LOGICA * COLUMNAS_CUADRICULA_LOGICA


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
            "fila": None,
            "columna": None,
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
    grados_actuales: dict[str, int] = defaultdict(int)
    for origen, destino in conexiones:
        grados_actuales[origen] += 1
        grados_actuales[destino] += 1

    while restantes:
        longitud_rama = min(len(restantes), aleatorio.randint(1, 3))
        posibles_padres = [nombre for nombre in habitaciones if nombre != salida and grados_actuales.get(nombre, 0) < 4]
        padre = aleatorio.choice(posibles_padres)
        rama = [restantes.pop() for _ in range(longitud_rama)]
        conexiones.append((padre, rama[0]))
        grados_actuales[padre] += 1
        grados_actuales[rama[0]] += 1
        for indice in range(len(rama) - 1):
            conexiones.append((rama[indice], rama[indice + 1]))
            grados_actuales[rama[indice]] += 1
            grados_actuales[rama[indice + 1]] += 1

    mazmorra = {
        "habitaciones": habitaciones,
        "conexiones": conexiones,
        "habitacion_inicio": inicio,
        "habitacion_boss": boss,
        "habitacion_salida": salida,
        "semilla": semilla,
    }
    proyectar_cuadricula_logica(mazmorra, aleatorio)
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


def construir_adyacencias(conexiones: list[tuple[str, str]]) -> dict[str, set[str]]:
    adyacencias: dict[str, set[str]] = defaultdict(set)
    for origen, destino in conexiones:
        adyacencias[origen].add(destino)
        adyacencias[destino].add(origen)
    return adyacencias


def proyectar_cuadricula_logica(mazmorra: dict, aleatorio: random.Random, intentos_maximos: int = 80) -> None:
    habitaciones = mazmorra["habitaciones"]

    if len(habitaciones) > MAXIMO_CELDAS_LOGICAS:
        raise ValueError("La mazmorra supera la capacidad de la cuadrícula lógica 6x6")

    adyacencias = construir_adyacencias(mazmorra["conexiones"])
    for nombre in habitaciones:
        adyacencias.setdefault(nombre, set())

    grados = {nombre: len(vecinos) for nombre, vecinos in adyacencias.items()}
    if any(grado > 4 for grado in grados.values()):
        raise ValueError("Existe una habitación con más de 4 conexiones, imposible de proyectar ortogonalmente")

    inicio = mazmorra["habitacion_inicio"]
    tamanos_subarbol = calcular_tamanos_subarbol(adyacencias, inicio)
    celdas_centrales = ordenar_celdas_por_centralidad()

    for _ in range(intentos_maximos):
        ubicaciones: dict[str, tuple[int, int]] = {}
        ocupadas: set[tuple[int, int]] = set()
        celda_inicio = aleatorio.choice(celdas_centrales[:8])
        ubicaciones[inicio] = celda_inicio
        ocupadas.add(celda_inicio)

        if intentar_proyectar_subarbol(
            actual=inicio,
            padre=None,
            adyacencias=adyacencias,
            tamanos_subarbol=tamanos_subarbol,
            ubicaciones=ubicaciones,
            ocupadas=ocupadas,
            aleatorio=aleatorio,
        ):
            for nombre, (fila, columna) in ubicaciones.items():
                habitaciones[nombre]["fila"] = fila
                habitaciones[nombre]["columna"] = columna

            validar_cuadricula_logica(mazmorra)
            return

    raise ValueError("No se pudo proyectar la topología dentro de la cuadrícula lógica 6x6")


def calcular_tamanos_subarbol(adyacencias: dict[str, set[str]], raiz: str) -> dict[str, int]:
    tamanos: dict[str, int] = {}

    def visitar(actual: str, padre: str | None) -> int:
        total = 1
        for vecino in adyacencias[actual]:
            if vecino == padre:
                continue
            total += visitar(vecino, actual)
        tamanos[actual] = total
        return total

    visitar(raiz, None)
    return tamanos


def intentar_proyectar_subarbol(
    actual: str,
    padre: str | None,
    adyacencias: dict[str, set[str]],
    tamanos_subarbol: dict[str, int],
    ubicaciones: dict[str, tuple[int, int]],
    ocupadas: set[tuple[int, int]],
    aleatorio: random.Random,
    celdas_restringidas: set[tuple[int, int]] | None = None,
) -> bool:
    celdas_restringidas = celdas_restringidas or set()
    hijos = [vecino for vecino in adyacencias[actual] if vecino != padre]
    hijos.sort(key=lambda nombre: tamanos_subarbol.get(nombre, 1), reverse=True)

    if not hijos:
        return True

    vecinos_libres = [
        celda
        for celda in vecinos_ortogonales(*ubicaciones[actual])
        if celda not in ocupadas and celda not in celdas_restringidas
    ]
    if len(hijos) > len(vecinos_libres):
        return False

    aleatorio.shuffle(vecinos_libres)

    def asignar_hijos(indice: int, libres: list[tuple[int, int]]) -> bool:
        if indice >= len(hijos):
            return True

        hijo = hijos[indice]
        candidatos = ordenar_celdas_para_hijo(actual, libres, ocupadas)
        for celda in candidatos:
            snapshot = set(ubicaciones.keys())
            ubicaciones[hijo] = celda
            ocupadas.add(celda)
            celdas_bloqueadas = set(libres) - {celda}

            if intentar_proyectar_subarbol(
                hijo,
                actual,
                adyacencias,
                tamanos_subarbol,
                ubicaciones,
                ocupadas,
                aleatorio,
                celdas_restringidas=celdas_restringidas | celdas_bloqueadas,
            ) and asignar_hijos(indice + 1, [libre for libre in libres if libre != celda]):
                return True

            restaurar_ubicaciones(snapshot, ubicaciones, ocupadas)

        return False

    return asignar_hijos(0, vecinos_libres)


def restaurar_ubicaciones(
    snapshot: set[str],
    ubicaciones: dict[str, tuple[int, int]],
    ocupadas: set[tuple[int, int]],
) -> None:
    for nombre in list(ubicaciones.keys()):
        if nombre in snapshot:
            continue
        ocupadas.discard(ubicaciones[nombre])
        del ubicaciones[nombre]


def ordenar_celdas_para_hijo(
    actual: str,
    libres: list[tuple[int, int]],
    ocupadas: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    del actual
    return sorted(
        libres,
        key=lambda celda: (
            -sum(1 for vecino in vecinos_ortogonales(*celda) if vecino not in ocupadas),
            distancia_al_centro(*celda),
        ),
    )


def ordenar_celdas_por_centralidad() -> list[tuple[int, int]]:
    celdas = [(fila, columna) for fila in range(FILAS_CUADRICULA_LOGICA) for columna in range(COLUMNAS_CUADRICULA_LOGICA)]
    return sorted(celdas, key=lambda celda: (distancia_al_centro(*celda), celda[0], celda[1]))


def distancia_al_centro(fila: int, columna: int) -> float:
    centro_fila = (FILAS_CUADRICULA_LOGICA - 1) / 2
    centro_columna = (COLUMNAS_CUADRICULA_LOGICA - 1) / 2
    return abs(fila - centro_fila) + abs(columna - centro_columna)


def vecinos_ortogonales(fila: int, columna: int) -> list[tuple[int, int]]:
    candidatos = [
        (fila - 1, columna),
        (fila + 1, columna),
        (fila, columna - 1),
        (fila, columna + 1),
    ]
    return [
        (fila_candidata, columna_candidata)
        for fila_candidata, columna_candidata in candidatos
        if 0 <= fila_candidata < FILAS_CUADRICULA_LOGICA and 0 <= columna_candidata < COLUMNAS_CUADRICULA_LOGICA
    ]


def validar_cuadricula_logica(mazmorra: dict) -> None:
    ocupadas: set[tuple[int, int]] = set()

    for nombre, habitacion in mazmorra["habitaciones"].items():
        fila = habitacion.get("fila")
        columna = habitacion.get("columna")

        if fila is None or columna is None:
            raise ValueError(f"La habitación {nombre} no tiene celda lógica asignada")
        if not (0 <= fila < FILAS_CUADRICULA_LOGICA and 0 <= columna < COLUMNAS_CUADRICULA_LOGICA):
            raise ValueError(f"La habitación {nombre} quedó fuera de la cuadrícula lógica 6x6")

        celda = (fila, columna)
        if celda in ocupadas:
            raise ValueError(f"Dos habitaciones ocupan la misma celda lógica: {celda}")
        ocupadas.add(celda)

    for origen, destino in mazmorra["conexiones"]:
        fila_origen = mazmorra["habitaciones"][origen]["fila"]
        columna_origen = mazmorra["habitaciones"][origen]["columna"]
        fila_destino = mazmorra["habitaciones"][destino]["fila"]
        columna_destino = mazmorra["habitaciones"][destino]["columna"]
        distancia = abs(fila_origen - fila_destino) + abs(columna_origen - columna_destino)
        if distancia != 1:
            raise ValueError(f"La conexión {origen} -> {destino} no respeta vecindad ortogonal en la cuadrícula lógica")

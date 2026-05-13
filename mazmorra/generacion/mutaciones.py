from __future__ import annotations

from collections import deque
from copy import deepcopy
import random

from mazmorra.generacion.constantes import TIPOS_SALA_COMBATE, TIPOS_SALA_MUTABLES
from mazmorra.generacion.topologia import (
    FILAS_CUADRICULA_LOGICA,
    COLUMNAS_CUADRICULA_LOGICA,
    GRADO_MAXIMO_HABITACION,
    calcular_grados,
    construir_adyacencias,
    proyectar_cuadricula_logica,
    recalibrar_atributos,
    validar_cuadricula_logica,
    validar_grados_habitaciones,
    vecinos_ortogonales,
)


def mutar_mazmorra(mazmorra: dict, aleatorio: random.Random) -> dict:
    mutada = deepcopy(mazmorra)
    operador = aleatorio.choice(
        (
            mutar_tipo_sala,
            mutar_enemigos,
            mutar_cofres,
            mutar_conexion_hoja,
            mutar_romper_corredor_largo,
            mutar_reconectar_vecindad_ortogonal,
            mutar_relocalizar_subrama,
            mutar_tamano_sala,
            mutar_disposicion_logica,
        )
    )
    try:
        operador(mutada, aleatorio)
    except ValueError:
        return deepcopy(mazmorra)
    requiere_reproyeccion = operador in {mutar_relocalizar_subrama}
    try:
        validar_grados_habitaciones(mutada)
    except ValueError:
        return deepcopy(mazmorra)
    if requiere_reproyeccion and not proyectar_o_revertir(mutada, mazmorra, aleatorio):
        return deepcopy(mazmorra)
    if operador in {mutar_conexion_hoja, mutar_reconectar_vecindad_ortogonal, mutar_disposicion_logica}:
        try:
            validar_cuadricula_logica(mutada)
        except ValueError:
            return deepcopy(mazmorra)
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


def mutar_disposicion_logica(mazmorra: dict, aleatorio: random.Random) -> None:
    operadores = [mover_habitacion_a_celda_libre, mutar_conexion_hoja]
    aleatorio.shuffle(operadores)
    for operador in operadores:
        if operador(mazmorra, aleatorio):
            return


def mutar_conexion_hoja(mazmorra: dict, aleatorio: random.Random) -> bool:
    grados = calcular_grados(mazmorra["conexiones"])
    hojas_reubicables = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if grados.get(nombre, 0) == 1
        if nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
    ]
    if not hojas_reubicables:
        return False

    ocupacion = construir_ocupacion_habitaciones(mazmorra)
    aleatorio.shuffle(hojas_reubicables)

    for hoja in hojas_reubicables:
        origen_actual = obtener_vecino_unico(mazmorra, hoja)
        posibles_padres = [
            nombre
            for nombre in mazmorra["habitaciones"]
            if nombre not in {hoja, origen_actual, mazmorra["habitacion_salida"]}
            and grados.get(nombre, 0) < GRADO_MAXIMO_HABITACION
        ]
        aleatorio.shuffle(posibles_padres)

        for nuevo_padre in posibles_padres:
            celdas_libres = celdas_libres_adyacentes_a_habitacion(mazmorra, ocupacion, nuevo_padre)
            if not celdas_libres:
                continue

            celda_original = obtener_celda_habitacion(mazmorra, hoja)
            nueva_conexion = tuple(sorted((hoja, nuevo_padre)))
            conexiones_existentes = {tuple(sorted(conexion)) for conexion in mazmorra["conexiones"]}
            if nueva_conexion in conexiones_existentes:
                continue

            nueva_celda = aleatorio.choice(celdas_libres)
            actualizar_celda_habitacion(mazmorra, hoja, nueva_celda)
            nuevas_conexiones = [conexion for conexion in mazmorra["conexiones"] if hoja not in conexion]
            nuevas_conexiones.append((hoja, nuevo_padre))
            mazmorra["conexiones"] = nuevas_conexiones

            try:
                validar_cuadricula_logica(mazmorra)
                return True
            except ValueError:
                actualizar_celda_habitacion(mazmorra, hoja, celda_original)
                mazmorra["conexiones"] = restaurar_conexion_hoja(nuevas_conexiones, hoja, origen_actual)

    return False


def mutar_reconectar_vecindad_ortogonal(mazmorra: dict, aleatorio: random.Random) -> None:
    grados = calcular_grados(mazmorra["conexiones"])
    ocupacion = construir_ocupacion_habitaciones(mazmorra)
    hojas_reubicables = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if grados.get(nombre, 0) == 1
        and nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
    ]
    aleatorio.shuffle(hojas_reubicables)

    for hoja in hojas_reubicables:
        origen_actual = obtener_vecino_unico(mazmorra, hoja)
        fila, columna = obtener_celda_habitacion(mazmorra, hoja)
        vecinos_fisicos = [
            ocupacion[celda]
            for celda in vecinos_ortogonales(fila, columna)
            if celda in ocupacion and ocupacion[celda] != origen_actual
        ]
        candidatos = [
            vecino
            for vecino in vecinos_fisicos
            if vecino != mazmorra["habitacion_salida"] and grados.get(vecino, 0) < GRADO_MAXIMO_HABITACION
        ]
        aleatorio.shuffle(candidatos)

        for nuevo_padre in candidatos:
            nueva_conexion = tuple(sorted((hoja, nuevo_padre)))
            conexiones_existentes = {tuple(sorted(conexion)) for conexion in mazmorra["conexiones"]}
            if nueva_conexion in conexiones_existentes:
                continue

            nuevas_conexiones = [conexion for conexion in mazmorra["conexiones"] if hoja not in conexion]
            nuevas_conexiones.append((hoja, nuevo_padre))
            mazmorra["conexiones"] = nuevas_conexiones

            try:
                validar_cuadricula_logica(mazmorra)
                return
            except ValueError:
                mazmorra["conexiones"] = restaurar_conexion_hoja(nuevas_conexiones, hoja, origen_actual)


def mutar_romper_corredor_largo(mazmorra: dict, aleatorio: random.Random) -> None:
    grados = calcular_grados(mazmorra["conexiones"])
    ocupacion = construir_ocupacion_habitaciones(mazmorra)
    hojas_reubicables = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if grados.get(nombre, 0) == 1
        and nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
    ]
    candidatos_corredor = obtener_nodos_corredor_largo(mazmorra, grados)

    if not hojas_reubicables or not candidatos_corredor:
        raise ValueError("No hay hojas o corredores largos para romper")

    aleatorio.shuffle(hojas_reubicables)
    aleatorio.shuffle(candidatos_corredor)

    for objetivo in candidatos_corredor:
        celdas_libres = celdas_libres_adyacentes_a_habitacion(mazmorra, ocupacion, objetivo)
        if not celdas_libres:
            continue

        for hoja in hojas_reubicables:
            origen_actual = obtener_vecino_unico(mazmorra, hoja)
            if hoja == objetivo or origen_actual == objetivo:
                continue

            nueva_conexion = tuple(sorted((hoja, objetivo)))
            conexiones_existentes = {tuple(sorted(conexion)) for conexion in mazmorra["conexiones"]}
            if nueva_conexion in conexiones_existentes:
                continue

            celda_original = obtener_celda_habitacion(mazmorra, hoja)
            nueva_celda = aleatorio.choice(celdas_libres)
            actualizar_celda_habitacion(mazmorra, hoja, nueva_celda)
            nuevas_conexiones = [conexion for conexion in mazmorra["conexiones"] if hoja not in conexion]
            nuevas_conexiones.append((hoja, objetivo))
            mazmorra["conexiones"] = nuevas_conexiones

            try:
                validar_cuadricula_logica(mazmorra)
                return
            except ValueError:
                actualizar_celda_habitacion(mazmorra, hoja, celda_original)
                mazmorra["conexiones"] = restaurar_conexion_hoja(nuevas_conexiones, hoja, origen_actual)

    raise ValueError("No se pudo romper ningún corredor largo")


def mutar_relocalizar_subrama(mazmorra: dict, aleatorio: random.Random) -> None:
    adyacencias = construir_adyacencias(mazmorra["conexiones"])
    camino_principal = camino_entre_habitaciones(
        adyacencias,
        mazmorra["habitacion_inicio"],
        mazmorra["habitacion_salida"],
    )
    padres = construir_padres_desde_inicio(adyacencias, mazmorra["habitacion_inicio"])
    grados = calcular_grados(mazmorra["conexiones"])

    candidatos_raiz = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if nombre not in camino_principal
        and nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
        and nombre in padres
    ]
    aleatorio.shuffle(candidatos_raiz)

    for raiz_subrama in candidatos_raiz:
        padre_actual = padres[raiz_subrama]
        nodos_subrama = obtener_nodos_subrama(adyacencias, raiz_subrama, padre_actual)
        posibles_padres = [
            nombre
            for nombre in mazmorra["habitaciones"]
            if nombre not in nodos_subrama
            and nombre != padre_actual
            and nombre != mazmorra["habitacion_salida"]
            and grados.get(nombre, 0) < GRADO_MAXIMO_HABITACION
        ]
        aleatorio.shuffle(posibles_padres)

        for nuevo_padre in posibles_padres:
            nuevas_conexiones = [
                conexion
                for conexion in mazmorra["conexiones"]
                if set(conexion) != {raiz_subrama, padre_actual}
            ]
            nuevas_conexiones.append((raiz_subrama, nuevo_padre))
            if len(nuevas_conexiones) != len(mazmorra["conexiones"]):
                continue
            mazmorra["conexiones"] = nuevas_conexiones
            return


def mover_habitacion_a_celda_libre(mazmorra: dict, aleatorio: random.Random) -> bool:
    grados = calcular_grados(mazmorra["conexiones"])
    hojas_movibles = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if grados.get(nombre, 0) == 1
        and nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
    ]
    if not hojas_movibles:
        return False

    ocupacion = construir_ocupacion_habitaciones(mazmorra)
    aleatorio.shuffle(hojas_movibles)

    for hoja in hojas_movibles:
        padre = obtener_vecino_unico(mazmorra, hoja)
        celdas_destino = [
            celda
            for celda in celdas_libres_adyacentes_a_habitacion(mazmorra, ocupacion, padre)
            if celda != obtener_celda_habitacion(mazmorra, hoja)
        ]
        if not celdas_destino:
            continue

        celda_original = obtener_celda_habitacion(mazmorra, hoja)
        actualizar_celda_habitacion(mazmorra, hoja, aleatorio.choice(celdas_destino))
        try:
            validar_cuadricula_logica(mazmorra)
            return True
        except ValueError:
            actualizar_celda_habitacion(mazmorra, hoja, celda_original)

    return False


def construir_ocupacion_habitaciones(mazmorra: dict) -> dict[tuple[int, int], str]:
    ocupacion: dict[tuple[int, int], str] = {}
    for nombre, habitacion in mazmorra["habitaciones"].items():
        fila = habitacion.get("fila")
        columna = habitacion.get("columna")
        if fila is None or columna is None:
            raise ValueError(f"La habitación {nombre} no tiene celda lógica asignada")
        ocupacion[(fila, columna)] = nombre
    return ocupacion


def obtener_celda_habitacion(mazmorra: dict, nombre: str) -> tuple[int, int]:
    habitacion = mazmorra["habitaciones"][nombre]
    return habitacion["fila"], habitacion["columna"]


def actualizar_celda_habitacion(mazmorra: dict, nombre: str, celda: tuple[int, int]) -> None:
    fila, columna = celda
    if not (0 <= fila < FILAS_CUADRICULA_LOGICA and 0 <= columna < COLUMNAS_CUADRICULA_LOGICA):
        raise ValueError("La celda lógica queda fuera del rango permitido")
    mazmorra["habitaciones"][nombre]["fila"] = fila
    mazmorra["habitaciones"][nombre]["columna"] = columna


def celdas_libres_adyacentes_a_habitacion(
    mazmorra: dict,
    ocupacion: dict[tuple[int, int], str],
    nombre: str,
) -> list[tuple[int, int]]:
    fila, columna = obtener_celda_habitacion(mazmorra, nombre)
    return [celda for celda in vecinos_ortogonales(fila, columna) if celda not in ocupacion]


def obtener_vecino_unico(mazmorra: dict, nombre: str) -> str:
    vecinos = []
    for origen, destino in mazmorra["conexiones"]:
        if origen == nombre:
            vecinos.append(destino)
        elif destino == nombre:
            vecinos.append(origen)
    if len(vecinos) != 1:
        raise ValueError(f"La habitación {nombre} no es una hoja válida")
    return vecinos[0]


def restaurar_conexion_hoja(
    conexiones_sin_hoja: list[tuple[str, str]],
    hoja: str,
    padre_original: str,
) -> list[tuple[str, str]]:
    restauradas = [conexion for conexion in conexiones_sin_hoja if hoja not in conexion]
    restauradas.append((hoja, padre_original))
    return restauradas


def camino_entre_habitaciones(
    adyacencias: dict[str, set[str]],
    origen: str,
    destino: str,
) -> list[str]:
    padres: dict[str, str | None] = {origen: None}
    cola = deque([origen])

    while cola:
        actual = cola.popleft()
        if actual == destino:
            break
        for vecino in vecinos_habitacion_ordenados(adyacencias, actual):
            if vecino in padres:
                continue
            padres[vecino] = actual
            cola.append(vecino)

    if destino not in padres:
        raise ValueError("No existe camino entre las habitaciones indicadas")

    camino = [destino]
    actual = destino
    while padres[actual] is not None:
        actual = padres[actual]
        camino.append(actual)
    camino.reverse()
    return camino


def construir_padres_desde_inicio(adyacencias: dict[str, set[str]], inicio: str) -> dict[str, str]:
    padres: dict[str, str] = {}
    cola = deque([inicio])
    visitados = {inicio}

    while cola:
        actual = cola.popleft()
        for vecino in vecinos_habitacion_ordenados(adyacencias, actual):
            if vecino in visitados:
                continue
            visitados.add(vecino)
            padres[vecino] = actual
            cola.append(vecino)

    return padres


def obtener_nodos_subrama(
    adyacencias: dict[str, set[str]],
    raiz: str,
    padre: str,
) -> set[str]:
    nodos = {raiz}
    pila = [raiz]

    while pila:
        actual = pila.pop()
        for vecino in reversed(vecinos_habitacion_ordenados(adyacencias, actual)):
            if vecino == padre or vecino in nodos:
                continue
            nodos.add(vecino)
            pila.append(vecino)

    return nodos


def obtener_nodos_corredor_largo(mazmorra: dict, grados: dict[str, int]) -> list[str]:
    adyacencias = construir_adyacencias(mazmorra["conexiones"])
    nodos_candidatos: set[str] = set()

    for nombre in sorted(grados):
        grado = grados[nombre]
        if grado != 2:
            continue

        vecinos = vecinos_habitacion_ordenados(adyacencias, nombre)
        if len(vecinos) != 2:
            continue

        for vecino in vecinos:
            if grados.get(vecino, 0) == 2:
                nodos_candidatos.add(nombre)
                break

    return sorted(
        nombre
        for nombre in nodos_candidatos
        if nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
        and grados.get(nombre, 0) < GRADO_MAXIMO_HABITACION
    )


def vecinos_habitacion_ordenados(adyacencias: dict[str, set[str]], nombre: str) -> list[str]:
    return sorted(adyacencias.get(nombre, ()))


def proyectar_o_revertir(mutada: dict, original: dict, aleatorio: random.Random) -> bool:
    try:
        proyectar_cuadricula_logica(mutada, aleatorio)
        return True
    except ValueError:
        mutada.clear()
        mutada.update(deepcopy(original))
        return False

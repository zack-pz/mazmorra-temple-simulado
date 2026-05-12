from __future__ import annotations

from copy import deepcopy
import random

from mazmorra.generacion.constantes import TIPOS_SALA_COMBATE, TIPOS_SALA_MUTABLES
from mazmorra.generacion.topologia import (
    GRADO_MAXIMO_HABITACION,
    calcular_grados,
    proyectar_cuadricula_logica,
    recalibrar_atributos,
    validar_grados_habitaciones,
)


def mutar_mazmorra(mazmorra: dict, aleatorio: random.Random) -> dict:
    mutada = deepcopy(mazmorra)
    operador = aleatorio.choice(
        (
            mutar_tipo_sala,
            mutar_enemigos,
            mutar_cofres,
            mutar_conexion_hoja,
            mutar_tamano_sala,
            mutar_disposicion_logica,
        )
    )
    try:
        operador(mutada, aleatorio)
    except ValueError:
        return deepcopy(mazmorra)
    requiere_reproyeccion = operador in {mutar_conexion_hoja, mutar_disposicion_logica}
    try:
        validar_grados_habitaciones(mutada)
    except ValueError:
        return deepcopy(mazmorra)
    if requiere_reproyeccion and not proyectar_o_revertir(mutada, mazmorra, aleatorio):
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
    del mazmorra, aleatorio


def mutar_conexion_hoja(mazmorra: dict, aleatorio: random.Random) -> None:
    grados = calcular_grados(mazmorra["conexiones"])
    hojas_reubicables = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if grados.get(nombre, 0) == 1
        if nombre not in {mazmorra["habitacion_inicio"], mazmorra["habitacion_boss"], mazmorra["habitacion_salida"]}
    ]
    if not hojas_reubicables:
        return

    hoja = aleatorio.choice(hojas_reubicables)
    origen_actual = next(
        origen if destino == hoja else destino
        for origen, destino in mazmorra["conexiones"]
        if origen == hoja or destino == hoja
    )
    posibles_padres = [
        nombre
        for nombre in mazmorra["habitaciones"]
        if nombre not in {hoja, origen_actual, mazmorra["habitacion_salida"]}
        and grados.get(nombre, 0) < GRADO_MAXIMO_HABITACION
    ]
    if not posibles_padres:
        return

    nuevo_padre = aleatorio.choice(posibles_padres)
    nueva_conexion = tuple(sorted((hoja, nuevo_padre)))
    conexiones_existentes = {tuple(sorted(conexion)) for conexion in mazmorra["conexiones"]}
    if nueva_conexion in conexiones_existentes:
        return

    nuevas_conexiones = [conexion for conexion in mazmorra["conexiones"] if hoja not in conexion]
    nuevas_conexiones.append((hoja, nuevo_padre))
    mazmorra["conexiones"] = nuevas_conexiones


def proyectar_o_revertir(mutada: dict, original: dict, aleatorio: random.Random) -> bool:
    try:
        proyectar_cuadricula_logica(mutada, aleatorio)
        return True
    except ValueError:
        mutada.clear()
        mutada.update(deepcopy(original))
        return False

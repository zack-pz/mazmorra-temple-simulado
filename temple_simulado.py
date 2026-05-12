from __future__ import annotations

from copy import deepcopy
from math import exp
import random

from mazmorra.evaluacion import evaluar_mazmorra
from mazmorra.generacion.config import ConfiguracionGenerador, ResultadoGeneracion
from mazmorra.generacion.mutaciones import mutar_mazmorra
from mazmorra.generacion.render import materializar_estado
from mazmorra.generacion.topologia import crear_mazmorra_inicial


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


__all__ = [
    "aceptar_vecino",
    "generar_mazmorra",
    "interpolar_temperatura",
]

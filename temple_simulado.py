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
    evaluacion_inicial = deepcopy(evaluacion_actual)

    mejor = deepcopy(actual)
    mejor_estado = estado_actual
    mejor_evaluacion = evaluacion_actual
    energia_inicial = evaluacion_actual["energia"]
    iteracion_mejor = -1
    vecinos_generados = 0
    vecinos_aceptados = 0
    vecinos_rechazados = 0
    empeoramientos_aceptados = 0
    empeoramientos_rechazados = 0
    mejoras_directas_aceptadas = 0
    energia_maxima_visitada = energia_inicial

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
        vecinos_generados += 1
        energia_actual = evaluacion_actual["energia"]
        energia_vecino = evaluacion_vecino["energia"]
        es_empeoramiento = energia_vecino > energia_actual

        if aceptar_vecino(
            energia_actual=energia_actual,
            energia_vecino=energia_vecino,
            temperatura=temperatura,
            aleatorio=aleatorio,
        ):
            vecinos_aceptados += 1
            if es_empeoramiento:
                empeoramientos_aceptados += 1
            else:
                mejoras_directas_aceptadas += 1
            actual = vecino
            estado_actual = estado_vecino
            evaluacion_actual = evaluacion_vecino
            energia_maxima_visitada = max(energia_maxima_visitada, energia_vecino)
        else:
            vecinos_rechazados += 1
            if es_empeoramiento:
                empeoramientos_rechazados += 1

        if evaluacion_actual["energia"] < mejor_evaluacion["energia"]:
            mejor = deepcopy(actual)
            mejor_estado = estado_actual
            mejor_evaluacion = evaluacion_actual
            iteracion_mejor = iteracion

    mejora_absoluta = energia_inicial - mejor_evaluacion["energia"]
    mejora_porcentual = 0.0 if energia_inicial == 0 else (mejora_absoluta / energia_inicial) * 100.0
    tasa_aceptacion = 0.0 if vecinos_generados == 0 else vecinos_aceptados / vecinos_generados
    tasa_empeoramientos_aceptados = 0.0 if vecinos_generados == 0 else empeoramientos_aceptados / vecinos_generados
    tasa_empeoramientos_rechazados = 0.0 if vecinos_generados == 0 else empeoramientos_rechazados / vecinos_generados

    return ResultadoGeneracion(
        estado=mejor_estado,
        evaluacion=mejor_evaluacion,
        semilla=configuracion.semilla,
        iteraciones=configuracion.iteraciones,
        energia_inicial=energia_inicial,
        energia_final=mejor_evaluacion["energia"],
        evaluacion_inicial=evaluacion_inicial,
        estadisticas_recocido={
            "vecinos_generados": vecinos_generados,
            "vecinos_aceptados": vecinos_aceptados,
            "vecinos_rechazados": vecinos_rechazados,
            "mejoras_directas_aceptadas": mejoras_directas_aceptadas,
            "empeoramientos_aceptados": empeoramientos_aceptados,
            "empeoramientos_rechazados": empeoramientos_rechazados,
            "tasa_aceptacion": tasa_aceptacion,
            "tasa_empeoramientos_aceptados": tasa_empeoramientos_aceptados,
            "tasa_empeoramientos_rechazados": tasa_empeoramientos_rechazados,
            "iteracion_mejor": iteracion_mejor,
            "energia_maxima_visitada": energia_maxima_visitada,
            "mejora_absoluta": mejora_absoluta,
            "mejora_porcentual": mejora_porcentual,
        },
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

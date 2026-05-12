from __future__ import annotations

from math import inf

from mazmorra.evaluacion.grafo import camino_mas_corto, construir_adyacencias, contar_tipos, distancias_bfs
from mazmorra.evaluacion.modelo import EstadoMazmorra, PesosObjetivo
from mazmorra.evaluacion.penalizaciones import (
    habitaciones_tesoro_desde_estado,
    minimos_tesoro_por_tamano,
    obtener_boss,
    penalizacion_dispersion_cuadricula,
    penalizacion_faltante_normalizada,
    penalizacion_interes_tesoros,
    penalizacion_lineas_excesivas,
    penalizacion_ocupacion_cuadricula,
    penalizacion_progresion_dificultad,
    penalizacion_ramificacion_util,
    penalizacion_rango,
    penalizacion_salas_vacias,
    proporcion_piso,
    resumen_cuadricula_logica,
)

GRADO_MINIMO_EVALUACION = 1
GRADO_MAXIMO_EVALUACION = 4


def evaluar_mazmorra(
    estado: EstadoMazmorra,
    pesos: PesosObjetivo | None = None,
    distancia_salida_ideal: int = 9,
) -> dict:
    pesos = pesos or PesosObjetivo()
    adyacencias = construir_adyacencias(estado.conexiones)

    for nombre_habitacion in estado.habitaciones:
        adyacencias.setdefault(nombre_habitacion, set())

    distancias_desde_inicio = distancias_bfs(adyacencias, estado.habitacion_inicio)
    distancia_salida = distancias_desde_inicio.get(estado.habitacion_salida, inf)
    cantidad_habitaciones = len(estado.habitaciones)
    habitaciones_tesoro = habitaciones_tesoro_desde_estado(estado)
    cantidad_tesoros = len(habitaciones_tesoro)
    tesoros_bloqueados = sum(1 for habitacion in habitaciones_tesoro if habitacion not in distancias_desde_inicio)
    proporcion_actual_piso = proporcion_piso(estado.grid)
    boss = obtener_boss(estado)
    distancias_desde_boss = distancias_bfs(adyacencias, boss) if boss is not None else {}
    distancia_boss = distancias_desde_inicio.get(boss, inf) if boss is not None else inf
    distancia_boss_a_salida = distancias_desde_boss.get(estado.habitacion_salida, inf) if boss is not None else inf
    tipos = contar_tipos(estado.habitaciones)
    minimo_tesoros = minimos_tesoro_por_tamano(cantidad_habitaciones)
    penalizacion_min_tesoros = penalizacion_faltante_normalizada(cantidad_tesoros, minimo_tesoros)
    cantidad_descanso = tipos.get("descanso", 0)
    camino_principal = camino_mas_corto(adyacencias, estado.habitacion_inicio, estado.habitacion_salida)
    boss_en_camino = boss in camino_principal if boss is not None else False

    penalizacion_dura_conectividad = 0.0 if distancia_salida != inf else 1.0
    cantidad_grados_invalidos = sum(
        1
        for vecinos in adyacencias.values()
        if len(vecinos) < GRADO_MINIMO_EVALUACION or len(vecinos) > GRADO_MAXIMO_EVALUACION
    )
    secuencia_valida = (
        boss is not None
        and distancia_boss != inf
        and distancia_boss_a_salida != inf
        and distancia_salida > distancia_boss
        and boss_en_camino
    )
    penalizacion_dura_secuencia_boss_salida = 0.0 if secuencia_valida else 1.0
    penalizacion_dura_grados_habitaciones = cantidad_grados_invalidos / max(1, cantidad_habitaciones)
    penalizacion_dura_cantidad_habitaciones = penalizacion_rango(cantidad_habitaciones, 8, 20)
    penalizacion_dura_cantidad_tesoros = penalizacion_min_tesoros
    penalizacion_dura_cantidad_descanso = max(0.0, cantidad_descanso - 2) / 2.0
    penalizacion_dura_tesoros_bloqueados = tesoros_bloqueados / max(1, cantidad_tesoros)

    ideal_salida = min(distancia_salida_ideal, max(6, cantidad_habitaciones - 1))
    penalizacion_suave_salida_lejos = 1.0 if distancia_salida == inf else penalizacion_faltante_normalizada(distancia_salida, ideal_salida)
    penalizacion_suave_interes_tesoros = penalizacion_interes_tesoros(
        adyacencias=adyacencias,
        habitacion_inicio=estado.habitacion_inicio,
        habitacion_salida=estado.habitacion_salida,
        habitaciones_tesoro=habitaciones_tesoro,
        distancia_salida_ideal=ideal_salida,
    )
    penalizacion_suave_progresion_dificultad = penalizacion_progresion_dificultad(estado.habitaciones, distancias_desde_inicio)
    penalizacion_suave_salas_vacias = penalizacion_salas_vacias(estado.habitaciones)
    penalizacion_suave_proporcion_piso = penalizacion_rango(proporcion_actual_piso, 0.22, 0.50)
    penalizacion_suave_dispersion_cuadricula = penalizacion_dispersion_cuadricula(estado.habitaciones)
    penalizacion_suave_ocupacion_cuadricula = penalizacion_ocupacion_cuadricula(estado.habitaciones)
    penalizacion_suave_ramificacion_util = penalizacion_ramificacion_util(adyacencias, camino_principal)
    penalizacion_suave_lineas_excesivas = penalizacion_lineas_excesivas(estado.habitaciones)
    resumen_cuadricula = resumen_cuadricula_logica(estado.habitaciones)

    penalizaciones = {
        "conectividad_dura": penalizacion_dura_conectividad,
        "secuencia_boss_salida_dura": penalizacion_dura_secuencia_boss_salida,
        "grados_habitaciones_dura": penalizacion_dura_grados_habitaciones,
        "cantidad_habitaciones_dura": penalizacion_dura_cantidad_habitaciones,
        "cantidad_tesoros_dura": penalizacion_dura_cantidad_tesoros,
        "cantidad_descanso_dura": penalizacion_dura_cantidad_descanso,
        "tesoros_bloqueados_dura": penalizacion_dura_tesoros_bloqueados,
        "salida_lejos_suave": penalizacion_suave_salida_lejos,
        "interes_tesoros_suave": penalizacion_suave_interes_tesoros,
        "progresion_dificultad_suave": penalizacion_suave_progresion_dificultad,
        "salas_vacias_suave": penalizacion_suave_salas_vacias,
        "proporcion_piso_suave": penalizacion_suave_proporcion_piso,
        "dispersion_cuadricula_suave": penalizacion_suave_dispersion_cuadricula,
        "ocupacion_cuadricula_suave": penalizacion_suave_ocupacion_cuadricula,
        "ramificacion_util_suave": penalizacion_suave_ramificacion_util,
        "lineas_excesivas_suave": penalizacion_suave_lineas_excesivas,
    }

    terminos_ponderados = {
        "conectividad_dura": penalizaciones["conectividad_dura"] * pesos.conectividad_dura,
        "secuencia_boss_salida_dura": penalizaciones["secuencia_boss_salida_dura"] * pesos.secuencia_boss_salida_dura,
        "grados_habitaciones_dura": penalizaciones["grados_habitaciones_dura"] * pesos.grados_habitaciones_dura,
        "cantidad_habitaciones_dura": penalizaciones["cantidad_habitaciones_dura"] * pesos.cantidad_habitaciones_dura,
        "cantidad_tesoros_dura": penalizaciones["cantidad_tesoros_dura"] * pesos.cantidad_tesoros_dura,
        "cantidad_descanso_dura": penalizaciones["cantidad_descanso_dura"] * pesos.cantidad_descanso_dura,
        "tesoros_bloqueados_dura": penalizaciones["tesoros_bloqueados_dura"] * pesos.tesoros_bloqueados_dura,
        "salida_lejos_suave": penalizaciones["salida_lejos_suave"] * pesos.salida_lejos_suave,
        "interes_tesoros_suave": penalizaciones["interes_tesoros_suave"] * pesos.interes_tesoros_suave,
        "progresion_dificultad_suave": penalizaciones["progresion_dificultad_suave"] * pesos.progresion_dificultad_suave,
        "salas_vacias_suave": penalizaciones["salas_vacias_suave"] * pesos.salas_vacias_suave,
        "proporcion_piso_suave": penalizaciones["proporcion_piso_suave"] * pesos.proporcion_piso_suave,
        "dispersion_cuadricula_suave": penalizaciones["dispersion_cuadricula_suave"] * pesos.dispersion_cuadricula_suave,
        "ocupacion_cuadricula_suave": penalizaciones["ocupacion_cuadricula_suave"] * pesos.ocupacion_cuadricula_suave,
        "ramificacion_util_suave": penalizaciones["ramificacion_util_suave"] * pesos.ramificacion_util_suave,
        "lineas_excesivas_suave": penalizaciones["lineas_excesivas_suave"] * pesos.lineas_excesivas_suave,
    }

    return {
        "energia": sum(terminos_ponderados.values()),
        "factible": all(
            penalizaciones[clave] == 0.0
            for clave in (
                "conectividad_dura",
                "secuencia_boss_salida_dura",
                "grados_habitaciones_dura",
                "cantidad_habitaciones_dura",
                "cantidad_tesoros_dura",
                "cantidad_descanso_dura",
                "tesoros_bloqueados_dura",
            )
        ),
        "metricas": {
            "cantidad_habitaciones": cantidad_habitaciones,
            "cantidad_tesoros": cantidad_tesoros,
            "tesoros_minimos_requeridos": minimo_tesoros,
            "cantidad_descanso": cantidad_descanso,
            "cantidad_enemigos": estado.cantidad_enemigos,
            "distancia_boss": None if distancia_boss == inf else distancia_boss,
            "distancia_salida": None if distancia_salida == inf else distancia_salida,
            "distancia_boss_a_salida": None if distancia_boss_a_salida == inf else distancia_boss_a_salida,
            "cantidad_grados_invalidos": cantidad_grados_invalidos,
            "tesoros_bloqueados": tesoros_bloqueados,
            "proporcion_piso": proporcion_actual_piso,
            "boss_en_camino_principal": boss_en_camino,
            "filas_usadas": int(resumen_cuadricula["filas_usadas"]),
            "columnas_usadas": int(resumen_cuadricula["columnas_usadas"]),
            "alto_caja_logica": int(resumen_cuadricula["alto_caja"]),
            "ancho_caja_logica": int(resumen_cuadricula["ancho_caja"]),
            "area_caja_logica": int(resumen_cuadricula["area_caja"]),
            "densidad_caja_logica": resumen_cuadricula["densidad_caja"],
            "aspecto_caja_logica": resumen_cuadricula["aspecto_caja"],
            "habitaciones_fuera_camino_principal": max(0, cantidad_habitaciones - len(camino_principal)),
            "cantidad_bifurcaciones": sum(1 for vecinos in adyacencias.values() if len(vecinos) >= 3),
            "tipos_sala": dict(tipos),
        },
        "penalizaciones": penalizaciones,
        "terminos_ponderados": terminos_ponderados,
    }

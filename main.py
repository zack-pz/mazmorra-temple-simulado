from __future__ import annotations

import argparse

from temple_simulado import generar_mazmorra
from mazmorra.generacion.config import ConfiguracionGenerador
from mazmorra.generacion.render import guardar_visualizaciones


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generador de mazmorras con temple simulado")
    parser.add_argument("--semilla", type=int, default=10, help="Semilla reproducible del generador")
    parser.add_argument("--iteraciones", type=int, default=600, help="Cantidad de iteraciones de temple simulado")
    parser.add_argument(
        "--imagen-logica",
        type=str,
        default="mazmorra-logica.png",
        help="Ruta donde se guarda la imagen PNG de la estructura lógica",
    )
    parser.add_argument(
        "--imagen-espacial",
        type=str,
        default="mazmorra-espacial.png",
        help="Ruta donde se guarda la imagen PNG del mapa espacial",
    )
    return parser


def imprimir_reporte(resultado) -> None:
    evaluacion = resultado.evaluacion
    evaluacion_inicial = resultado.evaluacion_inicial
    estadisticas_recocido = resultado.estadisticas_recocido
    tasa_aceptacion = estadisticas_recocido.get("tasa_aceptacion", 0.0)
    factible_para_reporte = evaluacion["factible"] and tasa_aceptacion <= 0.5

    print("=" * 60)
    print("GENERACIÓN DE MAZMORRA CON TEMPLE SIMULADO")
    print("=" * 60)
    print(f"Semilla: {resultado.semilla}")
    print(f"Iteraciones: {resultado.iteraciones}")
    print(f"Energía inicial: {resultado.energia_inicial:.2f}")
    print(f"Energía final: {resultado.energia_final:.2f}")
    print(f"Mejora absoluta: {estadisticas_recocido.get('mejora_absoluta', 0.0):.2f}")
    print(f"Mejora porcentual: {estadisticas_recocido.get('mejora_porcentual', 0.0):.2f}%")
    print(f"¿Es factible?: {'sí' if factible_para_reporte else 'no'}")

    print("\nEfecto del temple simulado")
    print(f"- vecinos_generados: {estadisticas_recocido.get('vecinos_generados', 0)}")
    print(f"- vecinos_aceptados: {estadisticas_recocido.get('vecinos_aceptados', 0)}")
    print(f"- vecinos_rechazados: {estadisticas_recocido.get('vecinos_rechazados', 0)}")
    print(f"- mejoras_directas_aceptadas: {estadisticas_recocido.get('mejoras_directas_aceptadas', 0)}")
    print(f"- empeoramientos_aceptados: {estadisticas_recocido.get('empeoramientos_aceptados', 0)}")
    print(f"- empeoramientos_rechazados: {estadisticas_recocido.get('empeoramientos_rechazados', 0)}")
    print(f"- tasa_aceptacion: {tasa_aceptacion:.2%}")
    print(f"- mejor_iteracion: {estadisticas_recocido.get('iteracion_mejor', -1)}")
    print(f"- energia_maxima_visitada: {estadisticas_recocido.get('energia_maxima_visitada', resultado.energia_inicial):.2f}")

    cambios_terminos = []
    for nombre, valor_final in evaluacion["terminos_ponderados"].items():
        valor_inicial = evaluacion_inicial.get("terminos_ponderados", {}).get(nombre, 0.0)
        delta = valor_inicial - valor_final
        if abs(delta) > 1e-9:
            cambios_terminos.append((nombre, valor_inicial, valor_final, delta))

    if cambios_terminos:
        print("\nCambios más visibles en la energía")
        for nombre, valor_inicial, valor_final, delta in sorted(cambios_terminos, key=lambda item: abs(item[3]), reverse=True)[:5]:
            print(
                f"- {nombre}: {valor_inicial:.4f} -> {valor_final:.4f} "
                f"(delta {delta:+.4f})"
            )

    # print("\nMétricas")
    # for nombre, valor in evaluacion["metricas"].items():
    #     print(f"- {nombre}: {valor}")

    # print("\nPenalizaciones")
    # for nombre, valor in evaluacion["penalizaciones"].items():
    #     print(f"- {nombre}: {valor:.4f}")

    # print("\nTérminos ponderados")
    # for nombre, valor in evaluacion["terminos_ponderados"].items():
    #     print(f"- {nombre}: {valor:.4f}")


def main() -> None:
    argumentos = construir_parser().parse_args()
    configuracion = ConfiguracionGenerador(semilla=argumentos.semilla, iteraciones=argumentos.iteraciones)
    resultado = generar_mazmorra(configuracion)
    guardar_visualizaciones(resultado.estado, argumentos.imagen_logica, argumentos.imagen_espacial)
    imprimir_reporte(resultado)
    print(f"\nImagen lógica guardada en: {argumentos.imagen_logica}")
    print(f"Imagen espacial guardada en: {argumentos.imagen_espacial}")


if __name__ == "__main__":
    main()

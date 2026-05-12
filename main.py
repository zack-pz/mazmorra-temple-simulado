from __future__ import annotations

import argparse

from mazmorra.generator import ConfiguracionGenerador, generar_mazmorra, guardar_visualizacion


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generador de mazmorras con temple simulado")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla reproducible del generador")
    parser.add_argument("--iteraciones", type=int, default=600, help="Cantidad de iteraciones de temple simulado")
    parser.add_argument(
        "--imagen",
        type=str,
        default="mazmorra-generada.png",
        help="Ruta donde se guarda la visualización PNG",
    )
    return parser


def imprimir_reporte(resultado) -> None:
    evaluacion = resultado.evaluacion

    print("=" * 60)
    print("GENERACIÓN DE MAZMORRA CON TEMPLE SIMULADO")
    print("=" * 60)
    print(f"Semilla: {resultado.semilla}")
    print(f"Iteraciones: {resultado.iteraciones}")
    print(f"Energía inicial: {resultado.energia_inicial:.2f}")
    print(f"Energía final: {resultado.energia_final:.2f}")
    print(f"¿Es factible?: {'sí' if evaluacion['factible'] else 'no'}")

    print("\nMétricas")
    for nombre, valor in evaluacion["metricas"].items():
        print(f"- {nombre}: {valor}")

    print("\nPenalizaciones")
    for nombre, valor in evaluacion["penalizaciones"].items():
        print(f"- {nombre}: {valor:.4f}")

    print("\nTérminos ponderados")
    for nombre, valor in evaluacion["terminos_ponderados"].items():
        print(f"- {nombre}: {valor:.4f}")


def main() -> None:
    argumentos = construir_parser().parse_args()
    configuracion = ConfiguracionGenerador(semilla=argumentos.semilla, iteraciones=argumentos.iteraciones)
    resultado = generar_mazmorra(configuracion)
    guardar_visualizacion(resultado.estado, argumentos.imagen)
    imprimir_reporte(resultado)
    print(f"\nImagen guardada en: {argumentos.imagen}")


if __name__ == "__main__":
    main()

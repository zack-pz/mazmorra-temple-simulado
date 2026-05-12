from __future__ import annotations

from mazmorra.objective import EstadoMazmorra, evaluar_mazmorra
from mazmorra import mazmorra_estatica


def cargar_modulo_prototipo():
    return mazmorra_estatica


def construir_estado_desde_prototipo(modulo_prototipo) -> EstadoMazmorra:
    grid = modulo_prototipo.build_dungeon()

    return EstadoMazmorra(
        habitaciones=modulo_prototipo.ROOMS,
        conexiones=modulo_prototipo.CONNECTIONS,
        habitacion_inicio="entrada",
        habitacion_salida="boss",
        habitaciones_tesoro=["tesoro"],
        cantidad_enemigos=8,
        grid=grid,
    )


def imprimir_reporte(resultado: dict) -> None:
    print("=" * 50)
    print("EVALUACIÓN DE LA MAZMORRA")
    print("=" * 50)
    print(f"Energía total: {resultado['energia']:.2f}")
    print(f"¿Es factible?: {'sí' if resultado['factible'] else 'no'}")

    print("\nMétricas")
    for nombre, valor in resultado["metricas"].items():
        print(f"- {nombre}: {valor}")

    print("\nPenalizaciones")
    for nombre, valor in resultado["penalizaciones"].items():
        print(f"- {nombre}: {valor:.4f}")

    print("\nTérminos ponderados")
    for nombre, valor in resultado["terminos_ponderados"].items():
        print(f"- {nombre}: {valor:.4f}")


def main() -> None:
    modulo_prototipo = cargar_modulo_prototipo()
    estado = construir_estado_desde_prototipo(modulo_prototipo)
    resultado = evaluar_mazmorra(estado)
    imprimir_reporte(resultado)


if __name__ == "__main__":
    main()

__all__ = [
    "ConfiguracionGenerador",
    "ResultadoGeneracion",
    "EstadoMazmorra",
    "PesosObjetivo",
    "evaluar_mazmorra",
    "generar_mazmorra",
    "guardar_visualizaciones",
    "minimos_tesoro_por_tamano",
]


def __getattr__(nombre: str):
    if nombre in {"EstadoMazmorra", "PesosObjetivo", "evaluar_mazmorra", "minimos_tesoro_por_tamano"}:
        from mazmorra.evaluacion import EstadoMazmorra, PesosObjetivo, evaluar_mazmorra, minimos_tesoro_por_tamano

        valores = {
            "EstadoMazmorra": EstadoMazmorra,
            "PesosObjetivo": PesosObjetivo,
            "evaluar_mazmorra": evaluar_mazmorra,
            "minimos_tesoro_por_tamano": minimos_tesoro_por_tamano,
        }
        return valores[nombre]

    if nombre in {"ConfiguracionGenerador", "ResultadoGeneracion", "generar_mazmorra", "guardar_visualizaciones"}:
        from mazmorra.generacion import ConfiguracionGenerador, ResultadoGeneracion, generar_mazmorra, guardar_visualizaciones

        valores = {
            "ConfiguracionGenerador": ConfiguracionGenerador,
            "ResultadoGeneracion": ResultadoGeneracion,
            "generar_mazmorra": generar_mazmorra,
            "guardar_visualizaciones": guardar_visualizaciones,
        }
        return valores[nombre]

    raise AttributeError(f"module 'mazmorra' has no attribute {nombre!r}")

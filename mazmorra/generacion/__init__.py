__all__ = [
    "ConfiguracionGenerador",
    "ResultadoGeneracion",
    "generar_mazmorra",
    "guardar_visualizaciones",
]


def __getattr__(nombre: str):
    if nombre in {"ConfiguracionGenerador", "ResultadoGeneracion"}:
        from mazmorra.generacion.config import ConfiguracionGenerador, ResultadoGeneracion

        valores = {
            "ConfiguracionGenerador": ConfiguracionGenerador,
            "ResultadoGeneracion": ResultadoGeneracion,
        }
        return valores[nombre]

    if nombre == "generar_mazmorra":
        from mazmorra.generacion.recocido import generar_mazmorra

        return generar_mazmorra

    if nombre == "guardar_visualizaciones":
        from mazmorra.generacion.render import guardar_visualizaciones

        return guardar_visualizaciones

    raise AttributeError(f"module 'mazmorra.generacion' has no attribute {nombre!r}")

# Generador de mazmorras con temple simulado

Este proyecto genera **mazmorras 2D** usando **temple simulado**.

La idea principal es empezar con una mazmorra inicial válida, hacerle cambios pequeños y quedarse con la mejor versión encontrada según una **función de energía**.

## Qué hace el proyecto

El generador construye una mazmorra con:

- habitaciones como `inicio`, `combate`, `tesoro`, `descanso`, `boss` y `salida`
- conexiones entre habitaciones
- una distribución lógica sobre una cuadrícula de `6 x 6`
- una visualización final en dos imágenes

Al terminar, el programa muestra un reporte en consola y guarda:

- `mazmorra-logica.png`
- `mazmorra-espacial.png`

## Cómo funciona

El algoritmo sigue esta idea general:

1. crea una mazmorra inicial válida
2. evalúa su energía
3. genera una variante cercana por mutación
4. si la variante mejora, la acepta
5. si empeora, a veces igual la acepta según la temperatura
6. repite el proceso varias iteraciones
7. devuelve la mejor mazmorra encontrada

En este proyecto, **menor energía = mejor solución**.

## Estructura básica

- `main.py`: punto de entrada del programa
- `temple_simulado.py`: núcleo del algoritmo de temple simulado
- `mazmorra/generacion/`: creación inicial, mutaciones y render
- `mazmorra/evaluacion/`: función de energía y métricas

## Requisitos

Dependencias principales:

- `numpy`
- `matplotlib`

## Cómo ejecutarlo

Desde la raíz del proyecto:

```bash
uv venv .venv
uv pip install -r requirements.txt
uv run main.py --iteraciones 300
```

Si querés fijar explícitamente la semilla:

```bash
uv run main.py --semilla 10 --iteraciones 300
```

## Parámetros más importantes

- `--semilla`: controla la reproducibilidad de la generación
- `--iteraciones`: cantidad de iteraciones del temple simulado
- `--imagen-logica`: nombre o ruta de la imagen lógica de salida
- `--imagen-espacial`: nombre o ruta de la imagen espacial de salida

## Salida esperada

El programa imprime un resumen como este:

- semilla usada
- cantidad de iteraciones
- energía inicial y final
- mejora lograda
- cantidad de vecinos aceptados y rechazados
- mejor iteración encontrada

Además, guarda las imágenes de la mazmorra generada.

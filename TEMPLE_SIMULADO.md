# Cómo funciona el temple simulado en este proyecto

Este archivo explica **solo el funcionamiento del temple simulado** usado por el generador.  
No describe cómo se construye el grafo ni cómo se renderiza la mazmorra.

## Idea central

El temple simulado es una técnica de optimización que busca una buena solución sin quedarse atrapada demasiado rápido en óptimos locales.

En este proyecto, la idea es:

1. empezar con una solución válida inicial,
2. generar pequeñas variaciones de esa solución,
3. medir qué tan buena es cada variante con una **energía**,
4. aceptar siempre mejoras,
5. aceptar a veces empeoramientos cuando la temperatura todavía es alta,
6. enfriar progresivamente el sistema hasta quedarse con la mejor solución encontrada.

---

## Dónde está implementado

La implementación principal está en:

- `temple_simulado.py`

Ese archivo de la raíz concentra la orquestación del algoritmo y delega el trabajo auxiliar al paquete `mazmorra/`.

Las funciones clave son:

- `generar_mazmorra(...)`
- `interpolar_temperatura(...)`
- `aceptar_vecino(...)`

---

## Flujo general del algoritmo

## 1. Crear la solución inicial

Primero se genera una mazmorra inicial y se evalúa su energía:

```python
actual = crear_mazmorra_inicial(aleatorio, configuracion.semilla)
estado_actual = materializar_estado(actual)
evaluacion_actual = evaluar_mazmorra(estado_actual)
```

### Qué significa esto conceptualmente

- `actual`: solución actual que el algoritmo está explorando.
- `estado_actual`: representación materializada que puede evaluarse.
- `evaluacion_actual["energia"]`: costo de la solución actual.

En este proyecto, **menor energía = mejor solución**.

---

## 2. Guardar la mejor solución encontrada

Antes de empezar a mutar, el algoritmo guarda una copia de la mejor solución conocida:

```python
mejor = deepcopy(actual)
mejor_estado = estado_actual
mejor_evaluacion = evaluacion_actual
energia_inicial = evaluacion_actual["energia"]
```

Esto es importante porque el temple simulado puede aceptar soluciones peores temporalmente.  
Por eso hay que separar:

- **solución actual**
- **mejor solución histórica**

Si no hacés esa distinción, podés terminar peor de lo que ya habías encontrado.

---

## 3. Recorrer iteraciones

El bucle principal es este:

```python
for iteracion in range(configuracion.iteraciones):
```

Cada iteración representa un intento de mover la solución actual hacia otra vecina.

---

## 4. Calcular la temperatura actual

En cada iteración se calcula una temperatura:

```python
temperatura = interpolar_temperatura(
    paso=iteracion,
    total_pasos=configuracion.iteraciones,
    temperatura_inicial=configuracion.temperatura_inicial,
    temperatura_final=configuracion.temperatura_final,
)
```

La función usada es:

```python
def interpolar_temperatura(...):
    if total_pasos <= 1:
        return temperatura_final

    proporcion = paso / float(total_pasos - 1)
    return temperatura_inicial * ((temperatura_final / temperatura_inicial) ** proporcion)
```

### Qué significa esto conceptualmente

- al principio la temperatura es alta,
- luego baja gradualmente,
- cuanto más alta la temperatura, más tolerancia hay para aceptar soluciones peores,
- cuanto más baja la temperatura, más conservador se vuelve el algoritmo.

Este proyecto usa un **enfriamiento geométrico/interpolado en escala exponencial**.

---

## 5. Generar un vecino

Después se crea una variante de la solución actual:

```python
vecino = mutar_mazmorra(actual, aleatorio)
estado_vecino = materializar_estado(vecino)
evaluacion_vecino = evaluar_mazmorra(estado_vecino)
```

### Qué significa esto conceptualmente

Un **vecino** es una solución parecida a la actual, pero con un cambio pequeño.

Eso es clave. Temple simulado NO funciona comparando soluciones totalmente aleatorias sin relación entre sí.  
Funciona haciendo **exploración local controlada**.

---

## 6. Decidir si el vecino se acepta

Esta es la parte más importante del algoritmo:

```python
if aceptar_vecino(
    energia_actual=evaluacion_actual["energia"],
    energia_vecino=evaluacion_vecino["energia"],
    temperatura=temperatura,
    aleatorio=aleatorio,
):
    actual = vecino
    estado_actual = estado_vecino
    evaluacion_actual = evaluacion_vecino
```

La regla de aceptación es:

```python
def aceptar_vecino(...):
    if energia_vecino <= energia_actual:
        return True

    if temperatura <= 0:
        return False

    probabilidad = exp(-(energia_vecino - energia_actual) / temperatura)
    return aleatorio.random() < probabilidad
```

### Interpretación

#### Caso A — el vecino es mejor

Si la energía del vecino es menor o igual:

```python
energia_vecino <= energia_actual
```

entonces se acepta siempre.

#### Caso B — el vecino es peor

Si el vecino empeora la energía, todavía puede aceptarse con cierta probabilidad:

```python
exp(-(energia_vecino - energia_actual) / temperatura)
```

### Por qué esto es importante

Acá está la esencia del temple simulado.

Si solo aceptaras mejoras, el algoritmo sería un ascenso/descenso local codicioso.  
Eso se queda atrapado fácil en óptimos locales.

En cambio, aceptar a veces soluciones peores permite:

- salir de valles locales,
- explorar configuraciones nuevas,
- no congelarse demasiado pronto.

---

## 7. Actualizar la mejor solución histórica

Aunque el algoritmo acepte algo peor temporalmente, sigue guardando la mejor solución global que vio hasta ese momento:

```python
if evaluacion_actual["energia"] < mejor_evaluacion["energia"]:
    mejor = deepcopy(actual)
    mejor_estado = estado_actual
    mejor_evaluacion = evaluacion_actual
```

Esto asegura que el resultado final no sea simplemente la última solución visitada, sino la mejor encontrada durante toda la búsqueda.

---

## 8. Devolver el mejor resultado

Al terminar las iteraciones, el algoritmo devuelve la mejor solución guardada:

```python
return ResultadoGeneracion(
    estado=mejor_estado,
    evaluacion=mejor_evaluacion,
    semilla=configuracion.semilla,
    iteraciones=configuracion.iteraciones,
    energia_inicial=energia_inicial,
    energia_final=mejor_evaluacion["energia"],
)
```

Eso permite comparar:

- energía inicial
- energía final
- cantidad de iteraciones usadas

---

## Resumen conceptual en una frase

El algoritmo parte de una solución válida, genera vecinos por mutación, evalúa su energía, acepta siempre mejoras y acepta a veces empeoramientos según la temperatura, mientras conserva aparte la mejor solución global encontrada.

---

## Pseudocódigo simplificado

```text
crear solución inicial
evaluar energía inicial
guardar como mejor solución conocida

para cada iteración:
    calcular temperatura actual
    generar un vecino
    evaluar energía del vecino

    si el vecino es mejor:
        aceptarlo
    si el vecino es peor:
        aceptarlo con una probabilidad dependiente de la temperatura

    si la solución actual supera a la mejor histórica:
        guardar nueva mejor solución

devolver la mejor solución encontrada
```

---

## Parámetros que controlan el comportamiento

Los parámetros relevantes están en `mazmorra/generacion/config.py`.

Los más importantes son:

- `iteraciones`
- `temperatura_inicial`
- `temperatura_final`
- `semilla`

### Efecto de cada uno

- **más iteraciones**: más tiempo para explorar,
- **temperatura inicial más alta**: más libertad al comienzo,
- **temperatura final más baja**: más rigidez al final,
- **semilla fija**: reproducibilidad de la secuencia aleatoria.

---

## Qué NO hay que confundir

### Temple simulado no es:

- crear una solución aleatoria y listo,
- probar muchas soluciones independientes sin relación,
- quedarse siempre con la mejor inmediata,
- renderizar imágenes,
- construir el grafo en sí mismo.

### Temple simulado sí es:

- una estrategia de búsqueda,
- una política de aceptación de vecinos,
- un equilibrio entre exploración y explotación,
- un proceso que enfría gradualmente el sistema.

---

## Archivos relacionados si querés seguir leyendo

- `temple_simulado.py` — núcleo del temple simulado
- `mazmorra/generacion/mutaciones.py` — cómo se generan vecinos
- `mazmorra/evaluacion/evaluador.py` — cómo se calcula la energía
- `mazmorra/generacion/config.py` — parámetros del algoritmo

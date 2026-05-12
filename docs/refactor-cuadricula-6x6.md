# Plan de refactor hacia cuadrícula lógica 6x6

## Objetivo

Reducir la linealidad del generador introduciendo una **cuadrícula lógica de 6 columnas x 6 filas** como restricción espacial del crecimiento de habitaciones, sin mezclar esa lógica con el render final del grid.

## Diagnóstico actual

- La **topología** se genera como `camino principal + ramas`.
- El **layout** actual usa profundidad BFS para dibujar columnas, lo que exagera visualmente la linealidad.
- No existe todavía una posición lógica discreta por habitación; solo hay coordenadas de render (`x`, `y`, `w`, `h`).

## Principio arquitectónico

Separar tres niveles:

1. **Topología**: qué habitaciones existen y cómo se conectan.
2. **Posición lógica**: en qué celda `(fila, columna)` de la cuadrícula 6x6 cae cada habitación.
3. **Render espacial**: cómo esa celda se transforma en tiles y pasillos del mapa final.

## Fase 1 — Introducir cuadrícula lógica 6x6

### Meta

Agregar a cada habitación una posición lógica dentro de una malla de 6x6.

### Trabajo

- Agregar `fila` y `columna` o `celda=(fila, columna)` al modelo de habitación.
- Definir ocupación máxima de 36 celdas.
- Validar que no existan dos habitaciones en la misma celda.
- Mantener por ahora la topología actual, pero proyectarla sobre la cuadrícula.

### Riesgo

Medio. Cambia el modelo de datos del generador, pero todavía no toca fuerte la función objetivo.

## Fase 2 — Derivar render desde la cuadrícula lógica

### Meta

Eliminar el layout basado en profundidad BFS como fuente primaria de posiciones visuales.

### Trabajo

- Reemplazar `asignar_layout(...)` por un cálculo derivado desde la celda lógica.
- Mapear cada celda de la cuadrícula a una región del grid final.
- Tallar pasillos entre celdas vecinas conectadas.

### Riesgo

Medio-bajo. Simplifica el render y reduce acoplamiento.

## Fase 3 — Restringir grados a 1..4

### Meta

Cada habitación debe tener entre 1 y 4 conexiones.

### Trabajo

- Agregar validación dura por grado mínimo y máximo.
- Ajustar generación inicial para no crear nodos con grado inválido.
- Ajustar mutaciones estructurales para preservar esa restricción.
- Mantener ramificación moderada: permitir bifurcaciones útiles sin volver al grafo estrella ni colapsar todo a un pasillo.

### Riesgo

Medio. Impacta generación y mutaciones, pero mantiene alineado el objetivo de reducir linealidad sin destruir la variedad topológica.

## Fase 4 — Mejorar mutaciones estructurales

### Meta

Dejar atrás la mutación centrada solo en hojas.

### Trabajo

- Crear operadores como:
  - mover habitación a celda libre
  - reconectar respetando vecindad ortogonal
  - expandir rama a celda libre
  - podar o relocalizar subrama
- Mantener conectividad total y secuencia `inicio -> boss -> salida`.

### Riesgo

Medio-alto. Es el corazón del cambio topológico.

## Fase 5 — Afinar función objetivo

### Meta

Premiar estructuras menos lineales y mejor distribuidas.

### Trabajo

- Agregar métricas suaves de:
  - dispersión en cuadrícula
  - ocupación razonable de la 6x6
  - ramificación útil
  - penalización por apelotonamiento o líneas excesivas

### Estado aplicado

- Se incorporaron penalizaciones suaves específicas de cuadrícula lógica en `mazmorra/evaluacion/penalizaciones.py`.
- La evaluación ahora considera:
  - dispersión por caja lógica y uso de ejes
  - densidad de ocupación dentro de la caja lógica
  - proporción de habitaciones fuera del camino principal y bifurcaciones de grado alto (3 o 4)
  - elongación excesiva de la caja lógica como proxy de linealidad
- Se exponen métricas adicionales en el reporte para facilitar tuning posterior de pesos.

### Riesgo

Bajo a medio. Depende del tuning de pesos.

## Recomendación de implementación

No mezclar todas las fases en un solo commit grande. La secuencia recomendada es:

1. **Modelo lógico 6x6**
2. **Render derivado desde la cuadrícula**
3. **Restricción 1..3 conexiones**
4. **Nuevas mutaciones**
5. **Ajuste fino de la evaluación**

## Beneficio esperado

- Menos sensación de “línea recta con ramas”.
- Mejor separación entre concepto lógico y visualización.
- Base mucho más sólida para seguir evolucionando el generador.

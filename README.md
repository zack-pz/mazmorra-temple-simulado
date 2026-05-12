# Prototipo estático de mazmorra híbrida

Este directorio contiene un prototipo inicial para un **generador de mazmorras** pensado como base conceptual para aplicar **temple simulado** más adelante.

## Idea del prototipo

Se usa un enfoque **híbrido**:

1. **Grafo lógico**: representa habitaciones importantes y sus conexiones.
2. **Grid espacial**: representa cómo esa estructura se traduce a un mapa jugable con paredes, pisos y salas.

La intención es separar la **topología** de la mazmorra de su **distribución espacial**. Eso después te permite optimizar cosas como:

- conectividad
- distancia entre inicio y boss
- profundidad de exploración
- número de bifurcaciones
- ubicación de recompensas

## Archivo principal

- `mazmorra/mazmorra-estatica.py`

## Cómo ejecutar

Desde la raíz del proyecto:

```bash
python mazmorra/mazmorra-estatica.py
```

## Qué genera

El script muestra y guarda una figura con dos paneles:

- **izquierda:** estructura lógica de la mazmorra como grafo
- **derecha:** representación espacial sobre grid

También guarda la imagen en:

- `mazmorra/mazmorra-estatica.png`

## Qué representa cada color en el grid

- negro: pared
- gris claro: piso transitable
- verde: punto de inicio
- azul: salida
- amarillo/naranja: tesoro
- rojo: sala del boss

## Siguiente paso natural

El siguiente paso sería definir una **función de energía** para temple simulado, por ejemplo penalizando:

- salas desconectadas
- boss demasiado cerca del inicio
- pasillos excesivamente largos
- poca ramificación
- tesoro en zonas triviales

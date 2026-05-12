from __future__ import annotations

from collections import Counter, deque
from typing import Iterable


def construir_adyacencias(conexiones: Iterable[tuple[str, str]]) -> dict[str, set[str]]:
    adyacencias: dict[str, set[str]] = {}
    for origen, destino in conexiones:
        adyacencias.setdefault(origen, set()).add(destino)
        adyacencias.setdefault(destino, set()).add(origen)
    return adyacencias


def distancias_bfs(adyacencias: dict[str, set[str]], inicio: str) -> dict[str, int]:
    if inicio not in adyacencias:
        return {inicio: 0}

    distancias = {inicio: 0}
    cola = deque([inicio])

    while cola:
        actual = cola.popleft()
        for vecino in adyacencias[actual]:
            if vecino in distancias:
                continue
            distancias[vecino] = distancias[actual] + 1
            cola.append(vecino)

    return distancias


def camino_mas_corto(adyacencias: dict[str, set[str]], inicio: str, meta: str) -> list[str]:
    if inicio == meta:
        return [inicio]
    if inicio not in adyacencias or meta not in adyacencias:
        return []

    padres: dict[str, str | None] = {inicio: None}
    cola = deque([inicio])

    while cola:
        actual = cola.popleft()
        for vecino in adyacencias[actual]:
            if vecino in padres:
                continue
            padres[vecino] = actual
            if vecino == meta:
                camino = [meta]
                cursor = meta
                while padres[cursor] is not None:
                    cursor = padres[cursor]
                    camino.append(cursor)
                camino.reverse()
                return camino
            cola.append(vecino)

    return []


def tipo_habitacion(habitacion: dict) -> str:
    return habitacion.get("tipo", "combate")


def contar_tipos(habitaciones: dict[str, dict]) -> Counter:
    return Counter(tipo_habitacion(habitacion) for habitacion in habitaciones.values())

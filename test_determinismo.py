from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


CODIGO_FINGERPRINT = """
from temple_simulado import generar_mazmorra
from mazmorra.generacion.config import ConfiguracionGenerador
import json

resultado = generar_mazmorra(ConfiguracionGenerador(semilla=42, iteraciones={iteraciones}))
estado = resultado.estado
fingerprint = {{
    "energia_inicial": resultado.evaluacion_inicial["energia"],
    "energia_final": resultado.evaluacion["energia"],
    "habitaciones": sorted(
        (
            nombre,
            habitacion["tipo"],
            habitacion.get("enemigos", 0),
            habitacion.get("cofres", 0),
            habitacion.get("fila"),
            habitacion.get("columna"),
            habitacion.get("w"),
            habitacion.get("h"),
        )
        for nombre, habitacion in estado.habitaciones.items()
    ),
    "conexiones": sorted(tuple(sorted(conexion)) for conexion in estado.conexiones),
}}
print(json.dumps(fingerprint, sort_keys=True))
""".strip()


class TestDeterminismoSemilla(unittest.TestCase):
    raiz_proyecto = Path(__file__).resolve().parent

    def ejecutar_fingerprint(self, hash_seed: int, iteraciones: int) -> dict:
        entorno = dict(os.environ)
        entorno["PYTHONHASHSEED"] = str(hash_seed)
        salida = subprocess.run(
            [sys.executable, "-c", CODIGO_FINGERPRINT.format(iteraciones=iteraciones)],
            cwd=self.raiz_proyecto,
            env=entorno,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(salida.stdout)

    def assert_reproducible_entre_hash_seeds(self, iteraciones: int) -> None:
        baseline = self.ejecutar_fingerprint(hash_seed=0, iteraciones=iteraciones)

        for hash_seed in (1, 2, 3):
            with self.subTest(iteraciones=iteraciones, pyhash=hash_seed):
                actual = self.ejecutar_fingerprint(hash_seed=hash_seed, iteraciones=iteraciones)
                self.assertEqual(actual, baseline)

    def test_generacion_inicial_es_reproducible_entre_procesos(self) -> None:
        self.assert_reproducible_entre_hash_seeds(iteraciones=0)

    def test_recocido_largo_es_reproducible_entre_procesos(self) -> None:
        self.assert_reproducible_entre_hash_seeds(iteraciones=200)


if __name__ == "__main__":
    unittest.main()

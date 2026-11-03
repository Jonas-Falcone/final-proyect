import sqlite3
import unittest

from planeta.codigos import ALFABETO_SIN_CONFUSIONES, LARGO_DEL_CODIGO
from planeta.cuestionario import codificar_respuestas
from planeta.repositorio import RepositorioHuella

RESPUESTAS = codificar_respuestas("CCDCCCCDCC")


class PruebasDelRepositorio(unittest.TestCase):
    def setUp(self):
        self.repositorio = RepositorioHuella(sqlite3.connect(":memory:"))

    def test_crea_cuentas_con_codigos_validos_y_distintos(self):
        codigos = {self.repositorio.crear_cuenta() for _ in range(200)}
        self.assertEqual(len(codigos), 200)
        for codigo in codigos:
            self.assertEqual(len(codigo), LARGO_DEL_CODIGO)
            self.assertLessEqual(set(codigo), set(ALFABETO_SIN_CONFUSIONES))

    def test_el_historial_guarda_los_intentos_en_orden(self):
        cuenta = self.repositorio.crear_cuenta()
        self.assertEqual(self.repositorio.historial(cuenta), [])
        self.repositorio.guardar_intento(RESPUESTAS, 6, cuenta)
        self.repositorio.guardar_intento(codificar_respuestas("BBBBBBBBBB"), 3, cuenta)
        self.assertEqual([i.nivel for i in self.repositorio.historial(cuenta)], [6, 3])
        self.assertEqual(self.repositorio.historial("NOEXISTE"), [])

    def test_un_intento_sin_confirmar_no_es_ejemplo(self):
        cuenta = self.repositorio.crear_cuenta()
        antes = len(self.repositorio.cargar_ejemplos())
        id_del_intento = self.repositorio.guardar_intento(RESPUESTAS, 6, cuenta)
        self.assertEqual(len(self.repositorio.cargar_ejemplos()), antes)
        self.repositorio.confirmar_intento(id_del_intento, 7)
        ejemplos = self.repositorio.cargar_ejemplos()
        self.assertEqual(len(ejemplos), antes + 1)
        nuevo = ejemplos[-1]
        self.assertEqual((nuevo.nivel, nuevo.respuestas, nuevo.es_de_persona_real), (7, RESPUESTAS, True))

    def test_ignora_filas_con_otra_cantidad_de_preguntas(self):
        self.repositorio._conexion.execute(
            "INSERT INTO sesiones (respuestas, nivel_bot, nivel_final, confirmado, cuenta) "
            "VALUES ('ABC', 1, 1, 1, 'XXXXXXXX')"
        )
        self.assertEqual(self.repositorio.historial("XXXXXXXX"), [])
        self.assertFalse(any(len(e.respuestas) == 3 for e in self.repositorio.cargar_ejemplos()))

    def test_actualiza_una_base_de_la_version_anterior(self):
        conexion = sqlite3.connect(":memory:")
        conexion.execute(
            "CREATE TABLE sesiones (id INTEGER PRIMARY KEY AUTOINCREMENT, respuestas TEXT NOT NULL, "
            "nivel_bot INTEGER NOT NULL, nivel_final INTEGER, confirmado INTEGER NOT NULL DEFAULT 0, "
            "fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        conexion.execute(
            "INSERT INTO sesiones (respuestas, nivel_bot, nivel_final, confirmado) "
            "VALUES ('CCCCCCCCCC', 5, 5, 1)"
        )
        repositorio = RepositorioHuella(conexion)
        self.assertEqual(sum(e.es_de_persona_real for e in repositorio.cargar_ejemplos()), 1)
        cuenta = repositorio.crear_cuenta()
        repositorio.guardar_intento(RESPUESTAS, 4, cuenta)
        self.assertEqual(len(repositorio.historial(cuenta)), 1)


if __name__ == "__main__":
    unittest.main()

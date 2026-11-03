import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from planeta import configuracion
from planeta.codigos import formatear_codigo, generar_codigo, limpiar_codigo
from planeta.formato import barra_de_progreso, emoji_bandera, formatear_numero, normalizar


class PruebasDeFormato(unittest.TestCase):
    def test_normalizar_quita_tildes_y_mayusculas(self):
        self.assertEqual(normalizar("  Perú "), "peru")

    def test_numeros_con_formato_espanol(self):
        self.assertEqual(formatear_numero(3.74, 2), "3,74")
        self.assertEqual(formatear_numero(1234567, 0), "1.234.567")
        self.assertEqual(formatear_numero(0.5), "0,5")

    def test_bandera_y_barra(self):
        self.assertEqual(emoji_bandera("AR"), "🇦🇷")
        self.assertEqual(barra_de_progreso(30), "▰▰▰▱▱▱▱▱▱▱")


class PruebasDeCodigos(unittest.TestCase):
    def test_el_codigo_se_puede_escribir_de_muchas_formas(self):
        codigo = generar_codigo()
        for variante in (formatear_codigo(codigo), formatear_codigo(codigo).lower(), f" {codigo} "):
            self.assertEqual(limpiar_codigo(variante), codigo)

    def test_formato_con_guion_en_el_medio(self):
        self.assertEqual(formatear_codigo("K7M2QX9P"), "K7M2-QX9P")


class PruebasDeConfiguracion(unittest.TestCase):
    def test_sin_token_devuelve_nada(self):
        with tempfile.TemporaryDirectory() as carpeta, patch.dict(os.environ, {}, clear=True):
            with patch.object(configuracion, "RUTA_ARCHIVO_TOKEN", Path(carpeta) / "token.txt"):
                self.assertIsNone(configuracion.leer_token())

    def test_lee_el_token_del_archivo_aunque_tenga_comillas_y_espacios(self):
        with tempfile.TemporaryDirectory() as carpeta, patch.dict(os.environ, {}, clear=True):
            ruta = Path(carpeta) / "token.txt"
            ruta.write_text('  "abc.DEF-123"  \n', encoding="utf-8")
            with patch.object(configuracion, "RUTA_ARCHIVO_TOKEN", ruta):
                self.assertEqual(configuracion.leer_token(), "abc.DEF-123")

    def test_la_variable_de_entorno_tiene_prioridad(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "token.txt"
            ruta.write_text("del-archivo", encoding="utf-8")
            with patch.dict(os.environ, {"DISCORD_TOKEN": " 'del-entorno' "}):
                with patch.object(configuracion, "RUTA_ARCHIVO_TOKEN", ruta):
                    self.assertEqual(configuracion.leer_token(), "del-entorno")

    def test_id_de_servidor(self):
        with patch.dict(os.environ, {"GUILD_ID": "12345"}):
            self.assertEqual(configuracion.leer_id_servidor(), 12345)
        with patch.dict(os.environ, {"GUILD_ID": "no-es-un-numero"}):
            self.assertIsNone(configuracion.leer_id_servidor())
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(configuracion.leer_id_servidor())


if __name__ == "__main__":
    unittest.main()

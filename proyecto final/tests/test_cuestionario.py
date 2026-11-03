import unittest
from unittest.mock import patch

from planeta.contenido import EJEMPLOS_INICIALES, PREGUNTAS
from planeta.cuestionario import (
    Ejemplo,
    Intento,
    calcular_nivel,
    codificar_respuestas,
    decodificar_respuestas,
    ejemplos_iniciales,
    elegir_preguntas_a_mejorar,
    medir_progreso,
    validar_contenido,
)
from planeta.errores import ErrorDeConfiguracion


class PruebasDelNivel(unittest.TestCase):
    def setUp(self):
        self.ejemplos = ejemplos_iniciales()

    def test_cada_ejemplo_inicial_cae_en_su_propio_nivel(self):
        for nivel, lista in EJEMPLOS_INICIALES.items():
            for letras in lista:
                with self.subTest(nivel=nivel, ejemplo=letras):
                    self.assertEqual(
                        calcular_nivel(codificar_respuestas(letras), self.ejemplos), nivel
                    )

    def test_los_extremos_dan_nivel_uno_y_diez(self):
        self.assertEqual(calcular_nivel((0,) * 10, self.ejemplos), 1)
        self.assertEqual(calcular_nivel((4,) * 10, self.ejemplos), 10)
        self.assertEqual(calcular_nivel((2,) * 10, self.ejemplos), 5)

    def test_una_sola_respuesta_mala_no_dispara_el_nivel(self):
        self.assertEqual(calcular_nivel(codificar_respuestas("EAAAAAAAAA"), self.ejemplos), 2)

    def test_los_ejemplos_de_personas_reales_influyen(self):
        raro = codificar_respuestas("EAEAEAEAEA")
        sin_aprender = calcular_nivel(raro, self.ejemplos)
        aprendido = self.ejemplos + [Ejemplo(10, raro, es_de_persona_real=True)]
        self.assertGreater(calcular_nivel(raro, aprendido), sin_aprender)

    def test_codificar_y_decodificar_son_inversas(self):
        self.assertEqual(decodificar_respuestas(codificar_respuestas("ABCDEEDCBA")), "ABCDEEDCBA")


class PruebasDeConsejos(unittest.TestCase):
    def setUp(self):
        self.ejemplos = ejemplos_iniciales()

    def test_devuelve_como_maximo_tres_consejos(self):
        respuestas = codificar_respuestas("DEDEDEDEDE")
        nivel = calcular_nivel(respuestas, self.ejemplos)
        self.assertLessEqual(len(elegir_preguntas_a_mejorar(respuestas, nivel, self.ejemplos)), 3)

    def test_quien_ya_lo_hace_todo_bien_no_recibe_consejos(self):
        self.assertEqual(elegir_preguntas_a_mejorar((0,) * 10, 1, self.ejemplos), [])

    def test_siempre_hay_consejos_si_hay_algo_que_mejorar(self):
        for letras in ("BAAAAAAAAA", "CCCCCCCCCC", "EEEEEEEEEE"):
            respuestas = codificar_respuestas(letras)
            nivel = calcular_nivel(respuestas, self.ejemplos)
            with self.subTest(letras=letras):
                self.assertTrue(elegir_preguntas_a_mejorar(respuestas, nivel, self.ejemplos))

    def test_los_consejos_apuntan_a_las_areas_mas_alejadas_de_la_meta(self):
        respuestas = codificar_respuestas("EAAAAAAAAA")
        elegidas = elegir_preguntas_a_mejorar(respuestas, 2, self.ejemplos)
        self.assertEqual(elegidas[0], PREGUNTAS[0])


class PruebasDelProgreso(unittest.TestCase):
    def test_detecta_mejoras_y_empeoramientos(self):
        anterior = Intento(codificar_respuestas("DDDDDDDDDD"), 8)
        nuevas = codificar_respuestas("CCDDDDDDDE")
        progreso = medir_progreso(anterior, nuevas, 7)
        self.assertEqual(progreso.areas_mejoradas, (PREGUNTAS[0].nombre_corto, PREGUNTAS[1].nombre_corto))
        self.assertEqual(progreso.areas_empeoradas, (PREGUNTAS[9].nombre_corto,))
        self.assertEqual((progreso.puntos_anteriores, progreso.puntos_actuales), (30, 29))

    def test_respuestas_iguales_no_generan_cambios(self):
        respuestas = codificar_respuestas("CCCCCCCCCC")
        progreso = medir_progreso(Intento(respuestas, 5), respuestas, 5)
        self.assertEqual((progreso.areas_mejoradas, progreso.areas_empeoradas), ((), ()))


class PruebasDeValidacion(unittest.TestCase):
    def test_el_contenido_actual_es_valido(self):
        validar_contenido()

    def test_avisa_si_un_ejemplo_esta_mal_escrito(self):
        ejemplos_rotos = {**EJEMPLOS_INICIALES, 3: ("AAA",)}
        with patch("planeta.cuestionario.EJEMPLOS_INICIALES", ejemplos_rotos):
            with self.assertRaises(ErrorDeConfiguracion):
                validar_contenido()

    def test_avisa_si_falta_un_nivel(self):
        sin_nivel = {n: v for n, v in EJEMPLOS_INICIALES.items() if n != 4}
        with patch("planeta.cuestionario.EJEMPLOS_INICIALES", sin_nivel):
            with self.assertRaises(ErrorDeConfiguracion):
                validar_contenido()


if __name__ == "__main__":
    unittest.main()

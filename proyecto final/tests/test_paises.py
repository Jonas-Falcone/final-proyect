import unittest

from planeta.configuracion import RUTA_DATOS_PAISES
from planeta.mensajes import construir_embed_pais
from planeta.paises import CatalogoPaises, Valoracion, valorar_puntaje


class PruebasDelCatalogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = CatalogoPaises.desde_archivo(RUTA_DATOS_PAISES)

    def test_conoce_los_paises_del_ranking_y_los_que_no_estan(self):
        argentina = self.catalogo.obtener("AR")
        self.assertEqual((argentina.ranking.puesto, argentina.ranking.puntaje), (58, 34.71))
        self.assertIsNone(self.catalogo.obtener("UY").ranking)
        self.assertIsNotNone(self.catalogo.obtener("UY").emisiones)
        self.assertIsNone(self.catalogo.obtener("EU").emisiones)

    def test_el_ranking_tiene_64_entradas_del_puesto_4_al_67(self):
        puestos = sorted(p.ranking.puesto for p in self.catalogo if p.ranking)
        self.assertEqual(puestos, list(range(4, 68)))

    def test_resolver_acepta_codigos_nombres_y_tildes(self):
        casos = {
            "AR": "AR", "argentina": "AR", "Estados Unidos": "US", "United States": "US",
            "peru": "PE", "Perú": "PE", "Unión Europea": "EU", "niger": "NE", "Nigeria": "NG",
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(self.catalogo.resolver(texto).codigo, esperado)

    def test_resolver_devuelve_nada_si_no_hay_certeza(self):
        for texto in ("", "   ", "Narnia", "xx"):
            with self.subTest(texto=texto):
                self.assertIsNone(self.catalogo.resolver(texto))

    def test_buscar_prioriza_los_que_empiezan_con_el_texto(self):
        resultados = [p.codigo for p in self.catalogo.buscar("arg")]
        self.assertIn("AR", resultados)
        self.assertLessEqual(len(resultados), 25)
        self.assertEqual(len(self.catalogo.buscar("")), 25)

    def test_buscar_solo_con_emisiones_excluye_la_union_europea(self):
        self.assertNotIn("EU", [p.codigo for p in self.catalogo.buscar("union", solo_con_emisiones=True)])
        self.assertIn("EU", [p.codigo for p in self.catalogo.buscar("union")])


class PruebasDeValoracion(unittest.TestCase):
    def test_cortes_de_puntaje(self):
        self.assertEqual(valorar_puntaje(80.52), Valoracion.BIEN)
        self.assertEqual(valorar_puntaje(64.3), Valoracion.BIEN)
        self.assertEqual(valorar_puntaje(57.24), Valoracion.REGULAR)
        self.assertEqual(valorar_puntaje(50.0), Valoracion.MAL)
        self.assertEqual(valorar_puntaje(44.96), Valoracion.MUY_MAL)
        self.assertEqual(valorar_puntaje(11.9), Valoracion.MUY_MAL)


class PruebasDeMensajesDePais(unittest.TestCase):
    def test_todos_los_paises_generan_un_mensaje_valido_para_discord(self):
        catalogo = CatalogoPaises.desde_archivo(RUTA_DATOS_PAISES)
        for pais in catalogo:
            datos = construir_embed_pais(pais, catalogo.promedio_mundial_de_emisiones).to_dict()
            with self.subTest(pais=pais.codigo):
                self.assertLessEqual(len(datos["title"]), 256)
                for campo in datos.get("fields", []):
                    self.assertLessEqual(len(campo["name"]), 256)
                    self.assertLessEqual(len(campo["value"]), 1024)
                self.assertLess(len(str(datos)), 6000)

    def test_argentina_aparece_como_muy_mal_en_el_puesto_58(self):
        catalogo = CatalogoPaises.desde_archivo(RUTA_DATOS_PAISES)
        embed = construir_embed_pais(catalogo.obtener("AR"), catalogo.promedio_mundial_de_emisiones)
        self.assertIn("Muy mal", embed.description)
        self.assertIn("58º", embed.fields[0].value)


if __name__ == "__main__":
    unittest.main()

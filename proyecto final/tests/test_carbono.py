import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from planeta.carbono import (
    CalidadAire,
    ClienteOpenMeteo,
    ClimaActual,
    ComparacionConElPromedio,
    Lugar,
    NivelDeAire,
    clasificar_aire,
    comparar_con_el_promedio,
    consultar_ciudad,
    elegir_lugar,
    estimar_emisiones_de_la_ciudad,
    interpretar_aire,
    interpretar_clima,
    interpretar_lugares,
)
from planeta.errores import ErrorDeServicioExterno

RESPUESTA_DE_LUGARES = {
    "results": [
        {"name": "La Plata", "latitude": -34.9, "longitude": -57.9, "country_code": "AR",
         "admin1": "Provincia de Buenos Aires", "admin2": "Partido de La Plata", "population": 772618},
        {"name": "La Plata", "latitude": 2.39, "longitude": -75.89, "country_code": "CO",
         "admin1": "Huila", "population": 50000},
        {"name": "La Plata", "latitude": -34.0, "longitude": -58.0, "country_code": "AR",
         "admin1": "Santa Fe", "population": 0},
    ]
}


class PruebasDeInterpretacion(unittest.TestCase):
    def test_solo_conserva_los_lugares_del_pais_pedido(self):
        lugares = interpretar_lugares(RESPUESTA_DE_LUGARES, "AR")
        self.assertEqual([l.provincia for l in lugares], ["Provincia de Buenos Aires", "Santa Fe"])
        self.assertIsNone(lugares[1].poblacion)

    def test_sin_resultados_devuelve_lista_vacia(self):
        self.assertEqual(interpretar_lugares({"generationtime_ms": 0.3}, "AR"), [])

    def test_interpreta_el_clima(self):
        clima = interpretar_clima({
            "current": {"temperature_2m": 21.4, "weather_code": 2, "wind_speed_10m": 14.2},
            "daily": {"temperature_2m_min": [12.1], "temperature_2m_max": [23.0]},
        })
        self.assertEqual((clima.temperatura, clima.minima_del_dia, clima.maxima_del_dia), (21.4, 12.1, 23.0))
        self.assertTrue(clima.tiene_datos)
        self.assertFalse(interpretar_clima({"current": {}}).tiene_datos)
        self.assertFalse(interpretar_clima({}).tiene_datos)

    def test_interpreta_el_aire(self):
        aire = interpretar_aire({"current": {"us_aqi": 62, "pm2_5": 17.3}})
        self.assertEqual((aire.indice, aire.particulas_2_5, aire.ozono), (62, 17.3, None))


class PruebasDeEleccionDeLugar(unittest.TestCase):
    def setUp(self):
        self.lugares = interpretar_lugares(RESPUESTA_DE_LUGARES, "AR")

    def test_prefiere_el_lugar_de_la_provincia_indicada(self):
        lugar, coincide = elegir_lugar(self.lugares, "Santa Fe")
        self.assertEqual((lugar.provincia, coincide), ("Santa Fe", True))

    def test_acepta_la_provincia_escrita_de_forma_parcial_o_con_tildes(self):
        for escrito in ("Buenos Aires", "provincia de buenos aires", "BUENOS AIRES"):
            with self.subTest(escrito=escrito):
                self.assertTrue(elegir_lugar(self.lugares, escrito)[1])

    def test_si_la_provincia_no_coincide_usa_el_lugar_mas_poblado(self):
        lugar, coincide = elegir_lugar(self.lugares, "Narnia")
        self.assertEqual((lugar.provincia, coincide), ("Provincia de Buenos Aires", False))

    def test_una_provincia_demasiado_corta_no_cuenta_como_coincidencia(self):
        self.assertFalse(elegir_lugar(self.lugares, "Bu")[1])
        self.assertFalse(elegir_lugar(self.lugares, "")[1])


class PruebasDeClasificacion(unittest.TestCase):
    def test_limites_del_indice_de_aire(self):
        casos = {0: NivelDeAire.BUENA, 50: NivelDeAire.BUENA, 51: NivelDeAire.MODERADA,
                 150: NivelDeAire.DANINA_PARA_SENSIBLES, 200: NivelDeAire.DANINA,
                 300: NivelDeAire.MUY_DANINA, 301: NivelDeAire.PELIGROSA}
        for indice, esperado in casos.items():
            with self.subTest(indice=indice):
                self.assertEqual(clasificar_aire(indice), esperado)

    def test_comparacion_con_el_promedio_mundial(self):
        self.assertEqual(comparar_con_el_promedio(10, 4.7), ComparacionConElPromedio.POR_ENCIMA)
        self.assertEqual(comparar_con_el_promedio(4.7, 4.7), ComparacionConElPromedio.PARECIDO)
        self.assertEqual(comparar_con_el_promedio(1, 4.7), ComparacionConElPromedio.POR_DEBAJO)

    def test_estimacion_de_emisiones_de_la_ciudad(self):
        self.assertEqual(estimar_emisiones_de_la_ciudad(2.0, 1000), 2000.0)
        self.assertIsNone(estimar_emisiones_de_la_ciudad(2.0, None))
        self.assertIsNone(estimar_emisiones_de_la_ciudad(2.0, 0))


class ClienteFalso:
    def __init__(self, lugares, clima=None, aire=None, falla_clima=False, falla_aire=False, falla_todo=False):
        self._lugares, self._clima, self._aire = lugares, clima, aire
        self._falla_clima, self._falla_aire, self._falla_todo = falla_clima, falla_aire, falla_todo

    async def buscar_lugares(self, ciudad, codigo_pais):
        if self._falla_todo:
            raise ErrorDeServicioExterno("sin conexión")
        return self._lugares

    async def obtener_clima(self, lugar):
        if self._falla_clima:
            raise ErrorDeServicioExterno("sin conexión")
        return self._clima

    async def obtener_aire(self, lugar):
        if self._falla_aire:
            raise ErrorDeServicioExterno("sin conexión")
        return self._aire


class PruebasDeConsulta(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.lugares = interpretar_lugares(RESPUESTA_DE_LUGARES, "AR")
        self.clima = ClimaActual(2, 21.4, 20.9, 63, 14.2, 0.0, 12.1, 23.0)
        self.aire = CalidadAire(62, 17.3, 28.1, 12.0, 71.5)

    async def test_consulta_completa(self):
        cliente = ClienteFalso(self.lugares, self.clima, self.aire)
        consulta = await consultar_ciudad(cliente, "AR", "Buenos Aires", "La Plata")
        self.assertEqual((consulta.lugar.provincia, consulta.provincia_coincide), ("Provincia de Buenos Aires", True))
        self.assertIs(consulta.clima, self.clima)
        self.assertIs(consulta.aire, self.aire)

    async def test_ciudad_inexistente(self):
        self.assertIsNone(await consultar_ciudad(ClienteFalso([]), "AR", "x", "Xyzzy"))

    async def test_si_falla_el_clima_o_el_aire_igual_devuelve_el_resto(self):
        sin_clima = await consultar_ciudad(
            ClienteFalso(self.lugares, aire=self.aire, falla_clima=True), "AR", "", "La Plata")
        self.assertEqual((sin_clima.clima, sin_clima.aire), (None, self.aire))
        sin_aire = await consultar_ciudad(
            ClienteFalso(self.lugares, clima=self.clima, falla_aire=True), "AR", "", "La Plata")
        self.assertEqual((sin_aire.clima, sin_aire.aire), (self.clima, None))

    async def test_si_falla_la_busqueda_se_propaga_el_error(self):
        with self.assertRaises(ErrorDeServicioExterno):
            await consultar_ciudad(ClienteFalso([], falla_todo=True), "AR", "x", "y")

    async def test_un_error_inesperado_no_se_esconde(self):
        cliente = ClienteFalso(self.lugares, self.clima, self.aire)
        cliente.obtener_aire = AsyncMock(side_effect=KeyError("bug"))
        with self.assertRaises(KeyError):
            await consultar_ciudad(cliente, "AR", "", "La Plata")


class PruebasDelClienteHttp(unittest.IsolatedAsyncioTestCase):
    async def test_los_errores_de_red_se_convierten_en_error_de_servicio(self):
        cliente = ClienteOpenMeteo()
        sesion = MagicMock()
        sesion.closed = False
        sesion.get.side_effect = aiohttp.ClientConnectionError("sin red")
        cliente._sesion = sesion
        with self.assertRaises(ErrorDeServicioExterno):
            await cliente.buscar_lugares("La Plata", "AR")

    async def test_envia_los_parametros_como_texto(self):
        cliente = ClienteOpenMeteo()
        recibido = {}

        async def falso(self, url, parametros):
            recibido.update(parametros)
            return {}

        lugar = Lugar("X", -34.9, -57.9, None, (), None)
        with patch.object(ClienteOpenMeteo, "_pedir_json", falso):
            await cliente.obtener_clima(lugar)
        self.assertEqual((recibido["latitude"], recibido["forecast_days"]), (-34.9, 1))
        await cliente.cerrar()


if __name__ == "__main__":
    unittest.main()

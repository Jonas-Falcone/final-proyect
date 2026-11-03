import unittest
import unittest.mock
from unittest.mock import patch

import discord
from discord import app_commands

from planeta.carbono import CalidadAire, ClienteOpenMeteo, ClimaActual, Lugar
from planeta.codigos import formatear_codigo, limpiar_codigo
from planeta.comandos import crear_autocompletado, crear_bot
from planeta.errores import ErrorDeServicioExterno
from planeta.mensajes import MENSAJE_CODIGO_NO_ENCONTRADO, MENSAJE_DE_ERROR_GENERAL
from planeta.vistas import CodigoModal, CuestionarioView
from tests.ayudas import (
    con_valores_elegidos,
    crear_interaccion_falsa,
    crear_servicios_de_prueba,
)

PRIMER_INTENTO = (3, 2, 3, 2, 3, 3, 2, 3, 2, 3)
SEGUNDO_INTENTO = (1, 1, 2, 1, 1, 2, 1, 1, 1, 1)


class PruebasDelFlujoDeHuella(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.servicios = crear_servicios_de_prueba()
        self.bot = crear_bot(self.servicios, None)
        self.interaccion = crear_interaccion_falsa()

    def ultimos_argumentos(self):
        return self.interaccion.response.edit_message.call_args.kwargs

    async def contestar(self, vista, respuestas):
        for numero, respuesta in enumerate(respuestas, start=1):
            seleccion = vista.children[0]
            with con_valores_elegidos(seleccion, [str(respuesta)]):
                await seleccion.callback(self.interaccion)
            if numero < len(respuestas):
                vista = self.ultimos_argumentos()["view"]
        return self.ultimos_argumentos()

    async def abrir_menu(self):
        await self.bot.tree.get_command("huella").callback(self.interaccion)
        argumentos = self.interaccion.response.send_message.call_args.kwargs
        self.assertTrue(argumentos["ephemeral"])
        return argumentos["view"]

    async def hacer_prueba_nueva(self):
        menu = await self.abrir_menu()
        await menu.children[1].callback(self.interaccion)
        return await self.contestar(self.ultimos_argumentos()["view"], PRIMER_INTENTO)

    async def test_el_menu_ofrece_las_dos_opciones(self):
        menu = await self.abrir_menu()
        self.assertEqual([b.label for b in menu.children], ["Mejorar puntuación", "Iniciar prueba nueva"])

    async def test_prueba_nueva_entrega_un_codigo_de_cuenta(self):
        resultado = await self.hacer_prueba_nueva()
        campos = {campo.name: campo.value for campo in resultado["embed"].fields}
        self.assertIn("🔑 Tu código de cuenta", campos)
        self.assertNotIn("📈 Tu progreso", campos)
        codigo = limpiar_codigo(campos["🔑 Tu código de cuenta"].split("`")[1])
        self.assertEqual(len(self.servicios.repositorio.historial(codigo)), 1)

    async def test_las_10_preguntas_se_muestran_en_orden(self):
        menu = await self.abrir_menu()
        await menu.children[1].callback(self.interaccion)
        self.assertEqual(self.ultimos_argumentos()["embed"].title, "Pregunta 1 de 10")
        vista = self.ultimos_argumentos()["view"]
        for esperada in range(2, 11):
            with con_valores_elegidos(vista.children[0], ["0"]):
                await vista.children[0].callback(self.interaccion)
            self.assertEqual(self.ultimos_argumentos()["embed"].title, f"Pregunta {esperada} de 10")
            vista = self.ultimos_argumentos()["view"]

    async def test_confirmar_el_nivel_agrega_un_ejemplo_nuevo(self):
        resultado = await self.hacer_prueba_nueva()
        antes = len(self.servicios.repositorio.cargar_ejemplos())
        await resultado["view"].children[0].callback(self.interaccion)
        self.assertEqual(len(self.servicios.repositorio.cargar_ejemplos()), antes + 1)
        self.assertIsNone(self.ultimos_argumentos()["view"])

    async def test_corregir_el_nivel_guarda_el_nivel_elegido(self):
        resultado = await self.hacer_prueba_nueva()
        vista = resultado["view"]
        await vista.children[1].callback(self.interaccion)
        seleccion = vista.children[0]
        self.assertEqual(len(seleccion.options), 10)
        with con_valores_elegidos(seleccion, ["9"]):
            await seleccion.callback(self.interaccion)
        self.assertEqual(self.servicios.repositorio.cargar_ejemplos()[-1].nivel, 9)

    async def test_mejorar_puntuacion_con_el_codigo_muestra_el_progreso(self):
        resultado = await self.hacer_prueba_nueva()
        codigo = formatear_codigo(
            limpiar_codigo(resultado["embed"].fields[-1].value.split("`")[1])
        )
        menu = await self.abrir_menu()
        await menu.children[0].callback(self.interaccion)
        modal = self.interaccion.response.send_modal.call_args.args[0]
        self.assertIsInstance(modal, CodigoModal)
        with patch.object(discord.ui.TextInput, "value", new_callable=unittest.mock.PropertyMock,
                          return_value=f" {codigo.lower()} "):
            await modal.on_submit(self.interaccion)
        bienvenida = self.ultimos_argumentos()
        self.assertIn(codigo, bienvenida["content"])
        self.assertIsInstance(bienvenida["view"], CuestionarioView)
        cuentas_antes = self.servicios.repositorio._conexion.execute("SELECT COUNT(*) FROM cuentas").fetchone()[0]
        resultado = await self.contestar(bienvenida["view"], SEGUNDO_INTENTO)
        campos = {campo.name: campo.value for campo in resultado["embed"].fields}
        self.assertIn("📈 Tu progreso", campos)
        self.assertIn("Intentos: 2", campos["🔑 Tu código de cuenta"])
        cuentas_despues = self.servicios.repositorio._conexion.execute("SELECT COUNT(*) FROM cuentas").fetchone()[0]
        self.assertEqual(cuentas_antes, cuentas_despues)

    async def test_un_codigo_incorrecto_muestra_un_error_sin_romper_el_menu(self):
        modal = CodigoModal(self.servicios)
        with patch.object(discord.ui.TextInput, "value", new_callable=unittest.mock.PropertyMock,
                          return_value="QQQQ-QQQQ"):
            await modal.on_submit(self.interaccion)
        self.interaccion.response.send_message.assert_awaited_once_with(
            MENSAJE_CODIGO_NO_ENCONTRADO, ephemeral=True)
        self.interaccion.response.edit_message.assert_not_awaited()


class PruebasDeComandos(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.servicios = crear_servicios_de_prueba()
        self.bot = crear_bot(self.servicios, None)
        self.interaccion = crear_interaccion_falsa()

    def comando(self, nombre):
        return self.bot.tree.get_command(nombre).callback

    def test_estan_los_tres_comandos(self):
        self.assertEqual({c.name for c in self.bot.tree.get_commands()}, {"huella", "pais", "carbono"})

    async def test_el_autocompletado_sugiere_paises_con_bandera(self):
        sugerencias = await crear_autocompletado(self.servicios.catalogo, False)(self.interaccion, "arg")
        self.assertIn("AR", [s.value for s in sugerencias])
        self.assertTrue(all(len(s.name) <= 100 for s in sugerencias))
        vacias = await crear_autocompletado(self.servicios.catalogo, False)(self.interaccion, "")
        self.assertEqual(len(vacias), 25)

    async def test_pais_responde_con_el_ranking(self):
        await self.comando("pais")(self.interaccion, "AR")
        embed = self.interaccion.response.send_message.call_args.kwargs["embed"]
        self.assertTrue(embed.title.endswith("Argentina"))

    async def test_pais_desconocido_responde_en_privado(self):
        await self.comando("pais")(self.interaccion, "Narnia")
        self.assertTrue(self.interaccion.response.send_message.call_args.kwargs["ephemeral"])

    async def test_carbono_con_datos_completos(self):
        lugar = Lugar("La Plata", -34.9, -57.9, "Provincia de Buenos Aires", ("Provincia de Buenos Aires",), 772618)
        clima = ClimaActual(2, 21.4, 20.9, 63, 14.2, 0.0, 12.1, 23.0)
        aire = CalidadAire(62, 17.3, 28.1, 12.0, 71.5)

        async def buscar(self, ciudad, codigo_pais):
            return [lugar]

        async def obtener_clima(self, _):
            return clima

        async def obtener_aire(self, _):
            return aire

        with patch.multiple(ClienteOpenMeteo, buscar_lugares=buscar, obtener_clima=obtener_clima, obtener_aire=obtener_aire):
            await self.comando("carbono")(self.interaccion, "AR", "Buenos Aires", "La Plata")
        self.interaccion.response.defer.assert_awaited_once()
        embed = self.interaccion.followup.send.call_args.kwargs["embed"]
        self.assertEqual(embed.title, "🌍 La Plata, Provincia de Buenos Aires, Argentina")
        self.assertIn("772.618", embed.fields[0].value)

    async def test_carbono_con_una_ciudad_que_no_existe(self):
        async def buscar(self, ciudad, codigo_pais):
            return []

        with patch.object(ClienteOpenMeteo, "buscar_lugares", buscar):
            await self.comando("carbono")(self.interaccion, "AR", "Buenos Aires", "Xyzzy")
        mensaje = self.interaccion.followup.send.call_args.args[0]
        self.assertIn("No encontré la ciudad «Xyzzy» en Argentina", mensaje)

    async def test_carbono_cuando_el_servicio_externo_falla(self):
        async def buscar(self, ciudad, codigo_pais):
            raise ErrorDeServicioExterno("sin red")

        with patch.object(ClienteOpenMeteo, "buscar_lugares", buscar), self.assertLogs(level="ERROR"):
            await self.comando("carbono")(self.interaccion, "AR", "Buenos Aires", "La Plata")
        self.assertIn("No pude conectarme", self.interaccion.followup.send.call_args.args[0])

    async def test_carbono_rechaza_paises_sin_datos_de_emisiones(self):
        for pais in ("Narnia", "Unión Europea"):
            with self.subTest(pais=pais):
                await self.comando("carbono")(self.interaccion, pais, "x", "y")
                self.assertIn("No reconocí el país", self.interaccion.response.send_message.call_args.args[0])
        self.interaccion.response.defer.assert_not_awaited()

    async def test_un_error_inesperado_le_avisa_al_usuario(self):
        manejador = self.bot.tree.on_error
        self.interaccion.response.is_done.return_value = False
        with self.assertLogs(level="ERROR"):
            await manejador(self.interaccion, app_commands.AppCommandError("falló"))
        self.interaccion.response.send_message.assert_awaited_with(MENSAJE_DE_ERROR_GENERAL, ephemeral=True)
        self.interaccion.response.is_done.return_value = True
        with self.assertLogs(level="ERROR"):
            await manejador(self.interaccion, app_commands.AppCommandError("falló"))
        self.interaccion.followup.send.assert_awaited_with(MENSAJE_DE_ERROR_GENERAL, ephemeral=True)


if __name__ == "__main__":
    unittest.main()

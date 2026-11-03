import logging
from typing import Optional

import discord
from discord import app_commands

from planeta.carbono import consultar_ciudad
from planeta.errores import ErrorDeServicioExterno
from planeta.formato import emoji_bandera
from planeta.mensajes import (
    MENSAJE_DE_ERROR_GENERAL,
    MENSAJE_SERVICIO_NO_DISPONIBLE,
    construir_embed_carbono,
    construir_embed_pais,
    mensaje_ciudad_no_encontrada,
    mensaje_pais_no_reconocido,
)
from planeta.paises import CatalogoPaises
from planeta.servicios import Servicios
from planeta.vistas import crear_menu_de_huella


class BotPlaneta(discord.Client):
    def __init__(self, servicios: Servicios, id_servidor: Optional[int]) -> None:
        super().__init__(intents=discord.Intents.default())
        self.servicios = servicios
        self.tree = app_commands.CommandTree(self)
        self._id_servidor = id_servidor

    async def setup_hook(self) -> None:
        if self._id_servidor is None:
            await self.tree.sync()
            return
        servidor = discord.Object(id=self._id_servidor)
        self.tree.copy_global_to(guild=servidor)
        await self.tree.sync(guild=servidor)

    async def on_ready(self) -> None:
        print(f"✅ Conectado como {self.user}. Comandos: /huella, /pais, /carbono")

    async def close(self) -> None:
        await super().close()
        await self.servicios.clima.cerrar()
        self.servicios.repositorio.cerrar()


def crear_autocompletado(catalogo: CatalogoPaises, solo_con_emisiones: bool):
    async def autocompletar(
        interaction: discord.Interaction, texto_escrito: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=f"{emoji_bandera(pais.codigo)} {pais.nombre}", value=pais.codigo)
            for pais in catalogo.buscar(texto_escrito, solo_con_emisiones)
        ]

    return autocompletar


def registrar_comandos(bot: BotPlaneta) -> None:
    servicios = bot.servicios
    catalogo = servicios.catalogo

    @bot.tree.command(
        name="huella", description="Descubre tu nivel de daño al planeta o mejora tu puntuación"
    )
    async def comando_huella(interaction: discord.Interaction) -> None:
        embed, vista = crear_menu_de_huella(servicios)
        await interaction.response.send_message(embed=embed, view=vista, ephemeral=True)

    @bot.tree.command(
        name="pais",
        description="Mira cómo le va a un país contra el cambio climático y su puesto mundial",
    )
    @app_commands.describe(pais="Empieza a escribir y elige un país de la lista")
    @app_commands.autocomplete(pais=crear_autocompletado(catalogo, solo_con_emisiones=False))
    async def comando_pais(interaction: discord.Interaction, pais: str) -> None:
        pais_encontrado = catalogo.resolver(pais)
        if pais_encontrado is None:
            await interaction.response.send_message(
                mensaje_pais_no_reconocido(pais), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=construir_embed_pais(pais_encontrado, catalogo.promedio_mundial_de_emisiones)
        )

    @bot.tree.command(
        name="carbono", description="Huella de carbono, clima y calidad del aire de tu ciudad"
    )
    @app_commands.describe(
        pais="Tu país (elígelo de la lista)",
        provincia="Tu provincia, estado o región",
        ciudad="Tu ciudad",
    )
    @app_commands.autocomplete(pais=crear_autocompletado(catalogo, solo_con_emisiones=True))
    async def comando_carbono(
        interaction: discord.Interaction, pais: str, provincia: str, ciudad: str
    ) -> None:
        pais_encontrado = catalogo.resolver(pais)
        if pais_encontrado is None or pais_encontrado.emisiones is None:
            await interaction.response.send_message(
                mensaje_pais_no_reconocido(pais), ephemeral=True
            )
            return
        await interaction.response.defer(thinking=True)
        try:
            consulta = await consultar_ciudad(
                servicios.clima, pais_encontrado.codigo, provincia, ciudad
            )
        except ErrorDeServicioExterno:
            logging.exception("Falló la consulta de /carbono")
            await interaction.followup.send(MENSAJE_SERVICIO_NO_DISPONIBLE, ephemeral=True)
            return
        if consulta is None:
            await interaction.followup.send(
                mensaje_ciudad_no_encontrada(ciudad, pais_encontrado.nombre), ephemeral=True
            )
            return
        await interaction.followup.send(
            embed=construir_embed_carbono(
                pais_encontrado, provincia, consulta, catalogo.promedio_mundial_de_emisiones
            )
        )

    @bot.tree.error
    async def al_fallar_un_comando(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        logging.error("Error inesperado en un comando", exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send(MENSAJE_DE_ERROR_GENERAL, ephemeral=True)
        else:
            await interaction.response.send_message(MENSAJE_DE_ERROR_GENERAL, ephemeral=True)


def crear_bot(servicios: Servicios, id_servidor: Optional[int]) -> BotPlaneta:
    bot = BotPlaneta(servicios, id_servidor)
    registrar_comandos(bot)
    return bot

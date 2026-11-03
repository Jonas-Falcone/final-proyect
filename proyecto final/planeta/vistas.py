from __future__ import annotations

import discord

from planeta.contenido import NIVELES, PREGUNTAS
from planeta.cuestionario import Respuestas
from planeta.mensajes import (
    MENSAJE_CODIGO_NO_ENCONTRADO,
    MENSAJE_DE_AGRADECIMIENTO,
    MENSAJE_PARA_PEDIR_OPINION,
    construir_embed_menu,
    construir_embed_pregunta,
    construir_embed_resultado,
    construir_texto_de_bienvenida,
)
from planeta.servicio_huella import buscar_cuenta, completar_cuestionario
from planeta.servicios import Servicios

SEGUNDOS_DE_VIGENCIA = 900


class MenuHuellaView(discord.ui.View):
    def __init__(self, servicios: Servicios) -> None:
        super().__init__(timeout=SEGUNDOS_DE_VIGENCIA)
        self._servicios = servicios

    @discord.ui.button(label="Mejorar puntuación", emoji="📈", style=discord.ButtonStyle.primary)
    async def mejorar_puntuacion(
        self, interaction: discord.Interaction, boton: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(CodigoModal(self._servicios))

    @discord.ui.button(label="Iniciar prueba nueva", emoji="🆕", style=discord.ButtonStyle.success)
    async def iniciar_prueba_nueva(
        self, interaction: discord.Interaction, boton: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(
            embed=construir_embed_pregunta(0),
            view=CuestionarioView(self._servicios, (), None),
        )


class CodigoModal(discord.ui.Modal, title="Mejorar puntuación"):
    codigo = discord.ui.TextInput(
        label="Tu código de cuenta", placeholder="Ejemplo: K7M2-QX9P", max_length=20
    )

    def __init__(self, servicios: Servicios) -> None:
        super().__init__()
        self._servicios = servicios

    async def on_submit(self, interaction: discord.Interaction) -> None:
        cuenta = buscar_cuenta(self._servicios.repositorio, self.codigo.value)
        if cuenta is None:
            await interaction.response.send_message(MENSAJE_CODIGO_NO_ENCONTRADO, ephemeral=True)
            return
        await interaction.response.edit_message(
            content=construir_texto_de_bienvenida(cuenta),
            embed=construir_embed_pregunta(0),
            view=CuestionarioView(self._servicios, (), cuenta.codigo),
        )


class PreguntaSelect(discord.ui.Select):
    def __init__(
        self, servicios: Servicios, respuestas: Respuestas, codigo_de_cuenta: str | None
    ) -> None:
        opciones = [
            discord.SelectOption(label=texto, value=str(indice))
            for indice, texto in enumerate(PREGUNTAS[len(respuestas)].opciones)
        ]
        super().__init__(placeholder="Elige tu respuesta…", options=opciones)
        self._servicios = servicios
        self._respuestas = respuestas
        self._codigo_de_cuenta = codigo_de_cuenta

    async def callback(self, interaction: discord.Interaction) -> None:
        respuestas = self._respuestas + (int(self.values[0]),)
        if len(respuestas) < len(PREGUNTAS):
            await interaction.response.edit_message(
                embed=construir_embed_pregunta(len(respuestas)),
                view=CuestionarioView(self._servicios, respuestas, self._codigo_de_cuenta),
            )
            return
        await mostrar_resultado(interaction, self._servicios, respuestas, self._codigo_de_cuenta)


class CuestionarioView(discord.ui.View):
    def __init__(
        self, servicios: Servicios, respuestas: Respuestas, codigo_de_cuenta: str | None
    ) -> None:
        super().__init__(timeout=SEGUNDOS_DE_VIGENCIA)
        self.add_item(PreguntaSelect(servicios, respuestas, codigo_de_cuenta))


class NivelSelect(discord.ui.Select):
    def __init__(self, servicios: Servicios, id_del_intento: int) -> None:
        opciones = [
            discord.SelectOption(label=f"Nivel {numero} · {nivel.nombre}", value=str(numero))
            for numero, nivel in NIVELES.items()
        ]
        super().__init__(placeholder="¿Qué nivel crees que eres?", options=opciones)
        self._servicios = servicios
        self._id_del_intento = id_del_intento

    async def callback(self, interaction: discord.Interaction) -> None:
        self._servicios.repositorio.confirmar_intento(self._id_del_intento, int(self.values[0]))
        await agradecer(interaction)


class OpinionView(discord.ui.View):
    def __init__(self, servicios: Servicios, id_del_intento: int, nivel: int) -> None:
        super().__init__(timeout=SEGUNDOS_DE_VIGENCIA)
        self._servicios = servicios
        self._id_del_intento = id_del_intento
        self._nivel = nivel

    @discord.ui.button(label="Sí, es justo", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar_nivel(
        self, interaction: discord.Interaction, boton: discord.ui.Button
    ) -> None:
        self._servicios.repositorio.confirmar_intento(self._id_del_intento, self._nivel)
        await agradecer(interaction)

    @discord.ui.button(
        label="Creo que soy otro nivel", emoji="🤔", style=discord.ButtonStyle.secondary
    )
    async def corregir_nivel(
        self, interaction: discord.Interaction, boton: discord.ui.Button
    ) -> None:
        self.clear_items()
        self.add_item(NivelSelect(self._servicios, self._id_del_intento))
        await interaction.response.edit_message(view=self)


async def mostrar_resultado(
    interaction: discord.Interaction,
    servicios: Servicios,
    respuestas: Respuestas,
    codigo_de_cuenta: str | None,
) -> None:
    resultado = completar_cuestionario(servicios.repositorio, respuestas, codigo_de_cuenta)
    await interaction.response.edit_message(
        content=MENSAJE_PARA_PEDIR_OPINION,
        embed=construir_embed_resultado(resultado),
        view=OpinionView(servicios, resultado.id_del_intento, resultado.nivel),
    )


async def agradecer(interaction: discord.Interaction) -> None:
    await interaction.response.edit_message(content=MENSAJE_DE_AGRADECIMIENTO, view=None)


def crear_menu_de_huella(servicios: Servicios) -> tuple[discord.Embed, MenuHuellaView]:
    return construir_embed_menu(), MenuHuellaView(servicios)

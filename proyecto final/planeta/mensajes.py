from __future__ import annotations

import discord

from planeta.carbono import (
    CalidadAire,
    ClimaActual,
    ComparacionConElPromedio,
    ConsultaCiudad,
    NivelDeAire,
    clasificar_aire,
    comparar_con_el_promedio,
    estimar_emisiones_de_la_ciudad,
)
from planeta.codigos import formatear_codigo
from planeta.contenido import NIVELES, PREGUNTAS
from planeta.cuestionario import NIVEL_MAXIMO, NIVEL_MINIMO, Progreso
from planeta.formato import barra_de_progreso, emoji_bandera, formatear_numero
from planeta.paises import (
    TOTAL_DE_PUESTOS_DEL_RANKING,
    Emisiones,
    Pais,
    RankingClimatico,
    Valoracion,
    valorar_puntaje,
)
from planeta.servicio_huella import CuentaExistente, ResultadoDeHuella

MENSAJE_PARA_PEDIR_OPINION = "¿Te parece acertado tu nivel? Tu opinión ayuda a mejorar el bot 👇"
MENSAJE_DE_AGRADECIMIENTO = "🙏 ¡Gracias! Tu respuesta ayuda a que el bot sea más preciso."
MENSAJE_CODIGO_NO_ENCONTRADO = (
    "❌ No encontré ese código. Revisa que esté bien escrito (ejemplo: `K7M2-QX9P`) "
    "o elige **Iniciar prueba nueva** para crear tu cuenta."
)
MENSAJE_SERVICIO_NO_DISPONIBLE = (
    "😕 No pude conectarme al servicio de datos. Intenta de nuevo en unos minutos."
)
MENSAJE_DE_ERROR_GENERAL = "😕 Algo salió mal. Intenta de nuevo en unos minutos."

TEXTO_DE_PRIVACIDAD = "Tus respuestas se guardan de forma anónima para que el bot mejore."
EMOJI_POR_RESPUESTA = ("🟢", "🟢", "🟡", "🟠", "🔴")
COLOR_SIN_RANKING = 0x95A5A6

AREAS_DEL_RANKING = (
    ("ghg", "Emisiones de gases"),
    ("renovables", "Energías renovables"),
    ("energia", "Uso de energía"),
    ("politica", "Política climática"),
)
EMOJI_POR_CALIFICACION = {
    "Muy alto": "🟢",
    "Alto": "🟢",
    "Medio": "🟡",
    "Bajo": "🟠",
    "Muy bajo": "🔴",
}
VALORACIONES = {
    Valoracion.BIEN: (
        "🟢", 0x2ECC71, "Bien: es de los países que más hacen contra el cambio climático.",
    ),
    Valoracion.REGULAR: (
        "🟡", 0xF1C40F, "Regular: hace cosas, pero todavía le falta bastante.",
    ),
    Valoracion.MAL: ("🟠", 0xE67E22, "Mal: hace menos de lo que debería."),
    Valoracion.MUY_MAL: (
        "🔴", 0xE74C3C, "Muy mal: es de los países que menos hacen contra el cambio climático.",
    ),
}
VEREDICTOS_DE_COMPARACION = {
    ComparacionConElPromedio.POR_ENCIMA: "🔴 por encima del promedio mundial",
    ComparacionConElPromedio.PARECIDO: "🟡 parecido al promedio mundial",
    ComparacionConElPromedio.POR_DEBAJO: "🟢 por debajo del promedio mundial",
}
DESCRIPCIONES_DE_CLIMA = (
    ({0}, "☀️", "Despejado"),
    ({1}, "🌤️", "Mayormente despejado"),
    ({2}, "⛅", "Parcialmente nublado"),
    ({3}, "☁️", "Nublado"),
    ({45, 48}, "🌫️", "Niebla"),
    ({51, 53, 55, 56, 57}, "🌦️", "Llovizna"),
    ({61, 63, 65, 66, 67}, "🌧️", "Lluvia"),
    ({71, 73, 75, 77}, "❄️", "Nieve"),
    ({80, 81, 82}, "🌦️", "Chubascos"),
    ({85, 86}, "🌨️", "Chubascos de nieve"),
    ({95, 96, 99}, "⛈️", "Tormenta"),
)
DESCRIPCIONES_DE_AIRE = {
    NivelDeAire.BUENA: (
        "🟢", "Buena", "Aire limpio: puedes hacer actividades al aire libre.",
    ),
    NivelDeAire.MODERADA: (
        "🟡", "Moderada", "Aceptable; las personas muy sensibles podrían notar molestias.",
    ),
    NivelDeAire.DANINA_PARA_SENSIBLES: (
        "🟠",
        "Dañina para grupos sensibles",
        "Niños, mayores y personas con asma: mejor reducir el esfuerzo al aire libre.",
    ),
    NivelDeAire.DANINA: (
        "🔴", "Dañina", "Conviene reducir las actividades intensas al aire libre.",
    ),
    NivelDeAire.MUY_DANINA: ("🟣", "Muy dañina", "Evita las actividades al aire libre."),
    NivelDeAire.PELIGROSA: ("🟤", "Peligrosa", "Quédate en espacios cerrados."),
}


def mensaje_pais_no_reconocido(texto: str) -> str:
    return f"No reconocí el país «{texto}». Empieza a escribirlo y elígelo de la lista."


def mensaje_ciudad_no_encontrada(ciudad: str, nombre_del_pais: str) -> str:
    return f"No encontré la ciudad «{ciudad}» en {nombre_del_pais}. Revisa que esté bien escrita."


def construir_embed_menu() -> discord.Embed:
    return discord.Embed(
        title="🌍 ¿Cuánto daño le haces al planeta?",
        description=(
            "Responde 10 preguntas y descubre tu **nivel de impacto** "
            "(1 = poco daño, 10 = muchísimo).\n\n"
            "🆕 **Iniciar prueba nueva**: haces el test y al final te damos "
            "un **código de cuenta**.\n"
            "📈 **Mejorar puntuación**: pones tu código, repites la prueba "
            "y ves si lograste bajar tu nivel."
        ),
        color=discord.Color.green(),
    )


def construir_embed_pregunta(indice: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Pregunta {indice + 1} de {len(PREGUNTAS)}",
        description=PREGUNTAS[indice].texto,
        color=discord.Color.green(),
    )
    if indice == 0:
        embed.set_footer(text=TEXTO_DE_PRIVACIDAD)
    return embed


def construir_texto_de_bienvenida(cuenta: CuentaExistente) -> str:
    niveles = [intento.nivel for intento in cuenta.intentos]
    return (
        f"🔑 Cuenta `{formatear_codigo(cuenta.codigo)}` · "
        f"Último nivel: **{niveles[-1]}** · "
        f"Mejor nivel: **{min(niveles)}** · Intentos: {len(niveles)}\n"
        "Responde otra vez para superar tu puntuación 💪"
    )


def construir_embed_resultado(resultado: ResultadoDeHuella) -> discord.Embed:
    nivel = NIVELES[resultado.nivel]
    embed = discord.Embed(
        title=f"{nivel.nombre} · Nivel {resultado.nivel}/{NIVEL_MAXIMO}",
        description=nivel.descripcion,
        color=_color_segun_el_nivel(resultado.nivel),
    )
    embed.add_field(
        name="Tu perfil (🟢 bajo · 🟡 medio · 🔴 alto impacto)",
        value=_perfil_de_impacto(resultado),
        inline=False,
    )
    if resultado.progreso is not None:
        embed.add_field(
            name="📈 Tu progreso", value=construir_texto_de_progreso(resultado.progreso), inline=False
        )
    titulo_de_consejos, texto_de_consejos = _consejos(resultado)
    embed.add_field(name=titulo_de_consejos, value=texto_de_consejos, inline=False)
    embed.add_field(
        name="🔑 Tu código de cuenta", value=_texto_del_codigo(resultado), inline=False
    )
    embed.set_footer(
        text=(
            f"Comparado con {resultado.ejemplos_usados} ejemplos "
            f"({resultado.ejemplos_de_personas_reales} de personas reales) "
            "· Estimación orientativa"
        )
    )
    return embed


def construir_texto_de_progreso(progreso: Progreso) -> str:
    if progreso.nivel_actual < progreso.nivel_anterior:
        titulo = (
            f"🎉 ¡Mejoraste! Bajaste del nivel {progreso.nivel_anterior} "
            f"al {progreso.nivel_actual}"
        )
    elif progreso.nivel_actual == progreso.nivel_anterior:
        titulo = f"Sigues en el nivel {progreso.nivel_actual}"
    else:
        titulo = (
            f"Subiste del nivel {progreso.nivel_anterior} al {progreso.nivel_actual}. "
            "¡Revisa los consejos y vuelve a intentarlo! 💪"
        )
    lineas = [
        f"**{titulo}**",
        f"Puntos de impacto: {progreso.puntos_anteriores} → "
        f"{progreso.puntos_actuales} (menos es mejor)",
    ]
    if progreso.areas_mejoradas:
        lineas.append("✅ Mejoraste en: " + ", ".join(progreso.areas_mejoradas))
    if progreso.areas_empeoradas:
        lineas.append("⚠️ Empeoraste en: " + ", ".join(progreso.areas_empeoradas))
    if not progreso.areas_mejoradas and not progreso.areas_empeoradas:
        lineas.append("Respondiste igual que la vez anterior.")
    return "\n".join(lineas)


def construir_embed_pais(pais: Pais, promedio_mundial: float) -> discord.Embed:
    embed = discord.Embed(title=f"{emoji_bandera(pais.codigo)} {pais.nombre}")
    if pais.ranking is not None:
        _agregar_ranking(embed, pais.ranking)
    else:
        embed.color = COLOR_SIN_RANKING
        embed.description = (
            "⚪ Este país **no está en el ranking CCPI**, que solo evalúa 63 países y la "
            "Unión Europea (los que más emisiones producen). "
            "Abajo ves cuánto emite por persona."
        )
    if pais.emisiones is not None:
        embed.add_field(
            name="🏭 Emisiones por persona",
            value=_texto_de_emisiones(pais.emisiones, promedio_mundial),
            inline=False,
        )
    embed.set_footer(
        text=(
            "Ranking: CCPI 2026 (Germanwatch, NewClimate Institute y CAN) · "
            "Los puestos 1.º al 3.º quedan vacíos: ningún país hace lo suficiente · "
            "CO₂: Our World in Data"
        )
    )
    return embed


def construir_embed_carbono(
    pais: Pais, provincia_pedida: str, consulta: ConsultaCiudad, promedio_mundial: float
) -> discord.Embed:
    lugar = consulta.lugar
    partes_del_titulo = dict.fromkeys(
        parte for parte in (lugar.nombre, lugar.provincia, pais.nombre) if parte
    )
    embed = discord.Embed(
        title="🌍 " + ", ".join(partes_del_titulo), color=discord.Color.teal()
    )
    if not consulta.provincia_coincide:
        embed.description = (
            f"⚠️ No encontré la provincia «{provincia_pedida}» para esta ciudad, "
            "así que te muestro el lugar más grande con ese nombre."
        )
    embed.add_field(
        name="🏭 Huella de carbono (estimada)",
        value=_texto_de_huella(pais.emisiones, lugar.poblacion, pais.nombre, promedio_mundial),
        inline=False,
    )
    embed.add_field(
        name="🌤️ Clima ahora",
        value=(
            _texto_de_clima(consulta.clima)
            if consulta.clima is not None
            else "No pude obtener el clima en este momento."
        ),
        inline=False,
    )
    embed.add_field(
        name="😮‍💨 Calidad del aire",
        value=(
            _texto_de_aire(consulta.aire)
            if consulta.aire is not None
            else "No pude obtener la calidad del aire en este momento."
        ),
        inline=False,
    )
    embed.set_footer(
        text=(
            "Clima y aire: Open-Meteo.com (el aire viene de un modelo, no de estaciones "
            "locales) · CO₂: Our World in Data / Global Carbon Project"
        )
    )
    return embed


def _color_segun_el_nivel(nivel: int) -> discord.Color:
    avance = (nivel - NIVEL_MINIMO) / (NIVEL_MAXIMO - NIVEL_MINIMO)
    return discord.Color.from_rgb(int(230 * avance) + 25, int(200 * (1 - avance)) + 30, 60)


def _perfil_de_impacto(resultado: ResultadoDeHuella) -> str:
    return " · ".join(
        f"{EMOJI_POR_RESPUESTA[respuesta]} {pregunta.nombre_corto}"
        for respuesta, pregunta in zip(resultado.respuestas, PREGUNTAS)
    )


def _consejos(resultado: ResultadoDeHuella) -> tuple[str, str]:
    if not resultado.preguntas_a_mejorar:
        return (
            "💡 Consejo",
            "¡Ya lo haces todo muy bien! Cuéntales a tus amigos cómo lo logras 🌍",
        )
    titulo = (
        f"💡 Para pasar al nivel {resultado.nivel - 1}, empieza por aquí"
        if resultado.nivel > NIVEL_MINIMO
        else "💡 Para seguir mejorando"
    )
    texto = "\n\n".join(
        f"**{pregunta.nombre_corto}** — {pregunta.consejo}"
        for pregunta in resultado.preguntas_a_mejorar
    )
    return titulo, texto


def _texto_del_codigo(resultado: ResultadoDeHuella) -> str:
    codigo = formatear_codigo(resultado.codigo_de_cuenta)
    if resultado.es_cuenta_nueva:
        return (
            f"`{codigo}`\n⚠️ **Guárdalo**: es tu cuenta. Con él puedes volver a `/huella` → "
            "*Mejorar puntuación* y ver cuánto progresas. "
            "Si lo pierdes no se puede recuperar."
        )
    return (
        f"`{codigo}` · Intentos: {resultado.cantidad_de_intentos} "
        f"· Mejor nivel: {resultado.mejor_nivel}"
    )


def _agregar_ranking(embed: discord.Embed, ranking: RankingClimatico) -> None:
    emoji, color, frase = VALORACIONES[valorar_puntaje(ranking.puntaje)]
    embed.color = color
    embed.description = f"{emoji} **{frase}**"
    embed.add_field(
        name="🏆 Puesto mundial",
        value=f"**{ranking.puesto}º** de {TOTAL_DE_PUESTOS_DEL_RANKING}\nen acción climática",
        inline=True,
    )
    embed.add_field(
        name="📊 Puntaje",
        value=(
            f"{barra_de_progreso(ranking.puntaje)}\n"
            f"**{formatear_numero(ranking.puntaje)}** / 100"
        ),
        inline=True,
    )
    areas = "\n".join(
        f"{EMOJI_POR_CALIFICACION[ranking.calificaciones[clave]]} {nombre}: "
        f"**{ranking.calificaciones[clave]}**"
        for clave, nombre in AREAS_DEL_RANKING
    )
    embed.add_field(
        name="🔎 Cómo le va en cada área (calificación oficial)", value=areas, inline=False
    )


def _texto_de_emisiones(emisiones: Emisiones, promedio_mundial: float) -> str:
    texto = (
        f"**{formatear_numero(emisiones.toneladas_por_persona, 2)} t de CO₂ por persona "
        f"al año** ({emisiones.anio})\n"
        f"Promedio mundial: {formatear_numero(promedio_mundial, 2)} t"
    )
    if emisiones.puesto is not None:
        texto += (
            f"\nPuesto **{emisiones.puesto}º de {emisiones.total_de_paises}** "
            "(1.º = el que más emite por persona)"
        )
    return texto


def _texto_de_huella(
    emisiones: Emisiones,
    poblacion: int | None,
    nombre_del_pais: str,
    promedio_mundial: float,
) -> str:
    por_persona = emisiones.toneladas_por_persona
    veredicto = VEREDICTOS_DE_COMPARACION[comparar_con_el_promedio(por_persona, promedio_mundial)]
    lineas = [
        f"👤 **{formatear_numero(por_persona, 2)} t de CO₂ por persona al año** "
        f"({emisiones.anio}), {veredicto} ({formatear_numero(promedio_mundial, 2)} t)"
    ]
    total = estimar_emisiones_de_la_ciudad(por_persona, poblacion)
    if total is not None:
        lineas.append(
            f"🏙️ **Toda la ciudad: ≈ {_texto_de_toneladas(total)} de CO₂ al año** "
            f"({formatear_numero(poblacion, 0)} habitantes)"
        )
    lineas.append(
        "_Es una estimación: promedio de tu país × habitantes. La huella real depende "
        "de la industria, el transporte y la energía de cada ciudad._"
    )
    return "\n".join(lineas)


def _texto_de_toneladas(toneladas: float) -> str:
    if toneladas >= 1e9:
        return f"{formatear_numero(toneladas / 1e9)} mil millones de toneladas"
    if toneladas >= 1e6:
        return f"{formatear_numero(toneladas / 1e6)} millones de toneladas"
    return f"{formatear_numero(toneladas, 0)} toneladas"


def _describir_clima(codigo: int | None) -> tuple[str, str]:
    for codigos, emoji, descripcion in DESCRIPCIONES_DE_CLIMA:
        if codigo in codigos:
            return emoji, descripcion
    return "🌡️", "Sin descripción"


def _texto_de_clima(clima: ClimaActual) -> str:
    if not clima.tiene_datos:
        return "Sin datos de clima para esta zona."
    emoji, descripcion = _describir_clima(clima.codigo_de_clima)
    lineas = [f"{emoji} {descripcion}"]
    if clima.temperatura is not None:
        sensacion = (
            f" (sensación {formatear_numero(clima.sensacion_termica)} °C)"
            if clima.sensacion_termica is not None
            else ""
        )
        lineas.append(f"🌡️ **{formatear_numero(clima.temperatura)} °C**{sensacion}")
    if clima.minima_del_dia is not None and clima.maxima_del_dia is not None:
        lineas.append(
            f"📅 Hoy: mín {formatear_numero(clima.minima_del_dia)} °C · "
            f"máx {formatear_numero(clima.maxima_del_dia)} °C"
        )
    detalles = []
    if clima.humedad is not None:
        detalles.append(f"💧 Humedad {formatear_numero(clima.humedad, 0)} %")
    if clima.viento is not None:
        detalles.append(f"💨 Viento {formatear_numero(clima.viento, 0)} km/h")
    if clima.precipitacion:
        detalles.append(f"🌧️ Lluvia {formatear_numero(clima.precipitacion)} mm")
    if detalles:
        lineas.append(" · ".join(detalles))
    return "\n".join(lineas)


def _texto_de_aire(aire: CalidadAire) -> str:
    if aire.indice is None:
        return "Sin datos de calidad del aire para esta zona."
    emoji, nombre, consejo = DESCRIPCIONES_DE_AIRE[clasificar_aire(aire.indice)]
    mediciones = (
        ("PM2,5", aire.particulas_2_5),
        ("PM10", aire.particulas_10),
        ("NO₂", aire.dioxido_de_nitrogeno),
        ("O₃", aire.ozono),
    )
    detalle = [
        f"{etiqueta} {formatear_numero(valor)} µg/m³"
        for etiqueta, valor in mediciones
        if valor is not None
    ]
    return "\n".join(
        [
            f"{emoji} **{nombre}** (índice AQI {formatear_numero(aire.indice, 0)})",
            consejo,
            " · ".join(detalle),
        ]
    )

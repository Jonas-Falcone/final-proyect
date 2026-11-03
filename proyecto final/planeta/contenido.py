from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pregunta:
    nombre_corto: str
    texto: str
    opciones: tuple[str, ...]
    consejo: str


@dataclass(frozen=True)
class Nivel:
    nombre: str
    descripcion: str


PREGUNTAS: tuple[Pregunta, ...] = (
    Pregunta(
        nombre_corto="Transporte",
        texto="🚗 ¿Cómo te mueves en tu día a día?",
        opciones=(
            "Camino o voy en bici",
            "Transporte público",
            "Moto o auto compartido",
            "Auto propio, casi todos los días",
            "Auto propio para todo, incluso distancias cortas",
        ),
        consejo=(
            "Cambia algunos trayectos: a pie o en bici los cortos, transporte"
            " público o auto compartido los demás. El transporte es una de "
            "las mayores fuentes de emisiones personales."
        ),
    ),
    Pregunta(
        nombre_corto="Vuelos",
        texto="✈️ ¿Cuántos vuelos tomas al año?",
        opciones=(
            "Ninguno",
            "1 vuelo corto",
            "2 o 3 vuelos",
            "4 a 6 vuelos",
            "Más de 6, o vuelos largos frecuentes",
        ),
        consejo=(
            "Un vuelo largo puede ser una gran parte de tus emisiones del "
            "año. Usa tren o bus en trayectos cortos, agrupa tus viajes y "
            "cambia reuniones lejanas por videollamadas."
        ),
    ),
    Pregunta(
        nombre_corto="Alimentación",
        texto="🥩 ¿Cuánta carne comes?",
        opciones=(
            "Nada (vegetariano/a o vegano/a)",
            "1 o 2 veces por semana",
            "3 o 4 veces por semana",
            "Casi todos los días",
            "En casi todas las comidas",
        ),
        consejo=(
            "Reduce sobre todo la carne de res, la de mayor impacto. Prueba "
            "un día sin carne por semana y suma legumbres y verduras: no hace"
            " falta ser vegano, cada comida cuenta."
        ),
    ),
    Pregunta(
        nombre_corto="Electricidad",
        texto="💡 ¿Cómo usas la electricidad en casa?",
        opciones=(
            "Apago todo lo que no uso y tengo LED y equipos eficientes",
            "Casi siempre apago luces y aparatos",
            "A veces dejo cosas encendidas",
            "Suelo dejar luces, pantallas y cargadores conectados",
            "Todo encendido todo el día, sin pensarlo",
        ),
        consejo=(
            "Apaga luces y desenchufa cargadores, cambia a focos LED y elige "
            "electrodomésticos eficientes. Si puedes, contrata energía "
            "renovable."
        ),
    ),
    Pregunta(
        nombre_corto="Clima del hogar",
        texto="❄️ ¿Y con el aire acondicionado o la calefacción?",
        opciones=(
            "Casi nunca: ventilo, me abrigo o uso ventilador",
            "Solo en días muy extremos",
            "Varias horas al día en temporada",
            "Muchas horas, con una temperatura muy exigente",
            "Todo el día, incluso con ventanas abiertas",
        ),
        consejo=(
            "Aísla puertas y ventanas, ventila de forma natural y ajusta el "
            "termostato un par de grados: usar menos calefacción o aire "
            "acondicionado ya reduce el consumo."
        ),
    ),
    Pregunta(
        nombre_corto="Residuos",
        texto="♻️ ¿Qué haces con tu basura?",
        opciones=(
            "Separo, hago compost y genero muy poca",
            "Separo y reciclo casi todo",
            "Reciclo solo a veces",
            "Casi nunca reciclo",
            "Todo va junto en la misma bolsa",
        ),
        consejo=(
            "Separa tus residuos, haz compost con lo orgánico (en los "
            "basurales produce metano, un gas de efecto invernadero) y sigue "
            "el orden: reducir, reutilizar y reciclar."
        ),
    ),
    Pregunta(
        nombre_corto="Plásticos",
        texto="🥤 ¿Cuánto plástico de un solo uso usas (bolsas, botellas, vasos)?",
        opciones=(
            "Casi nada: llevo botella y bolsa reutilizables",
            "Muy poco",
            "Algunas veces por semana",
            "Casi todos los días",
            "Todos los días, sin alternativa reutilizable",
        ),
        consejo=(
            "Lleva botella y bolsa reutilizables y evita sorbetes y vasos "
            "descartables. El plástico se fabrica sobre todo con combustibles"
            " fósiles."
        ),
    ),
    Pregunta(
        nombre_corto="Consumo",
        texto="🛍️ ¿Qué tan seguido compras ropa o tecnología nueva?",
        opciones=(
            "Solo lo necesario; reparo o compro de segunda mano",
            "Poco y de buena calidad",
            "De vez en cuando, por gusto",
            "Seguido, sobre todo ropa barata o de moda",
            "Muy seguido; cambio de celular o de ropa cada pocos meses",
        ),
        consejo=(
            "Antes de comprar pregúntate si lo necesitas. Repara, compra de "
            "segunda mano y alarga la vida de tu celular y tu ropa: "
            "fabricarlos genera muchas emisiones."
        ),
    ),
    Pregunta(
        nombre_corto="Comida tirada",
        texto="🍎 ¿Cuánta comida terminas tirando?",
        opciones=(
            "Casi nada, lo aprovecho todo",
            "Muy poca",
            "Algo se me echa a perder cada tanto",
            "Bastante cada semana",
            "Tiro comida casi todos los días",
        ),
        consejo=(
            "Planifica las compras, congela las sobras y aprovecha lo que ya "
            "tienes. La comida que se tira desperdicia toda la energía y el "
            "agua usadas para producirla."
        ),
    ),
    Pregunta(
        nombre_corto="Agua",
        texto="🚿 ¿Cómo usas el agua (duchas, grifos)?",
        opciones=(
            "Duchas cortas y grifo cerrado cuando no lo uso",
            "Cuido bastante",
            "Uso normal, sin prestarle atención",
            "Duchas largas y grifo abierto seguido",
            "Mucho derroche: duchas larguísimas, fugas sin arreglar",
        ),
        consejo=(
            "Haz duchas más cortas y cierra el grifo mientras te cepillas los"
            " dientes. Calentar agua gasta energía, así que ahorrar agua "
            "caliente también baja emisiones."
        ),
    ),
)

NIVELES: dict[int, Nivel] = {
    1: Nivel(
        nombre="🌳 Guardián del planeta",
        descripcion=(
            "Tu estilo de vida casi no deja huella: te mueves sin emitir, "
            "comes liviano para el clima y cuidas cada recurso. ¡Eres un "
            "ejemplo a seguir!"
        ),
    ),
    2: Nivel(
        nombre="🌿 Ecologista ejemplar",
        descripcion=(
            "Tus hábitos son muy cuidadosos con el clima. Solo te quedan "
            "detalles por pulir."
        ),
    ),
    3: Nivel(
        nombre="🌱 Muy consciente",
        descripcion=(
            "Tus hábitos son buenos y se nota que piensas en el planeta. Con "
            "unos pocos ajustes llegas a la cima."
        ),
    ),
    4: Nivel(
        nombre="🍃 Consciente",
        descripcion=(
            "Haces muchas cosas bien, pero todavía hay áreas con bastante "
            "margen de mejora."
        ),
    ),
    5: Nivel(
        nombre="🌤️ En camino",
        descripcion=(
            "Estás a mitad de camino: sabes que importa, pero aún te faltan "
            "hábitos firmes."
        ),
    ),
    6: Nivel(
        nombre="🌥️ Distraído",
        descripcion=(
            "Tus hábitos tienen un impacto considerable y muchas veces ni lo "
            "notas. Pequeños cambios harán una gran diferencia."
        ),
    ),
    7: Nivel(
        nombre="☁️ Impacto notable",
        descripcion=(
            "Tus hábitos diarios aportan bastante al cambio climático. Hay "
            "mucho por mejorar y mucho por ganar."
        ),
    ),
    8: Nivel(
        nombre="🌫️ Alto impacto",
        descripcion=(
            "Varios de tus hábitos consumen muchos recursos y emiten mucho. "
            "Es un buen momento para empezar a cambiar."
        ),
    ),
    9: Nivel(
        nombre="🔥 Muy alto impacto",
        descripcion=(
            "Tu estilo de vida tiene una huella muy grande. Los primeros "
            "cambios (transporte, comida, energía) te darán resultados "
            "enormes."
        ),
    ),
    10: Nivel(
        nombre="🌋 Impacto extremo",
        descripcion=(
            "Casi todos tus hábitos tienen el máximo impacto. La buena "
            "noticia: cualquier cambio que hagas cuenta muchísimo."
        ),
    ),
}

EJEMPLOS_INICIALES: dict[int, tuple[str, ...]] = {
    1: ("AAAAAAAAAA", "AABAAAAAAA"),
    2: ("ABAABBAABA", "AAAACAAABB"),
    3: ("BBBBBBBBBA", "CABACABABC"),
    4: ("BBCBCBCBBB", "DACABCBCAC"),
    5: ("CCCCCCCCBB", "DBCCDBCBBC"),
    6: ("CCCCCCDDCC", "DCDBCDCCBD"),
    7: ("DDDDDDDDCB", "EDCDECCCCD"),
    8: ("DDDDDDDDDE", "EEDDCDEDCD"),
    9: ("EEEEDDEEDD", "EDEDEDEDEE"),
    10: ("EEEEEEEEEE", "DEEEEEEEEE"),
}

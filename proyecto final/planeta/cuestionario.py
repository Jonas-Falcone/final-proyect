from __future__ import annotations

import math
from dataclasses import dataclass

from planeta.contenido import EJEMPLOS_INICIALES, NIVELES, PREGUNTAS, Pregunta
from planeta.errores import ErrorDeConfiguracion

Respuestas = tuple[int, ...]

LETRAS_DE_RESPUESTA = "ABCDE"
NIVEL_MINIMO = 1
NIVEL_MAXIMO = 10
CANTIDAD_DE_VECINOS = 5
SUAVIZADO_DE_DISTANCIA = 0.5
MAXIMO_DE_CONSEJOS = 3


@dataclass(frozen=True)
class Ejemplo:
    nivel: int
    respuestas: Respuestas
    es_de_persona_real: bool = False


@dataclass(frozen=True)
class Intento:
    respuestas: Respuestas
    nivel: int


@dataclass(frozen=True)
class Progreso:
    nivel_anterior: int
    nivel_actual: int
    puntos_anteriores: int
    puntos_actuales: int
    areas_mejoradas: tuple[str, ...]
    areas_empeoradas: tuple[str, ...]


def codificar_respuestas(letras: str) -> Respuestas:
    return tuple(LETRAS_DE_RESPUESTA.index(letra) for letra in letras)


def decodificar_respuestas(respuestas: Respuestas) -> str:
    return "".join(LETRAS_DE_RESPUESTA[indice] for indice in respuestas)


def puntos_de_impacto(respuestas: Respuestas) -> int:
    return sum(respuestas)


def ejemplos_iniciales() -> list[Ejemplo]:
    return [
        Ejemplo(nivel, codificar_respuestas(letras))
        for nivel, lista in EJEMPLOS_INICIALES.items()
        for letras in lista
    ]


def distancia(a: Respuestas, b: Respuestas) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def calcular_nivel(
    respuestas: Respuestas,
    ejemplos: list[Ejemplo],
    vecinos: int = CANTIDAD_DE_VECINOS,
) -> int:
    mas_parecidos = sorted(
        (distancia(respuestas, ejemplo.respuestas), ejemplo.nivel)
        for ejemplo in ejemplos
    )[:vecinos]
    pesos = [1 / (separacion + SUAVIZADO_DE_DISTANCIA) for separacion, _ in mas_parecidos]
    nivel_ponderado = sum(
        peso * nivel for peso, (_, nivel) in zip(pesos, mas_parecidos)
    ) / sum(pesos)
    return max(NIVEL_MINIMO, min(NIVEL_MAXIMO, round(nivel_ponderado)))


def _respuestas_de_la_meta(
    respuestas: Respuestas, nivel: int, ejemplos: list[Ejemplo]
) -> Respuestas:
    candidatos = [e.respuestas for e in ejemplos if e.nivel == nivel - 1]
    sin_meta: Respuestas = (0,) * len(PREGUNTAS)
    return min(candidatos, key=lambda c: distancia(respuestas, c), default=sin_meta)


def elegir_preguntas_a_mejorar(
    respuestas: Respuestas,
    nivel: int,
    ejemplos: list[Ejemplo],
    maximo: int = MAXIMO_DE_CONSEJOS,
) -> list[Pregunta]:
    meta = _respuestas_de_la_meta(respuestas, nivel, ejemplos)
    por_prioridad = sorted(
        range(len(PREGUNTAS)),
        key=lambda i: (respuestas[i] - meta[i], respuestas[i]),
        reverse=True,
    )
    elegidas = [i for i in por_prioridad if respuestas[i] > meta[i]][:maximo]
    if not elegidas:
        elegidas = [i for i in por_prioridad if respuestas[i] > 0][:maximo]
    return [PREGUNTAS[i] for i in elegidas]


def medir_progreso(
    anterior: Intento, respuestas: Respuestas, nivel: int
) -> Progreso:
    areas = list(zip(PREGUNTAS, anterior.respuestas, respuestas))
    return Progreso(
        nivel_anterior=anterior.nivel,
        nivel_actual=nivel,
        puntos_anteriores=puntos_de_impacto(anterior.respuestas),
        puntos_actuales=puntos_de_impacto(respuestas),
        areas_mejoradas=tuple(p.nombre_corto for p, antes, ahora in areas if ahora < antes),
        areas_empeoradas=tuple(p.nombre_corto for p, antes, ahora in areas if ahora > antes),
    )


def validar_contenido() -> None:
    for posicion, pregunta in enumerate(PREGUNTAS, start=1):
        if len(pregunta.opciones) != len(LETRAS_DE_RESPUESTA):
            raise ErrorDeConfiguracion(
                f"La pregunta {posicion} debe tener {len(LETRAS_DE_RESPUESTA)} opciones."
            )
    if set(NIVELES) != set(range(NIVEL_MINIMO, NIVEL_MAXIMO + 1)):
        raise ErrorDeConfiguracion("Debe haber exactamente 10 niveles (del 1 al 10).")
    if set(EJEMPLOS_INICIALES) != set(NIVELES):
        raise ErrorDeConfiguracion("Cada nivel necesita al menos un ejemplo.")
    for nivel, lista in EJEMPLOS_INICIALES.items():
        for letras in lista:
            if len(letras) != len(PREGUNTAS) or not set(letras) <= set(LETRAS_DE_RESPUESTA):
                raise ErrorDeConfiguracion(
                    f"Ejemplo '{letras}' del nivel {nivel}: debe tener "
                    f"{len(PREGUNTAS)} letras entre A y E."
                )

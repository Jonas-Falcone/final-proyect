from __future__ import annotations

from dataclasses import dataclass

from planeta.codigos import limpiar_codigo
from planeta.contenido import Pregunta
from planeta.cuestionario import (
    Intento,
    Progreso,
    Respuestas,
    calcular_nivel,
    elegir_preguntas_a_mejorar,
    medir_progreso,
)
from planeta.repositorio import RepositorioHuella


@dataclass(frozen=True)
class CuentaExistente:
    codigo: str
    intentos: list[Intento]


@dataclass(frozen=True)
class ResultadoDeHuella:
    id_del_intento: int
    respuestas: Respuestas
    nivel: int
    preguntas_a_mejorar: list[Pregunta]
    progreso: Progreso | None
    codigo_de_cuenta: str
    es_cuenta_nueva: bool
    cantidad_de_intentos: int
    mejor_nivel: int
    ejemplos_usados: int
    ejemplos_de_personas_reales: int


def buscar_cuenta(repositorio: RepositorioHuella, texto_del_codigo: str) -> CuentaExistente | None:
    codigo = limpiar_codigo(texto_del_codigo)
    intentos = repositorio.historial(codigo)
    return CuentaExistente(codigo, intentos) if intentos else None


def completar_cuestionario(
    repositorio: RepositorioHuella,
    respuestas: Respuestas,
    codigo_de_cuenta: str | None,
) -> ResultadoDeHuella:
    ejemplos = repositorio.cargar_ejemplos()
    nivel = calcular_nivel(respuestas, ejemplos)
    intentos_anteriores = repositorio.historial(codigo_de_cuenta) if codigo_de_cuenta else []
    es_cuenta_nueva = codigo_de_cuenta is None
    codigo = codigo_de_cuenta or repositorio.crear_cuenta()
    id_del_intento = repositorio.guardar_intento(respuestas, nivel, codigo)
    return ResultadoDeHuella(
        id_del_intento=id_del_intento,
        respuestas=respuestas,
        nivel=nivel,
        preguntas_a_mejorar=elegir_preguntas_a_mejorar(respuestas, nivel, ejemplos),
        progreso=(
            medir_progreso(intentos_anteriores[-1], respuestas, nivel)
            if intentos_anteriores
            else None
        ),
        codigo_de_cuenta=codigo,
        es_cuenta_nueva=es_cuenta_nueva,
        cantidad_de_intentos=len(intentos_anteriores) + 1,
        mejor_nivel=min([intento.nivel for intento in intentos_anteriores] + [nivel]),
        ejemplos_usados=len(ejemplos),
        ejemplos_de_personas_reales=sum(e.es_de_persona_real for e in ejemplos),
    )

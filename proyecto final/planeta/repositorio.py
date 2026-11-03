from __future__ import annotations

import sqlite3
from pathlib import Path

from planeta.codigos import generar_codigo
from planeta.contenido import PREGUNTAS
from planeta.cuestionario import (
    Ejemplo,
    Intento,
    Respuestas,
    codificar_respuestas,
    decodificar_respuestas,
    ejemplos_iniciales,
)

SQL_CREAR_TABLA_DE_INTENTOS = """
    CREATE TABLE IF NOT EXISTS sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        respuestas TEXT NOT NULL,
        nivel_bot INTEGER NOT NULL,
        nivel_final INTEGER,
        confirmado INTEGER NOT NULL DEFAULT 0,
        fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        cuenta TEXT
    )
"""
SQL_CREAR_TABLA_DE_CUENTAS = """
    CREATE TABLE IF NOT EXISTS cuentas (
        codigo TEXT PRIMARY KEY,
        creada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
"""


class RepositorioHuella:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._conexion = conexion
        self._preparar_esquema()

    @classmethod
    def abrir(cls, ruta: Path | str) -> RepositorioHuella:
        return cls(sqlite3.connect(ruta))

    def cerrar(self) -> None:
        self._conexion.close()

    def crear_cuenta(self) -> str:
        while True:
            codigo = generar_codigo()
            try:
                self._conexion.execute("INSERT INTO cuentas (codigo) VALUES (?)", (codigo,))
                self._conexion.commit()
                return codigo
            except sqlite3.IntegrityError:
                continue

    def historial(self, codigo_de_cuenta: str) -> list[Intento]:
        filas = self._conexion.execute(
            "SELECT respuestas, nivel_bot FROM sesiones WHERE cuenta = ? ORDER BY id",
            (codigo_de_cuenta,),
        )
        return [
            Intento(codificar_respuestas(letras), nivel)
            for letras, nivel in filas
            if len(letras) == len(PREGUNTAS)
        ]

    def guardar_intento(
        self, respuestas: Respuestas, nivel: int, codigo_de_cuenta: str
    ) -> int:
        cursor = self._conexion.execute(
            "INSERT INTO sesiones (respuestas, nivel_bot, cuenta) VALUES (?, ?, ?)",
            (decodificar_respuestas(respuestas), nivel, codigo_de_cuenta),
        )
        self._conexion.commit()
        return cursor.lastrowid

    def confirmar_intento(self, id_del_intento: int, nivel_final: int) -> None:
        self._conexion.execute(
            "UPDATE sesiones SET nivel_final = ?, confirmado = 1 WHERE id = ?",
            (nivel_final, id_del_intento),
        )
        self._conexion.commit()

    def cargar_ejemplos(self) -> list[Ejemplo]:
        filas = self._conexion.execute(
            "SELECT nivel_final, respuestas FROM sesiones WHERE confirmado = 1"
        )
        de_personas_reales = [
            Ejemplo(nivel, codificar_respuestas(letras), es_de_persona_real=True)
            for nivel, letras in filas
            if len(letras) == len(PREGUNTAS)
        ]
        return ejemplos_iniciales() + de_personas_reales

    def _preparar_esquema(self) -> None:
        self._conexion.execute(SQL_CREAR_TABLA_DE_INTENTOS)
        columnas = [fila[1] for fila in self._conexion.execute("PRAGMA table_info(sesiones)")]
        if "cuenta" not in columnas:
            self._conexion.execute("ALTER TABLE sesiones ADD COLUMN cuenta TEXT")
        self._conexion.execute(SQL_CREAR_TABLA_DE_CUENTAS)
        self._conexion.commit()

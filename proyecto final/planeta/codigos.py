from __future__ import annotations

import secrets

ALFABETO_SIN_CONFUSIONES = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LARGO_DEL_CODIGO = 8
LARGO_DEL_PRIMER_GRUPO = 4


def generar_codigo() -> str:
    return "".join(
        secrets.choice(ALFABETO_SIN_CONFUSIONES) for _ in range(LARGO_DEL_CODIGO)
    )


def limpiar_codigo(texto: str) -> str:
    return "".join(caracter for caracter in texto.upper() if caracter.isalnum())


def formatear_codigo(codigo: str) -> str:
    return f"{codigo[:LARGO_DEL_PRIMER_GRUPO]}-{codigo[LARGO_DEL_PRIMER_GRUPO:]}"

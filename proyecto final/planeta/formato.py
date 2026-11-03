from __future__ import annotations

import unicodedata

PRIMERA_LETRA_DE_BANDERA = 0x1F1E6
LARGO_DE_BARRA_POR_DEFECTO = 10


def normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower().strip())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def emoji_bandera(codigo_pais: str) -> str:
    return "".join(
        chr(PRIMERA_LETRA_DE_BANDERA + ord(letra) - ord("A")) for letra in codigo_pais
    )


def formatear_numero(valor: float, decimales: int = 1) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def barra_de_progreso(
    valor: float, maximo: float = 100, largo: int = LARGO_DE_BARRA_POR_DEFECTO
) -> str:
    llenos = round(largo * valor / maximo)
    return "▰" * llenos + "▱" * (largo - llenos)

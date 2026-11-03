from __future__ import annotations

import os
from pathlib import Path

RAIZ_DEL_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_BASE_DE_DATOS = RAIZ_DEL_PROYECTO / "planeta.db"
RUTA_DATOS_PAISES = RAIZ_DEL_PROYECTO / "datos" / "paises.json"
RUTA_ARCHIVO_TOKEN = RAIZ_DEL_PROYECTO / "token.txt"

VARIABLE_DEL_TOKEN = "DISCORD_TOKEN"
VARIABLE_DEL_SERVIDOR = "GUILD_ID"


def leer_token() -> str | None:
    token = os.getenv(VARIABLE_DEL_TOKEN)
    if not token and RUTA_ARCHIVO_TOKEN.exists():
        token = RUTA_ARCHIVO_TOKEN.read_text(encoding="utf-8")
    if not token:
        return None
    return token.strip().strip("\"'").strip() or None


def leer_id_servidor() -> int | None:
    valor = os.getenv(VARIABLE_DEL_SERVIDOR, "").strip()
    return int(valor) if valor.isdigit() else None

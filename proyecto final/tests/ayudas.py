from __future__ import annotations

import sqlite3
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from planeta.carbono import ClienteOpenMeteo
from planeta.configuracion import RUTA_DATOS_PAISES
from planeta.paises import CatalogoPaises
from planeta.repositorio import RepositorioHuella
from planeta.servicios import Servicios


def crear_servicios_de_prueba() -> Servicios:
    return Servicios(
        repositorio=RepositorioHuella(sqlite3.connect(":memory:")),
        catalogo=CatalogoPaises.desde_archivo(RUTA_DATOS_PAISES),
        clima=ClienteOpenMeteo(),
    )


def crear_interaccion_falsa() -> MagicMock:
    interaccion = MagicMock()
    interaccion.response.edit_message = AsyncMock()
    interaccion.response.send_message = AsyncMock()
    interaccion.response.send_modal = AsyncMock()
    interaccion.response.defer = AsyncMock()
    interaccion.followup.send = AsyncMock()
    return interaccion


def con_valores_elegidos(componente, valores: list[str]):
    return patch.object(
        type(componente), "values", new_callable=PropertyMock, return_value=valores
    )

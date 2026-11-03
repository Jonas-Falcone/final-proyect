from __future__ import annotations

from dataclasses import dataclass

from planeta.carbono import ClienteOpenMeteo
from planeta.configuracion import RUTA_BASE_DE_DATOS, RUTA_DATOS_PAISES
from planeta.errores import ErrorDeConfiguracion
from planeta.paises import CatalogoPaises
from planeta.repositorio import RepositorioHuella


@dataclass(frozen=True)
class Servicios:
    repositorio: RepositorioHuella
    catalogo: CatalogoPaises
    clima: ClienteOpenMeteo


def crear_servicios() -> Servicios:
    try:
        catalogo = CatalogoPaises.desde_archivo(RUTA_DATOS_PAISES)
    except FileNotFoundError as error:
        raise ErrorDeConfiguracion(
            f"Falta el archivo {RUTA_DATOS_PAISES.name} dentro de la carpeta "
            f"'{RUTA_DATOS_PAISES.parent.name}'."
        ) from error
    return Servicios(
        repositorio=RepositorioHuella.abrir(RUTA_BASE_DE_DATOS),
        catalogo=catalogo,
        clima=ClienteOpenMeteo(),
    )

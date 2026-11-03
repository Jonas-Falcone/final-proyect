from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum

import aiohttp

from planeta.errores import ErrorDeServicioExterno
from planeta.formato import normalizar

URL_BUSQUEDA_DE_LUGARES = "https://geocoding-api.open-meteo.com/v1/search"
URL_CLIMA = "https://api.open-meteo.com/v1/forecast"
URL_CALIDAD_DEL_AIRE = "https://air-quality-api.open-meteo.com/v1/air-quality"

VARIABLES_DE_CLIMA_ACTUAL = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "precipitation,weather_code,wind_speed_10m"
)
VARIABLES_DE_CLIMA_DEL_DIA = "temperature_2m_max,temperature_2m_min"
VARIABLES_DE_AIRE = "us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone"
NIVELES_ADMINISTRATIVOS = ("admin1", "admin2", "admin3", "admin4")

MAXIMO_DE_LUGARES_POR_BUSQUEDA = 100
IDIOMA_DE_LOS_RESULTADOS = "es"
SEGUNDOS_DE_ESPERA_MAXIMA = 12
LARGO_MINIMO_PARA_COMPARAR_ZONAS = 3
UMBRAL_POR_ENCIMA_DEL_PROMEDIO = 1.2
UMBRAL_POR_DEBAJO_DEL_PROMEDIO = 0.8


class NivelDeAire(Enum):
    BUENA = "buena"
    MODERADA = "moderada"
    DANINA_PARA_SENSIBLES = "danina_para_sensibles"
    DANINA = "danina"
    MUY_DANINA = "muy_danina"
    PELIGROSA = "peligrosa"


LIMITES_DE_AIRE = (
    (50, NivelDeAire.BUENA),
    (100, NivelDeAire.MODERADA),
    (150, NivelDeAire.DANINA_PARA_SENSIBLES),
    (200, NivelDeAire.DANINA),
    (300, NivelDeAire.MUY_DANINA),
)


class ComparacionConElPromedio(Enum):
    POR_ENCIMA = "por_encima"
    PARECIDO = "parecido"
    POR_DEBAJO = "por_debajo"


@dataclass(frozen=True)
class Lugar:
    nombre: str
    latitud: float
    longitud: float
    provincia: str | None
    zonas: tuple[str, ...]
    poblacion: int | None


@dataclass(frozen=True)
class ClimaActual:
    codigo_de_clima: int | None
    temperatura: float | None
    sensacion_termica: float | None
    humedad: float | None
    viento: float | None
    precipitacion: float | None
    minima_del_dia: float | None
    maxima_del_dia: float | None

    @property
    def tiene_datos(self) -> bool:
        return self.temperatura is not None or self.codigo_de_clima is not None


@dataclass(frozen=True)
class CalidadAire:
    indice: float | None
    particulas_2_5: float | None
    particulas_10: float | None
    dioxido_de_nitrogeno: float | None
    ozono: float | None


@dataclass(frozen=True)
class ConsultaCiudad:
    lugar: Lugar
    provincia_coincide: bool
    clima: ClimaActual | None
    aire: CalidadAire | None


def clasificar_aire(indice: float) -> NivelDeAire:
    for limite, nivel in LIMITES_DE_AIRE:
        if indice <= limite:
            return nivel
    return NivelDeAire.PELIGROSA


def comparar_con_el_promedio(
    toneladas_por_persona: float, promedio_mundial: float
) -> ComparacionConElPromedio:
    proporcion = toneladas_por_persona / promedio_mundial
    if proporcion > UMBRAL_POR_ENCIMA_DEL_PROMEDIO:
        return ComparacionConElPromedio.POR_ENCIMA
    if proporcion < UMBRAL_POR_DEBAJO_DEL_PROMEDIO:
        return ComparacionConElPromedio.POR_DEBAJO
    return ComparacionConElPromedio.PARECIDO


def estimar_emisiones_de_la_ciudad(
    toneladas_por_persona: float, poblacion: int | None
) -> float | None:
    return toneladas_por_persona * poblacion if poblacion else None


def interpretar_lugares(datos: dict, codigo_pais: str) -> list[Lugar]:
    lugares = []
    for resultado in datos.get("results", []):
        if (resultado.get("country_code") or "").upper() != codigo_pais:
            continue
        lugares.append(
            Lugar(
                nombre=resultado.get("name") or "",
                latitud=resultado["latitude"],
                longitud=resultado["longitude"],
                provincia=resultado.get("admin1"),
                zonas=tuple(
                    resultado[nivel] for nivel in NIVELES_ADMINISTRATIVOS if resultado.get(nivel)
                ),
                poblacion=resultado.get("population") or None,
            )
        )
    return lugares


def interpretar_clima(datos: dict) -> ClimaActual:
    actual = datos.get("current") or {}
    del_dia = datos.get("daily") or {}
    return ClimaActual(
        codigo_de_clima=actual.get("weather_code"),
        temperatura=actual.get("temperature_2m"),
        sensacion_termica=actual.get("apparent_temperature"),
        humedad=actual.get("relative_humidity_2m"),
        viento=actual.get("wind_speed_10m"),
        precipitacion=actual.get("precipitation"),
        minima_del_dia=_primer_valor(del_dia.get("temperature_2m_min")),
        maxima_del_dia=_primer_valor(del_dia.get("temperature_2m_max")),
    )


def interpretar_aire(datos: dict) -> CalidadAire:
    actual = datos.get("current") or {}
    return CalidadAire(
        indice=actual.get("us_aqi"),
        particulas_2_5=actual.get("pm2_5"),
        particulas_10=actual.get("pm10"),
        dioxido_de_nitrogeno=actual.get("nitrogen_dioxide"),
        ozono=actual.get("ozone"),
    )


def elegir_lugar(lugares: list[Lugar], provincia: str) -> tuple[Lugar, bool]:
    provincia_normalizada = normalizar(provincia)
    coincidentes = [
        lugar for lugar in lugares if _coincide_con_la_provincia(lugar, provincia_normalizada)
    ]
    elegidos = coincidentes or lugares
    return max(elegidos, key=lambda lugar: lugar.poblacion or 0), bool(coincidentes)


class ClienteOpenMeteo:
    def __init__(self) -> None:
        self._sesion: aiohttp.ClientSession | None = None

    async def buscar_lugares(self, ciudad: str, codigo_pais: str) -> list[Lugar]:
        datos = await self._pedir_json(
            URL_BUSQUEDA_DE_LUGARES,
            {
                "name": ciudad,
                "count": MAXIMO_DE_LUGARES_POR_BUSQUEDA,
                "language": IDIOMA_DE_LOS_RESULTADOS,
                "format": "json",
            },
        )
        return interpretar_lugares(datos, codigo_pais)

    async def obtener_clima(self, lugar: Lugar) -> ClimaActual:
        datos = await self._pedir_json(
            URL_CLIMA,
            {
                **_coordenadas(lugar),
                "forecast_days": 1,
                "current": VARIABLES_DE_CLIMA_ACTUAL,
                "daily": VARIABLES_DE_CLIMA_DEL_DIA,
            },
        )
        return interpretar_clima(datos)

    async def obtener_aire(self, lugar: Lugar) -> CalidadAire:
        datos = await self._pedir_json(
            URL_CALIDAD_DEL_AIRE,
            {**_coordenadas(lugar), "current": VARIABLES_DE_AIRE},
        )
        return interpretar_aire(datos)

    async def cerrar(self) -> None:
        if self._sesion is not None and not self._sesion.closed:
            await self._sesion.close()

    async def _pedir_json(self, url: str, parametros: dict) -> dict:
        sesion = self._sesion_activa()
        try:
            async with sesion.get(
                url, params={clave: str(valor) for clave, valor in parametros.items()}
            ) as respuesta:
                respuesta.raise_for_status()
                return await respuesta.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
            raise ErrorDeServicioExterno(f"Falló la consulta a {url}") from error

    def _sesion_activa(self) -> aiohttp.ClientSession:
        if self._sesion is None or self._sesion.closed:
            self._sesion = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=SEGUNDOS_DE_ESPERA_MAXIMA)
            )
        return self._sesion


async def consultar_ciudad(
    cliente: ClienteOpenMeteo, codigo_pais: str, provincia: str, ciudad: str
) -> ConsultaCiudad | None:
    lugares = await cliente.buscar_lugares(ciudad, codigo_pais)
    if not lugares:
        return None
    lugar, provincia_coincide = elegir_lugar(lugares, provincia)
    clima, aire = await asyncio.gather(
        cliente.obtener_clima(lugar),
        cliente.obtener_aire(lugar),
        return_exceptions=True,
    )
    return ConsultaCiudad(
        lugar=lugar,
        provincia_coincide=provincia_coincide,
        clima=_valor_o_nada(clima),
        aire=_valor_o_nada(aire),
    )


def _coordenadas(lugar: Lugar) -> dict:
    return {"latitude": lugar.latitud, "longitude": lugar.longitud, "timezone": "auto"}


def _primer_valor(valores: list | None):
    return valores[0] if valores else None


def _coincide_con_la_provincia(lugar: Lugar, provincia_normalizada: str) -> bool:
    if len(provincia_normalizada) < LARGO_MINIMO_PARA_COMPARAR_ZONAS:
        return False
    for zona in lugar.zonas:
        zona_normalizada = normalizar(zona)
        if len(zona_normalizada) >= LARGO_MINIMO_PARA_COMPARAR_ZONAS and (
            provincia_normalizada in zona_normalizada
            or zona_normalizada in provincia_normalizada
        ):
            return True
    return False


def _valor_o_nada(resultado):
    if isinstance(resultado, ErrorDeServicioExterno):
        return None
    if isinstance(resultado, BaseException):
        raise resultado
    return resultado

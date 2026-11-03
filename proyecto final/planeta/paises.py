from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from planeta.formato import normalizar

TOTAL_DE_PUESTOS_DEL_RANKING = 67
PUNTAJE_MINIMO_PARA_BIEN = 64.3
PUNTAJE_MINIMO_PARA_REGULAR = 55
PUNTAJE_MINIMO_PARA_MAL = 45
MAXIMO_DE_SUGERENCIAS = 25


class Valoracion(Enum):
    BIEN = "bien"
    REGULAR = "regular"
    MAL = "mal"
    MUY_MAL = "muy_mal"


@dataclass(frozen=True)
class RankingClimatico:
    puesto: int
    puntaje: float
    calificaciones: dict[str, str]


@dataclass(frozen=True)
class Emisiones:
    toneladas_por_persona: float
    anio: int
    puesto: int | None
    total_de_paises: int | None


@dataclass(frozen=True)
class Pais:
    codigo: str
    nombre: str
    nombre_en_ingles: str
    ranking: RankingClimatico | None
    emisiones: Emisiones | None


def valorar_puntaje(puntaje: float) -> Valoracion:
    if puntaje >= PUNTAJE_MINIMO_PARA_BIEN:
        return Valoracion.BIEN
    if puntaje >= PUNTAJE_MINIMO_PARA_REGULAR:
        return Valoracion.REGULAR
    if puntaje >= PUNTAJE_MINIMO_PARA_MAL:
        return Valoracion.MAL
    return Valoracion.MUY_MAL


class CatalogoPaises:
    def __init__(self, paises: list[Pais], promedio_mundial_de_emisiones: float) -> None:
        self.promedio_mundial_de_emisiones = promedio_mundial_de_emisiones
        self._paises = {pais.codigo: pais for pais in paises}
        self._claves_de_busqueda = {
            pais.codigo: (normalizar(pais.nombre), normalizar(pais.nombre_en_ingles))
            for pais in paises
        }

    @classmethod
    def desde_archivo(cls, ruta: Path) -> CatalogoPaises:
        with ruta.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        rankings = {
            codigo: RankingClimatico(
                puesto=ranking["puesto"],
                puntaje=ranking["puntaje"],
                calificaciones=ranking["categorias"],
            )
            for codigo, ranking in datos["ccpi"].items()
        }
        paises = [
            _construir_pais(codigo, entrada, rankings.get(codigo))
            for codigo, entrada in datos["paises"].items()
        ]
        return cls(paises, datos["meta"]["mundo_co2_pc"])

    def obtener(self, codigo: str) -> Pais:
        return self._paises[codigo]

    def __len__(self) -> int:
        return len(self._paises)

    def __iter__(self):
        return iter(self._paises.values())

    def resolver(self, texto: str) -> Pais | None:
        clave = normalizar(texto)
        if not clave:
            return None
        for codigo, (nombre, nombre_en_ingles) in self._claves_de_busqueda.items():
            if clave in (nombre, nombre_en_ingles):
                return self._paises[codigo]
        codigo_directo = texto.strip().upper()
        if codigo_directo in self._paises:
            return self._paises[codigo_directo]
        parecidos = [
            codigo
            for codigo, (nombre, nombre_en_ingles) in self._claves_de_busqueda.items()
            if clave in nombre or clave in nombre_en_ingles
        ]
        return self._paises[parecidos[0]] if len(parecidos) == 1 else None

    def buscar(
        self,
        texto: str,
        solo_con_emisiones: bool = False,
        limite: int = MAXIMO_DE_SUGERENCIAS,
    ) -> list[Pais]:
        clave = normalizar(texto)
        coincidencias = []
        for codigo, pais in self._paises.items():
            if solo_con_emisiones and pais.emisiones is None:
                continue
            nombre, nombre_en_ingles = self._claves_de_busqueda[codigo]
            if not clave or nombre.startswith(clave) or nombre_en_ingles.startswith(clave):
                coincidencias.append((0, nombre, codigo, pais))
            elif clave in nombre or clave in nombre_en_ingles:
                coincidencias.append((1, nombre, codigo, pais))
        coincidencias.sort(key=lambda c: c[:3])
        return [pais for *_, pais in coincidencias[:limite]]


def _construir_pais(codigo: str, entrada: dict, ranking: RankingClimatico | None) -> Pais:
    emisiones = None
    if "co2_pc" in entrada:
        emisiones = Emisiones(
            toneladas_por_persona=entrada["co2_pc"],
            anio=entrada["anio"],
            puesto=entrada.get("puesto_co2"),
            total_de_paises=entrada.get("de_co2"),
        )
    return Pais(
        codigo=codigo,
        nombre=entrada.get("nombre_es") or entrada["es"],
        nombre_en_ingles=entrada["en"],
        ranking=ranking,
        emisiones=emisiones,
    )

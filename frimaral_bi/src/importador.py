"""
=================================================================================
importador.py — Lector de archivos XLSB del MGAP
=================================================================================
Lee el archivo XLSB del MGAP de forma eficiente y detectando estructura.

Responsabilidades:
    • Lectura del archivo XLSB (nunca modifica el original)
    • Detección automática de la hoja correcta
    • Detección de columnas (mapeo con COLUMNAS_MGAP conocidas)
    • Detección de tipos de datos (inferencia por muestra)
    • Registro de metadata (filas, columnas, hojas)
    • Soporte para archivos grandes (chunking con pandas)

No modifica nunca el archivo original.

Clase principal:
    XLSBImporter  — lector con detección automática
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Generator
from datetime import datetime

import pandas as pd

from config import (
    COLUMNAS_MGAP, COLUMNA_POR_NOMBRE, CHUNK_SIZE,
    HEADER_SAMPLE_SIZE, RE_INVISIBLES,
)
from logger import ImportLogger


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO DE LA IMPORTACIÓN
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ImportResult:
    """Resultado de la lectura del XLSB."""
    df             : pd.DataFrame
    hoja_usada     : str
    columnas_originales  : list[str]
    columnas_mapeadas    : dict[str, str]   # original → normalizado
    columnas_sin_mapear  : list[str]        # originales sin match en config
    filas_total    : int
    tiempo_lectura : float
    detectadas     : list[str]              # hojas encontradas
    tipo_detectado : str                   # "xlsb" | "xlsx" | "xls"


# ─────────────────────────────────────────────────────────────────────────────
# XLSB IMPORTER
# ─────────────────────────────────────────────────────────────────────────────

class XLSBImporter:
    """
    Lector profesional de archivos XLSB del MGAP.

    Uso:
        importer = XLSBImporter("archivo.xlsb", logger)
        resultado = importer.read()
        df = resultado.df
    """

    # Peso máximo del archivo para considerar lectura completa en memoria (MB)
    MAX_FILE_SIZE_MB = 500

    def __init__(self, ruta: str | Path, logger: ImportLogger):
        self.ruta    = Path(ruta).resolve()
        self.logger  = logger
        self._result: Optional[ImportResult] = None

        if not self.ruta.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {self.ruta}")

        self.logger.info(f"Archivo: {self.ruta}")
        self.logger.info(f"Tamaño : {self.ruta.stat().st_size / 1024 / 1024:.2f} MB")

    # ─── Lectura principal ────────────────────────────────────────────────

    def read(self, hoja: Optional[str] = None) -> ImportResult:
        """
        Lee el archivo XLSB y retorna un DataFrame con los datos.

        Args:
            hoja: Nombre de la hoja a leer. Si es None, detecta automáticamente.

        Returns:
            ImportResult con el DataFrame y metadata.
        """
        inicio = time.time()
        self.logger.separator()
        self.logger.info("ETAPA 1 — Lectura del archivo")

        # 1. Detectar tipo de archivo
        tipo = self._detectar_tipo()
        self.logger.info(f"Tipo detectado: {tipo}")

        # 2. Leer hojas disponibles
        hojas = self._leer_hojas(tipo)
        self.logger.info(f"Hojas encontradas: {len(hojas)} → {hojas}")

        # 3. Seleccionar hoja
        hoja_sel = self._seleccionar_hoja(hojas, hoja)
        self.logger.set_hoja(hoja_sel)
        self.logger.info(f"Hoja seleccionada: '{hoja_sel}'")

        # 4. Leer datos de la hoja seleccionada
        df = self._leer_hoja_dataframe(hoja_sel, tipo)
        self.logger.info(f"Filas leídas (raw): {len(df):,}")
        self.logger.info(f"Columnas leídas   : {len(df.columns)}")

        # 5. Mapeo de columnas
        mapa, sin_mapear = self._mapear_columnas(list(df.columns))
        self.logger.info(f"Columnas mapeadas : {len(mapa)}")
        if sin_mapear:
            self.logger.warning(f"Columnas sin mapear: {sin_mapear}")
        self.logger.set_columnas(list(df.columns))

        # 6. Renombrar columnas al nombre normalizado
        df = df.rename(columns=mapa)

        duracion = time.time() - inicio
        self.logger.success(f"Lectura completada en {duracion:.2f}s")

        self._result = ImportResult(
            df                 = df,
            hoja_usada         = hoja_sel,
            columnas_originales= list(df.columns),
            columnas_mapeadas  = mapa,
            columnas_sin_mapear= sin_mapear,
            filas_total        = len(df),
            tiempo_lectura     = duracion,
            detectadas         = hojas,
            tipo_detectado     = tipo,
        )
        return self._result

    # ─── Detección del tipo de archivo ───────────────────────────────────

    def _detectar_tipo(self) -> str:
        """Infiere el tipo de archivo por la extensión y contenido."""
        ext = self.ruta.suffix.lower()
        if ext == ".xlsb":
            return "xlsb"
        elif ext == ".xlsx":
            return "xlsx"
        elif ext == ".xls":
            return "xls"
        else:
            # Intentar abrir como XLSB primero
            return "xlsb"

    # ─── Leer lista de hojas ──────────────────────────────────────────────

    def _leer_hojas(self, tipo: str) -> list[str]:
        """Retorna la lista de nombres de hojas en el archivo."""
        self.logger.info(f"Detectando hojas ({tipo})...")
        try:
            if tipo == "xlsb":
                xl = pd.ExcelFile(self.ruta, engine="pyxlsb")
            else:
                xl = pd.ExcelFile(self.ruta, engine="openpyxl")
            hojas = xl.sheet_names
            for h in hojas:
                self.logger.add_hoja(h)
            return hojas
        except Exception as e:
            self.logger.error(f"No se pudieron leer las hojas: {e}")
            raise

    # ─── Seleccionar hoja ─────────────────────────────────────────────────

    def _seleccionar_hoja(self, hojas: list[str], sugerida: Optional[str]) -> str:
        """
        Selecciona la mejor hoja para importar.

        Estrategia:
            1. Si se pasó 'sugerida' y existe, usarla.
            2. Buscar una hoja que contenga datos (nombre similar a "MOVIMIENTOS",
               "ESTABLECIMIENTOS", "MGAP", o similar).
            3. Usar la primera hoja que no esté vacía.
            4. Caer a la primera hoja.
        """
        if sugerida and sugerida in hojas:
            return sugerida

        # Patrones que indican la hoja de datos principal
        patrones = ["movim", "estable", "mgap", "carga", "datos",
                    "produ", "certif", "frigo"]

        for hoja in hojas:
            hoja_lower = hoja.lower()
            if any(p in hoja_lower for p in patrones):
                self.logger.info(f"Hoja seleccionada por patrón: '{hoja}'")
                return hoja

        # Buscar la hoja con más filas (proxy de contenido)
        mejor_hoja  = hojas[0] if hojas else ""
        max_filas   = 0

        for hoja in hojas:
            try:
                if self.ruta.suffix.lower() == ".xlsb":
                    engine = "pyxlsb"
                else:
                    engine = "openpyxl"
                temp = pd.read_excel(
                    self.ruta, sheet_name=hoja, engine=engine,
                    nrows=5
                )
                if len(temp) > max_filas:
                    max_filas = len(temp)
                    mejor_hoja = hoja
            except Exception:
                pass

        self.logger.warning(
            f"No se detectó hoja obvia. "
            f"Seleccionando '{mejor_hoja}' ({max_filas} filas sample)"
        )
        return mejor_hoja

    # ─── Leer DataFrame ───────────────────────────────────────────────────

    def _leer_hoja_dataframe(self, hoja: str, tipo: str) -> pd.DataFrame:
        """Lee la hoja completa como DataFrame de pandas."""
        engine = "pyxlsb" if tipo == "xlsb" else "openpyxl"

        file_size_mb = self.ruta.stat().st_size / 1024 / 1024

        if file_size_mb > self.MAX_FILE_SIZE_MB:
            self.logger.warning(
                f"Archivo grande ({file_size_mb:.0f} MB) — "
                f"usando chunksize={CHUNK_SIZE:,}"
            )
            # Lectura por chunks (concatenar al final)
            chunks: list[pd.DataFrame] = []
            for chunk in pd.read_excel(
                self.ruta, sheet_name=hoja, engine=engine,
                chunksize=CHUNK_SIZE,
            ):
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_excel(self.ruta, sheet_name=hoja, engine=engine)

        # Limpieza mínima de caracteres invisibles en nombres de columna
        df.columns = [
            str(c).translate({ord(c2): None for c2 in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f'})
            for c in df.columns
        ]
        # Strip de nombres de columna
        df.columns = df.columns.str.strip()

        # Limpiar filas que sean puras NaN
        df = df.dropna(how="all").reset_index(drop=True)

        return df

    # ─── Mapeo de columnas ────────────────────────────────────────────────

    def _mapear_columnas(
        self, columnas_originales: list[str]
    ) -> tuple[dict[str, str], list[str]]:
        """
        Mapea nombres de columna originales a nombres normalizados.

        Estrategia de fuzzy matching:
            1. Match exacto (después de strip y lower)
            2. Match sin tildes
            3. Match por substring
            4. Lo que no matchea → sin_mapear

        Returns:
            (mapa {original: normalizado}, lista_sin_mapear)
        """
        import unicodedata

        mapa       : dict[str, str] = {}
        sin_mapear : list[str]      = []
        # Crear índice para búsqueda
        cols_por_nombre: dict = dict(COLUMNA_POR_NOMBRE)

        for col_original in columnas_originales:
            col_stripped = col_original.strip()
            col_lower    = col_stripped.lower()

            # Normalizar para búsqueda
            col_norm = self._normalizar_nombre(col_original)

            matched = False

            # 1. Match exacto
            if col_original in COLUMNA_POR_NOMBRE:
                mapa[col_original] = COLUMNA_POR_NOMBRE[col_original].nombre_normalizado
                matched = True

            # 2. Match sin tildes exacto
            elif col_norm in {
                self._normalizar_nombre(k): v.nombre_normalizado
                for k, v in COLUMNA_POR_NOMBRE.items()
            }:
                for k, v in COLUMNA_POR_NOMBRE.items():
                    if self._normalizar_nombre(k) == col_norm:
                        mapa[col_original] = v.nombre_normalizado
                        matched = True
                        break

            # 3. Match por substring
            elif not matched:
                for nombre_original, col_def in COLUMNA_POR_NOMBRE.items():
                    nom_norm = self._normalizar_nombre(nombre_original)
                    if col_norm and nom_norm and (
                        col_norm in nom_norm or nom_norm in col_norm
                    ):
                        mapa[col_original] = col_def.nombre_normalizado
                        matched = True
                        break

            if not matched:
                sin_mapear.append(col_original)

        return mapa, sin_mapear

    @staticmethod
    def _normalizar_nombre(s: str) -> str:
        """Normaliza un nombre de columna para búsqueda fuzzy."""
        import unicodedata
        s = s.strip().lower()
        # Quitar tildes
        s = "".join(
            c for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )
        # Caracteres especiales a espacio
        s = "".join(c if c.isalnum() or c in " _-" else " " for c in s)
        # Espacios múltiples a uno
        import re
        s = re.sub(r" {2,}", " ", s).strip()
        return s

    # ─── Detección de tipos por muestra ──────────────────────────────────

    def detectar_tipos_por_muestra(self, df: pd.DataFrame) -> dict[str, str]:
        """
        Infiere el tipo de dato de cada columna usando una muestra.

        Returns:
            dict {columna: "fecha" | "numero" | "texto"}
        """
        sample = df.head(HEADER_SAMPLE_SIZE)
        resultados: dict[str, str] = {}

        for col in df.columns:
            if col not in sample.columns:
                resultados[col] = "texto"
                continue

            # Detectar fechas
            if sample[col].apply(lambda x: self._es_fecha(x)).mean() > 0.8:
                resultados[col] = "fecha"
            # Detectar números
            elif sample[col].apply(lambda x: self._es_numerico(x)).mean() > 0.8:
                resultados[col] = "numero"
            else:
                resultados[col] = "texto"

        return resultados

    @staticmethod
    def _es_fecha(x) -> bool:
        """Detecta si un valor parece una fecha."""
        if pd.isna(x):
            return False
        s = str(x).strip()
        # Patrones comunes: dd/mm/yyyy, yyyy-mm-dd, dd-mm-yyyy
        import re
        return bool(re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", s))

    @staticmethod
    def _es_numerico(x) -> bool:
        """Detecta si un valor es numérico (int o float)."""
        if pd.isna(x):
            return False
        try:
            float(str(x).replace(",", "").replace(".", ""))
            return True
        except (ValueError, TypeError):
            return False

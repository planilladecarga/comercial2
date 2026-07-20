"""
=================================================================================
normalizador.py — Normalizador de datos del MGAP
=================================================================================
Aplica reglas de limpieza y transformación a los datos validados.
NUNCA modifica el archivo original — opera sobre una copia del DataFrame.

Transformaciones aplicadas:
    1. Limpieza de texto (espacios dobles, invisibles, mayúsculas)
    2. Separación de "Solo a Depósitos" en campo booleano
    3. Normalización de fechas a formato ISO
    4. Normalización de pesos (kilos) a float
    5. Campos calculados: año, mes, trimestre, semana ISO
    6. Campos booleanos derivados
    7. Unificación de nombres de empresas (para catálogo)

Uso:
    norm = DataNormalizer(df, logger)
    df_norm = norm.normalize()
"""

from __future__ import annotations

import re
import unicodedata
import pandas as pd
from datetime import datetime, date
from typing import Optional

from config import RE_INVISIBLES, RE_ESPACIOS_DOBLES
from logger import ImportLogger


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZER
# ─────────────────────────────────────────────────────────────────────────────

class DataNormalizer:
    """
    Normalizador de datos del MGAP.

    Trabaja sobre una copia del DataFrame.
    Registra cada transformación aplicada en el log.

    Uso:
        normalizer = DataNormalizer(df, logger)
        df_norm = normalizer.normalize()
    """

    def __init__(self, df: pd.DataFrame, logger: ImportLogger):
        self.df_in  = df.copy()
        self.df_out: Optional[pd.DataFrame] = None
        self.logger = logger

    # ─── Normalización completa ────────────────────────────────────────────

    def normalize(self) -> pd.DataFrame:
        """Ejecuta todas las normalizaciones en orden."""
        self.logger.separator()
        self.logger.info("ETAPA 3 — Normalización de datos")
        self.logger.info(f"Filas a normalizar: {len(self.df_in):,}")

        df = self.df_in

        # 1. Limpiar espacios y caracteres invisibles (todas las columnas texto)
        df = self._limpiar_texto(df)

        # 2. Mayúsculas consistentes
        df = self._normalizar_mayusculas(df)

        # 3. Normalizar fechas
        df = self._normalizar_fechas(df)

        # 4. Normalizar kilos y temperatura (numéricos)
        df = self._normalizar_numericos(df)

        # 5. Extraer "Solo a Depósitos" → booleano + país limpio
        df = self._extraer_solo_depositos(df)

        # 6. Campos calculados de calendario
        df = self._calcular_campos_calendario(df)

        # 7. Normalizar RUC
        df = self._normalizar_ruc(df)

        # 8. Crear campo normalizado para empresas (sin SA/SRL/etc.)
        df = self._crear_nombre_unificado(df)

        # 9. Clasificar tipo de movimiento
        df = self._clasificar_movimiento(df)

        # 10. Agregar IDs temporales (serán reemplazados por la BD)
        df = self._agregar_ids_temp(df)

        self.df_out = df
        self.logger.success(
            f"Normalización completada — {len(df):,} filas, "
            f"{len(df.columns)} columnas"
        )
        return df

    # ─── 1. Limpieza de texto ─────────────────────────────────────────────

    def _limpiar_texto(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina espacios dobles y caracteres invisibles de todas las cols texto."""
        columnas_texto = df.select_dtypes(include=["object"]).columns

        for col in columnas_texto:
            antes = df[col].astype(str).head()
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(RE_INVISIBLES, "", regex=True)
                .str.replace(RE_ESPACIOS_DOBLES, " ", regex=True)
                .replace({"nan": "", "None": "", "NA": ""})
            )
            despues = df[col].astype(str).head()
            changed = (antes != despues).sum()
            if changed > 0:
                self.logger.info(f"  Limpieza '{col}': {changed} celdas modificadas")

        return df

    # ─── 2. Mayúsculas ────────────────────────────────────────────────────

    def _normalizar_mayusculas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica UPPER a todas las columnas de texto relevantes."""
        cols_mayus = [
            "nombre_establecimiento", "departamento", "localidad",
            "tipo_establecimiento", "nombre_productor", "empresa",
            "destino", "tipo_movimiento", "producto",
        ]
        for col in cols_mayus:
            if col in df.columns:
                df[col] = df[col].str.upper().str.strip()

        return df

    # ─── 3. Fechas ───────────────────────────────────────────────────────

    def _normalizar_fechas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte la columna fecha_movimiento a formato ISO (YYYY-MM-DD).
        Crea columna auxiliar _fecha_raw antes de sobrescribir.
        """
        if "fecha_movimiento" not in df.columns:
            return df

        # Guardar raw
        df["_fecha_raw"] = df["fecha_movimiento"]

        # Parsear y convertir a ISO
        fechas_iso: list[str] = []
        parseadas  = 0

        for val in df["fecha_movimiento"]:
            dt = self._parsear_fecha(val)
            if dt:
                fechas_iso.append(dt.strftime("%Y-%m-%d"))
                parseadas += 1
            else:
                fechas_iso.append("")

        df["fecha_movimiento"] = fechas_iso
        self.logger.info(f"  Fechas normalizadas: {parseadas:,}/{len(df):,}")

        return df

    @staticmethod
    def _parsear_fecha(val) -> Optional[date]:
        if pd.isna(val):
            return None
        if isinstance(val, (datetime, pd.Timestamp)):
            return val.date()
        s = str(val).strip()
        patrones = [
            (r"(\d{1,2})/(\d{1,2})/(\d{4})", "%d/%m/%Y"),
            (r"(\d{1,2})-(\d{1,2})-(\d{4})", "%d-%m-%Y"),
            (r"(\d{4})-(\d{1,2})-(\d{1,2})",  "%Y-%m-%d"),
        ]
        for patron, fmt in patrones:
            m = re.match(patron, s)
            if m:
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return None

    # ─── 4. Numéricos (kilos, temperatura) ──────────────────────────────

    def _normalizar_numericos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convierte kilos y temperatura a float."""
        # Kilos netos
        if "kilos_netos" in df.columns:
            df["kilos_netos"] = (
                df["kilos_netos"]
                .astype(str)
                .str.strip()
                .str.replace(",", ".", regex=False)
                .replace(["", "nan", "None"], None)
            )
            df["kilos_netos"] = pd.to_numeric(df["kilos_netos"], errors="coerce")

        # Temperatura
        if "temperatura" in df.columns:
            df["temperatura"] = (
                df["temperatura"]
                .astype(str)
                .str.strip()
                .str.replace(",", ".", regex=False)
                .replace(["", "nan", "None"], None)
            )
            df["temperatura"] = pd.to_numeric(df["temperatura"], errors="coerce")

        return df

    # ─── 5. Extraer "Solo a Depósitos" ──────────────────────────────────

    def _extraer_solo_depositos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detecta la leyenda '(Solo a Depósitos)' en el campo destino o país
        y la separa en:
            - destino_pais  : nombre del país limpio
            - solo_deposito : True/False
        """
        # Crear columna booleana
        df["solo_deposito"] = False

        for col in ["destino", "empresa"]:
            if col not in df.columns:
                continue
            mask = df[col].str.contains(
                r"\(SOLO\s*A\s*DE[PÓ]SITOS\)", case=False, na=False, regex=True
            )
            if mask.any():
                df.loc[mask, "solo_deposito"] = True
                # Limpiar la leyenda del texto original
                df[col] = df[col].str.replace(
                    r"\s*\(SOLO\s*A\s*DE[PÓ]SITOS\)\s*", "", case=False,
                    regex=True, inplace=False
                ).str.strip()
                count = mask.sum()
                self.logger.info(
                    f"  '{col}': {count} registros marcados como 'solo_deposito'"
                )

        return df

    # ─── 6. Campos de calendario ────────────────────────────────────────

    def _calcular_campos_calendario(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega columnas calculadas a partir de fecha_movimiento:
            anio, mes, nombre_mes, trimestre, semestre, semana_iso
        """
        if "fecha_movimiento" not in df.columns:
            return df

        # Convertir string ISO a datetime
        fechas_dt = pd.to_datetime(df["fecha_movimiento"], errors="coerce")

        df["anio"]         = fechas_dt.dt.year
        df["mes"]          = fechas_dt.dt.month
        df["nombre_mes"]   = fechas_dt.dt.strftime("%B")
        df["trimestre"]    = fechas_dt.dt.quarter
        df["semestre"]     = ((fechas_dt.dt.month - 1) // 6) + 1
        df["semana_iso"]   = fechas_dt.dt.isocalendar().week

        # Día de la semana (1=Lunes, 7=Domingo)
        df["dia_semana"]   = fechas_dt.dt.dayofweek + 1
        df["dia_nombre"]   = fechas_dt.dt.day_name(locale="es_ES")

        self.logger.info(
            f"  Calendario: {df['anio'].notna().sum():,} fechas procesadas"
        )

        return df

    # ─── 7. Normalizar RUC ───────────────────────────────────────────────

    def _normalizar_ruc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia el RUC: elimina puntos, guiones, espacios."""
        if "ruc" not in df.columns:
            return df

        df["ruc"] = (
            df["ruc"]
            .astype(str)
            .str.strip()
            .str.replace(".", "", regex=False)
            .str.replace("-", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.upper()
        )
        return df

    # ─── 8. Nombre unificado para empresas ───────────────────────────────

    def _crear_nombre_unificado(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea columna 'empresa_unificada' con nombre limpio de empresa
        para ayudar a detectar duplicados en el catálogo:
            - Elimina SA, S.A., SRL, S.R.L., LTDA, LTDA., etc.
            - Elimina espacios múltiples
        """
        if "empresa" not in df.columns:
            return df

        def unificar(nombre: str) -> str:
            if pd.isna(nombre) or not nombre:
                return ""
            s = str(nombre)
            # Eliminar sufijos corporativos
            for sufijo in [
                r"\s+S\.?A\.?$", r"\s+S\.?R\.?L\.?$", r"\s+LTDA\.?$",
                r"\s+INC\.?$", r"\s+COOP\.?$", r"\s+SOCIEDAD\s+ANÓNIMA",
                r"\s+SOCIEDAD\s+DE\s+RESPONSABILIDAD\s+LIMITADA",
            ]:
                s = re.sub(sufijo, "", s, flags=re.IGNORECASE)
            # Limpiar
            s = s.strip().upper()
            s = re.sub(r" {2,}", " ", s)
            return s

        df["empresa_unificada"] = df["empresa"].apply(unificar)
        return df

    # ─── 9. Clasificar movimiento ─────────────────────────────────────────

    def _clasificar_movimiento(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega columna 'categoria_movimiento' con clasificación:
            INTERNO   — Faena, Certificación, Despacho (dentro de UY)
            EXPORT    — Exportación
            IMPORT    — Importación
            OTRO      — Transferencia, Trámite, otros
        """
        if "tipo_movimiento" not in df.columns:
            return df

        def clasificar(tipo: str) -> str:
            if pd.isna(tipo):
                return "OTRO"
            t = str(tipo).upper()
            if t in {"EXPORTACIÓN", "EXPORTACION"}:
                return "EXPORT"
            if t in {"IMPORTACIÓN", "IMPORTACION"}:
                return "IMPORT"
            if t in {"FAENA", "CERTIFICACIÓN", "CERTIFICACION", "DESPACHO"}:
                return "INTERNO"
            return "OTRO"

        df["categoria_movimiento"] = df["tipo_movimiento"].apply(clasificar)
        return df

    # ─── 10. IDs temporales ──────────────────────────────────────────────

    def _agregar_ids_temp(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega un ID temporal (auto-increment) a cada fila.
        Este ID es temporal — la BD real will assign la PK.
        """
        df.reset_index(drop=True, inplace=True)
        df.insert(0, "_id_temp", range(1, len(df) + 1))
        return df

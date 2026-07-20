"""
=================================================================================
validador.py — Validador de datos del MGAP
=================================================================================
Valida cada fila del DataFrame contra las reglas de negocio definidas.
Nunca detiene la importación por un único error — marca la fila como
rechazada o con advertencia y continúa.

Reglas validadas (RN*):
    RN001  Columnas obligatorias no nulas
    RN002  Fecha no anterior a 01/01/2025
    RN003  Kilos netos > 0
    RN004  Kilos netos es numérico
    RN005  RUC con formato válido (12 o 14 dígitos)
    RN006  Tipo establecimiento válido
    RN007  Tipo movimiento válido
    RN008  GRE no duplicado
    RN009  Departamento válido (Uruguay)
    RN010  Temperatura numérica (si presente)

Uso:
    validator = DataValidator(df, logger)
    df_valid, df_rechazadas = validator.validate()
"""

from __future__ import annotations

import re
import pandas as pd
from datetime import datetime, date
from typing import Optional

from config import (
    REGLA_FECHA_NO_NULA, REGLA_FECHA_DESDE_2025,
    REGLA_KILOS_POSITIVOS, REGLA_KILOS_NUMERICO,
    REGLA_RUC_FORMATO, REGLA_COL_OBLIGATORIA,
    REGLA_VALOR_INVALIDO, REGLA_DUPLICADO_GRE,
    REGLA_DEPTO_VALIDO, REGLA_TEMP_NUMERICA,
    COLUMNAS_MGAP, DEPARTAMENTOS_URUGUAY, RE_RUC,
)
from logger import ImportLogger


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO DE LA VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class ValidationResult:
    """
    Resultado de la validación de una fila individual.
    Se instancia una vez por fila y se acumula.
    """
    __slots__ = ("es_valida", "errores", "advertencias")

    def __init__(self) -> None:
        self.es_valida   : bool = True
        self.errores     : list[str] = []
        self.advertencias: list[str] = []

    def add_error(self, regla_id: str, mensaje: str) -> None:
        self.es_valida = False
        self.errores.append(f"[{regla_id}] {mensaje}")

    def add_warning(self, regla_id: str, mensaje: str) -> None:
        self.advertencias.append(f"[{regla_id}] {mensaje}")


# ─────────────────────────────────────────────────────────────────────────────
# DATA VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class DataValidator:
    """
    Validador de datos del MGAP.

    Valida el DataFrame completo y retorna:
        df_valido    : filas que pasan todas las validaciones
        df_rechazadas: filas con errores (no se importan)

    Los errores se registran en logger pero nunca detienen el proceso.
    """

    # Fecha mínima permitida (01/01/2025 según requisito)
    FECHA_MIN = date(2025, 1, 1)

    def __init__(self, df: pd.DataFrame, logger: ImportLogger):
        self.df     = df.copy()
        self.logger = logger
        self._gre_vistos: set[str] = set()

    # ─── Validación principal ─────────────────────────────────────────────

    def validate(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Valida todas las filas y retorna (df_valido, df_rechazadas).
        """
        self.logger.separator()
        self.logger.info("ETAPA 2 — Validación de datos")
        self.logger.info(f"Total de filas a validar: {len(self.df):,}")

        # Agregar columna de resultado
        self.df["_validacion_ok"]  = True
        self.df["_validacion_err"] = ""
        self.df["_validacion_warn"] = ""

        errores_acumulados = 0
        advertencias_acumuladas = 0

        for idx, row in self.df.iterrows():
            fila_num = idx + 2  # +2 = fila Excel (header=1)
            result = self._validar_fila(row, fila_num)

            if not result.es_valida:
                self.df.at[idx, "_validacion_ok"]  = False
                self.df.at[idx, "_validacion_err"] = "; ".join(result.errores)
                errores_acumulados += len(result.errores)

            if result.advertencias:
                self.df.at[idx, "_validacion_warn"] = "; ".join(result.advertencias)
                advertencias_acumuladas += len(result.advertencias)

        # Separar válidos y rechazados
        df_validos     = self.df[self.df["_validacion_ok"] == True].copy()
        df_rechazadas  = self.df[self.df["_validacion_ok"] == False].copy()

        # Limpiar columnas auxiliares de los válidos
        for col in ["_validacion_ok", "_validacion_err", "_validacion_warn"]:
            df_validos.drop(columns=[col], inplace=True, errors="ignore")
            df_rechazadas.drop(columns=[col], inplace=True, errors="ignore")

        self.logger.info(f"Filas válidas   : {len(df_validos):,}")
        self.logger.info(f"Filas rechazadas: {len(df_rechazadas):,}")
        self.logger.info(f"Errores totales : {errores_acumulados:,}")
        self.logger.info(f"Advertencias    : {advertencias_acumuladas:,}")
        self.logger.success("Validación completada")

        return df_validos, df_rechazadas

    # ─── Validación por fila ──────────────────────────────────────────────

    def _validar_fila(self, row: pd.Series, fila_num: int) -> ValidationResult:
        """
        Valida una fila individual contra todas las reglas.
        NO lanza excepciones — solo registra en logger y retorna resultado.
        """
        result = ValidationResult()

        # RN001 — Columnas obligatorias no nulas
        for col_def in COLUMNAS_MGAP:
            if not col_def.obligatorio:
                continue
            col = col_def.nombre_normalizado
            if col not in row.index:
                continue
            val = row[col]
            if pd.isna(val) or str(val).strip() == "":
                result.add_error(
                    REGLA_COL_OBLIGATORIA,
                    f"Campo obligatorio vacío: {col}",
                )
                self.logger.record_error(
                    REGLA_COL_OBLIGATORIA,
                    fila=fila_num,
                    columna=col,
                    valor=str(val),
                    mensaje=f"Campo obligatorio vacío",
                )

        # RN002 — Fecha no nula y desde 01/01/2025
        if "fecha_movimiento" in row.index:
            val = row["fecha_movimiento"]
            if not pd.isna(val):
                fecha_dt = self._parsear_fecha(val)
                if fecha_dt is None:
                    result.add_error(
                        REGLA_FECHA_NO_NULA,
                        f"Fecha inválida: '{val}'",
                    )
                    self.logger.record_error(
                        REGLA_FECHA_NO_NULA,
                        fila=fila_num,
                        columna="fecha_movimiento",
                        valor=str(val),
                        mensaje="Fecha no parseable",
                    )
                elif fecha_dt < self.FECHA_MIN:
                    result.add_error(
                        REGLA_FECHA_DESDE_2025,
                        f"Fecha anterior a 01/01/2025: {fecha_dt}",
                    )
                    self.logger.record_error(
                        REGLA_FECHA_DESDE_2025,
                        fila=fila_num,
                        columna="fecha_movimiento",
                        valor=str(val),
                        mensaje=f"Fecha {fecha_dt} anterior a límite 01/01/2025",
                    )

        # RN003 + RN004 — Kilos netos
        if "kilos_netos" in row.index:
            val = row["kilos_netos"]
            if not pd.isna(val):
                val_str = str(val).strip().replace(",", ".")
                try:
                    kilos = float(val_str)
                    if kilos <= 0:
                        result.add_error(
                            REGLA_KILOS_POSITIVOS,
                            f"Kilos deben ser > 0: '{val}'",
                        )
                        self.logger.record_error(
                            REGLA_KILOS_POSITIVOS,
                            fila=fila_num,
                            columna="kilos_netos",
                            valor=str(val),
                            mensaje="Kilos netos deben ser mayores a 0",
                        )
                except (ValueError, TypeError):
                    result.add_error(
                        REGLA_KILOS_NUMERICO,
                        f"Kilos no numéricos: '{val}'",
                    )
                    self.logger.record_error(
                        REGLA_KILOS_NUMERICO,
                        fila=fila_num,
                        columna="kilos_netos",
                        valor=str(val),
                        mensaje="Kilos netos no son un número válido",
                    )

        # RN005 — Formato RUC
        if "ruc" in row.index:
            val = str(row["ruc"]).strip() if not pd.isna(row["ruc"]) else ""
            if val and not RE_RUC.match(val.replace(" ", "")):
                result.add_warning(
                    REGLA_RUC_FORMATO,
                    f"RUC con formato sospechoso: '{val}'",
                )
                self.logger.record_warning(
                    REGLA_RUC_FORMATO,
                    fila=fila_num,
                    columna="ruc",
                    valor=str(val),
                    mensaje="RUC no coincide con patrón 12/14 dígitos",
                )

        # RN006 — Tipo establecimiento válido
        if "tipo_establecimiento" in row.index:
            val = str(row["tipo_establecimiento"]).strip().upper()
            if val and val not in {
                "PRODUCTOR", "CERTIFICADOR", "AMBOS",
                "MATADERO", "FRIGORÍFICO", "DISTRIBUIDOR", "DEPOSITANTE",
            }:
                result.add_warning(
                    REGLA_VALOR_INVALIDO,
                    f"Tipo establecimiento desconocido: '{val}'",
                )
                self.logger.record_warning(
                    REGLA_VALOR_INVALIDO,
                    fila=fila_num,
                    columna="tipo_establecimiento",
                    valor=str(val),
                    mensaje=f"Tipo '{val}' no reconocido en catálogo",
                )

        # RN007 — Tipo movimiento válido
        if "tipo_movimiento" in row.index:
            val = str(row["tipo_movimiento"]).strip().upper()
            if val and val not in {
                "FAENA", "CERTIFICACIÓN", "CERTIFICACION",
                "DESPACHO", "IMPORTACIÓN", "IMPORTACION",
                "EXPORTACIÓN", "EXPORTACION",
                "TRANSFERENCIA", "TRÁMITE", "TRAMITE",
            }:
                result.add_warning(
                    REGLA_VALOR_INVALIDO,
                    f"Tipo movimiento desconocido: '{val}'",
                )
                self.logger.record_warning(
                    REGLA_VALOR_INVALIDO,
                    fila=fila_num,
                    columna="tipo_movimiento",
                    valor=str(val),
                    mensaje=f"Tipo movimiento '{val}' no reconocido",
                )

        # RN008 — GRE no duplicado
        if "nro_gre" in row.index:
            val = str(row["nro_gre"]).strip() if not pd.isna(row["nro_gre"]) else ""
            if val and val.upper() not in ("N/A", "NULL", "-", ""):
                if val in self._gre_vistos:
                    result.add_error(
                        REGLA_DUPLICADO_GRE,
                        f"GRE duplicado: '{val}'",
                    )
                    self.logger.record_error(
                        REGLA_DUPLICADO_GRE,
                        fila=fila_num,
                        columna="nro_gre",
                        valor=str(val),
                        mensaje=f"Nro GRE '{val}' ya apareció en otra fila",
                    )
                else:
                    self._gre_vistos.add(val)

        # RN009 — Departamento válido
        if "departamento" in row.index:
            val = str(row["departamento"]).strip().upper()
            if val and val not in DEPARTAMENTOS_URUGUAY:
                result.add_warning(
                    REGLA_DEPTO_VALIDO,
                    f"Departamento no reconocido: '{val}'",
                )
                self.logger.record_warning(
                    REGLA_DEPTO_VALIDO,
                    fila=fila_num,
                    columna="departamento",
                    valor=str(val),
                    mensaje=f"Departamento '{val}' no es un dpto. de Uruguay",
                )

        # RN010 — Temperatura numérica
        if "temperatura" in row.index:
            val = row["temperatura"]
            if not pd.isna(val):
                try:
                    float(str(val).replace(",", "."))
                except (ValueError, TypeError):
                    result.add_warning(
                        REGLA_TEMP_NUMERICA,
                        f"Temperatura no numérica: '{val}'",
                    )
                    self.logger.record_warning(
                        REGLA_TEMP_NUMERICA,
                        fila=fila_num,
                        columna="temperatura",
                        valor=str(val),
                        mensaje="Temperatura no es un valor numérico",
                    )

        return result

    # ─── Parser de fechas flexible ────────────────────────────────────────

    @staticmethod
    def _parsear_fecha(val) -> Optional[date]:
        """
        Intenta convertir un valor a date con múltiples formatos.
        Retorna None si no puede parsear.
        """
        import re

        if pd.isna(val):
            return None

        # Ya es datetime
        if isinstance(val, (datetime, pd.Timestamp)):
            return val.date()

        s = str(val).strip()

        # Patrones comunes
        patrones = [
            (r"(\d{1,2})/(\d{1,2})/(\d{4})", "%d/%m/%Y"),
            (r"(\d{1,2})-(\d{1,2})-(\d{4})", "%d-%m-%Y"),
            (r"(\d{4})-(\d{1,2})-(\d{1,2})",  "%Y-%m-%d"),
            (r"(\d{4})/(\d{1,2})/(\d{1,2})",  "%Y/%m/%d"),
        ]

        for patron, fmt in patrones:
            m = re.match(patron, s)
            if m:
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue

        # Última opción: pandas
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return None

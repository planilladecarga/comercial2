"""
=================================================================================
config.py — Configuración centralizada del motor de importación FRIMARAL BI
=================================================================================
Toda la configuración del pipeline está aquí. No hardcodear nada fuera de este
archivo. Permite override por variables de entorno.

Configuraciones:
    • Rutas de archivos y directorios
    • Columnas obligatorias del XLSB MGAP
    • Tipos de datos esperados por columna
    • Reglas de negocio (valores permitidos, rangos)
    • Nombres de tablas SQLite
    • Parámetros de rendimiento (chunksize)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent.parent          # .../frimaral_bi/
SRC_DIR         = BASE_DIR / "src"
DATA_DIR        = BASE_DIR / "data"
LOGS_DIR        = BASE_DIR / "logs"
DB_DIR          = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH  = DB_DIR / "frimaral_bi.db"
DEFAULT_LOG_PATH = LOGS_DIR / f"importacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


# ─────────────────────────────────────────────────────────────────────────────
# COLUMNAS OBLIGATORIAS DEL XLSB MGAP
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ColumnaMGAP:
    """Representa una columna conocida del archivo XLSB del MGAP."""
    nombre_original : str          # Nombre exacto en el XLSB
    nombre_normalizado: str        # Nombre para uso interno (snake_case)
    tipo_dato       : str          # "texto" | "numero" | "fecha" | "decimal"
    obligatorio     : bool         # Si es campo requerido
    nullable        : bool         # Si puede ser NULL/nulo
    longitud_max    : Optional[int]= None  # Longitud máxima (para texto)


# Las columnas se definen en orden aproximado de aparición en el XLSB.
# Esta lista se usa para: validación, mapeo, detección automática.
COLUMNAS_MGAP: tuple[ColumnaMGAP, ...] = (
    ColumnaMGAP("Nro. Establecimiento",     "nro_establecimiento",   "texto",    True,  False, 10),
    ColumnaMGAP("Nombre Establecimiento",   "nombre_establecimiento", "texto",    True,  False, 200),
    ColumnaMGAP("Departamento",            "departamento",           "texto",    True,  False, 50),
    ColumnaMGAP("Localidad",               "localidad",              "texto",    False, True,  100),
    ColumnaMGAP("Tipo Establecimiento",    "tipo_establecimiento",   "texto",    True,  False, 30),
    ColumnaMGAP("Nro. Productor",         "nro_productor",          "texto",    True,  False, 15),
    ColumnaMGAP("Nombre Productor",        "nombre_productor",       "texto",    True,  False, 200),
    ColumnaMGAP("RUC",                     "ruc",                     "texto",    True,  False, 20),
    ColumnaMGAP("Empresa",                 "empresa",                "texto",    True,  False, 200),
    ColumnaMGAP("Destino",                 "destino",                "texto",    False, True,  200),
    ColumnaMGAP("Tipo Movimiento",         "tipo_movimiento",        "texto",    True,  False, 30),
    ColumnaMGAP("Fecha Movimiento",        "fecha_movimiento",       "fecha",    True,  False, None),
    ColumnaMGAP("Nro. GRE",                "nro_gre",                "texto",    False, True,  25),
    ColumnaMGAP("Nro. Certificado",        "nro_certificado",        "texto",    False, True,  25),
    ColumnaMGAP("Producto",                "producto",               "texto",    True,  False, 100),
    ColumnaMGAP("Kilos Netos",             "kilos_netos",           "decimal",  True,  False, None),
    ColumnaMGAP("Temperatura",             "temperatura",            "decimal",  False, True,  None),
    ColumnaMGAP("Observaciones",           "observaciones",          "texto",    False, True,  500),
)

# Mapa rápido: nombre_original → ColumnaMGAP
COLUMNA_POR_NOMBRE: dict[str, ColumnaMGAP] = {
    c.nombre_original: c for c in COLUMNAS_MGAP
}

# Nombres normalizados (orden que tendrá la tabla SQLite)
CAMPO_ORDEN = [c.nombre_normalizado for c in COLUMNAS_MGAP]

# ─────────────────────────────────────────────────────────────────────────────
# VALORES PERMITIDOS (dominios)
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_ESTABLECIMIENTO: frozenset[str] = frozenset({
    "PRODUCTOR", "CERTIFICADOR", "AMBOS",
    "Matadero", "Frigorífico", "Distribuidor", "Depositante",
})

TIPOS_MOVIMIENTO: frozenset[str] = frozenset({
    "FAENA", "CERTIFICACIÓN", "CERTIFICACION", "DESPACHO",
    "IMPORTACIÓN", "IMPORTACION", "EXPORTACIÓN", "EXPORTACION",
    "TRANSFERENCIA", "TRÁMITE", "TRAMITE",
})

# Departamentos oficiales de Uruguay (19)
DEPARTAMENTOS_URUGUAY: frozenset[str] = frozenset({
    "ARTIGAS", "CANELONES", "CERRO LARGO", "COLONIA",
    "DURAZNO", "FLORES", "FLORIDA", "LAVALLEJA",
    "MALDONADO", "MONTEVIDEO", "PAYSANDÚ", "RÍO NEGRO",
    "RIO NEGRO", "RIVERA", "ROCHA", "SALTO",
    "SAN JOSÉ", "SAN JOSE", "SORIANO", "TACUAREMBÓ", "TACUAREMBO",
    "TREINTA Y TRES", "TREINTA Y TRES",
})

# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO — IDs (referenciadas en validador.py y log)
# ─────────────────────────────────────────────────────────────────────────────

REGLA_FECHA_NO_NULA      = "RN001"
REGLA_FECHA_DESDE_2025   = "RN002"
REGLA_KILOS_POSITIVOS    = "RN003"
REGLA_KILOS_NUMERICO     = "RN004"
REGLA_RUC_FORMATO        = "RN005"
REGLA_COL_OBLIGATORIA   = "RN006"
REGLA_VALOR_INVALIDO     = "RN007"
REGLA_DUPLICADO_GRE      = "RN008"
REGLA_DEPTO_VALIDO       = "RN009"
REGLA_TEMP_NUMERICA      = "RN010"

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA BASE DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

DB_FILENAME = "frimaral_bi.db"

# Nombre de las tablas del modelo en estrella
TABLA_HECHOS        = "movimientos"
TABLA_EMPRESAS      = "dim_empresas"
TABLA_PAISES        = "dim_paises"
TABLA_PRODUCTOS     = "dim_productos"
TABLA_CORTES        = "dim_cortes"
TABLA_CALENDARIO    = "dim_calendario"
TABLA_LOG           = "log_importacion"
TABLA_LOG_ERRORES   = "log_errores"
TABLA_LOG_ADVERTENCIAS = "log_advertencias"


# ─────────────────────────────────────────────────────────────────────────────
# PARÁMETROS DE RENDIMIENTO
# ─────────────────────────────────────────────────────────────────────────────

# Filas por chunk al procesar (0 = todo en memoria)
CHUNK_SIZE: int = 10_000

# Cantidad de filas del header/excerpt para detección de tipos
HEADER_SAMPLE_SIZE: int = 100

# Encoding esperado del XLSB
DEFAULT_ENCODING: str = "utf-8"

# ─────────────────────────────────────────────────────────────────────────────
# EXPRESIONES REGULARES DE VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────

import re

# RUC Uruguayo: 12 o 14 dígitos (con o sin guiones)
RE_RUC = re.compile(r"^\d{1,2}\.?\d{3}\.?\d{3}([-.]?\d{1,3})?$")

# Caracteres invisibles comunes
RE_INVISIBLES = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\u200b\u200c\u200d\u2060\ufeff]"
)

# Espacios múltiples
RE_ESPACIOS_DOBLES = re.compile(r" {2,}")

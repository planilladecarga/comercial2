"""
=================================================================================
catalogos.py — Generador de catálogos y dimensiones
=================================================================================
Construye las tablas de dimensión a partir de los datos normalizados.

Dimensiones generadas:
    DIM_EMPRESAS    — Empresas únicas (Productor / Certificador / Depósito)
    DIM_PAISES      — Países (con flag solo_deposito y región)
    DIM_PRODUCTOS   — Productos cárnicos
    DIM_CORTES      — Cortes por producto (futuro — placeholder)
    DIM_CALENDARIO  — Calendario perpetuo

Cada módulo de catálogo es independiente y puede ejecutarse por separado.

Uso:
    builder = CatalogoBuilder(df_norm, logger)
    catalogos = builder.build_all()
    empresas_df    = catalogos["empresas"]
    paises_df     = catalogos["paises"]
    productos_df  = catalogos["productos"]
    cortes_df     = catalogos["cortes"]
    calendario_df = catalogos["calendario"]
"""

from __future__ import annotations

import pandas as pd
from datetime import datetime, date
from typing import Optional

from logger import ImportLogger


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO DE LA CONSTRUCCIÓN DE CATÁLOGOS
# ─────────────────────────────────────────────────────────────────────────────

class CatalogosResult:
    """
    Contenedor de todos los DataFrames de dimensión generados.
    """
    def __init__(self):
        self.empresas   : Optional[pd.DataFrame] = None
        self.paises    : Optional[pd.DataFrame] = None
        self.productos  : Optional[pd.DataFrame] = None
        self.cortes    : Optional[pd.DataFrame] = None
        self.calendario: Optional[pd.DataFrame] = None

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            "empresas"   : self.empresas,
            "paises"    : self.paises,
            "productos"  : self.productos,
            "cortes"    : self.cortes,
            "calendario" : self.calendario,
        }


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO BUILDER
# ─────────────────────────────────────────────────────────────────────────────

class CatalogoBuilder:
    """
    Constructor de catálogos de dimensión.

    Usage:
        builder = CatalogoBuilder(df_normalizado, logger)
        result = builder.build_all()
        empresas = result.empresas
    """

    def __init__(self, df: pd.DataFrame, logger: ImportLogger):
        self.df     = df
        self.logger = logger
        self.result = CatalogosResult()

    def build_all(self) -> CatalogosResult:
        """Construye todos los catálogos en orden."""
        self.logger.separator()
        self.logger.info("ETAPA 4 — Construcción de catálogos")

        self.logger.info("  Construyendo DIM_EMPRESAS...")
        self.result.empresas = self._build_empresas()

        self.logger.info("  Construyendo DIM_PAISES...")
        self.result.paises = self._build_paises()

        self.logger.info("  Construyendo DIM_PRODUCTOS...")
        self.result.productos = self._build_productos()

        self.logger.info("  Construyendo DIM_CORTES...")
        self.result.cortes = self._build_cortes()

        self.logger.info("  Construyendo DIM_CALENDARIO...")
        self.result.calendario = self._build_calendario()

        self.logger.success("Catálogos construidos:")
        for nombre, df in self.result.as_dict().items():
            if df is not None:
                self.logger.success(f"  {nombre}: {len(df):,} registros")

        return self.result

    # ─── DIM EMPRESAS ───────────────────────────────────────────────────

    def _build_empresas(self) -> pd.DataFrame:
        """
        Construye la dimensión EMPRESAS unificando datos de:
            • Establecimiento Productor
            • Establecimiento Certificador
            • Destino
            • Empresa (razón social)

        Cada empresa recibe:
            id_empresa    — clave subrogada
            nombre_original — nombre tal como aparece en los datos
            nombre_norm    — nombre en mayúsculas, limpio
            nombre_unif    — nombre sin SA/SRL/etc. (para match)
            ruc            — RUC de la empresa
            tipo_principal — el tipo más frecuente con que aparece
            es_productor   — bool
            es_certificador— bool
            es_deposito    — bool
            es_puerto      — bool (detectado por nombre)
            es_competidor  — bool
            activo         — siempre True para nuevas
            fecha_primera   — primera fecha de movimiento
            fecha_ultima   — última fecha de movimiento
            cant_movimientos — total de movimientos
        """
        registros: list[dict] = []
        seen: dict[str, dict] = {}

        cols_origen = [
            ("empresa",              "empresa"),
            ("nombre_establecimiento","establecimiento"),
            ("destino",              "destino"),
            ("ruc",                  "ruc"),
            ("tipo_establecimiento", "tipo_estab"),
        ]

        # Recolectar de cada origen
        for nombre_col, tipo in cols_origen:
            if nombre_col not in self.df.columns:
                continue
            for _, row in self.df.iterrows():
                nombre_raw = str(row.get(nombre_col, "")).strip()
                if not nombre_raw or nombre_raw.lower() in ("nan", "none", ""):
                    continue

                ruc_raw = str(row.get("ruc", "")).strip()
                tipo_raw = str(row.get("tipo_estab", "")).strip().upper()
                fecha_raw = str(row.get("fecha_movimiento", "")).strip()

                # Normalizar nombre
                nombre_norm = nombre_raw.upper().strip()
                nombre_unif = self._unificar_nombre(nombre_raw)

                key = nombre_unif  # usar nombre unificado como clave de dedup

                if key not in seen:
                    seen[key] = {
                        "nombre_original"   : nombre_raw,
                        "nombre_norm"       : nombre_norm,
                        "nombre_unif"       : nombre_unif,
                        "ruc"               : ruc_raw,
                        "es_productor"      : False,
                        "es_certificador"   : False,
                        "es_deposito"       : False,
                        "es_puerto"         : self._es_puerto(nombre_raw),
                        "es_competidor"     : self._es_competidor(nombre_raw),
                        "tipos_vistos"      : [],
                        "fechas"            : [],
                        "cant_movimientos"  : 0,
                    }
                seen[key]["tipos_vistos"].append(tipo_raw)
                seen[key]["cant_movimientos"] += 1
                if fecha_raw and fecha_raw != "nan":
                    seen[key]["fechas"].append(fecha_raw)

        # Clasificar tipos
        for key, emp in seen.items():
            tipos = emp["tipos_vistos"]
            emp["es_productor"]    = any(
                t in {"PRODUCTOR", "MATADERO"} for t in tipos
            )
            emp["es_certificador"] = "CERTIFICADOR" in tipos
            emp["es_deposito"]    = "DEPOSITANTE" in tipos or emp["es_deposito"]
            emp["tipo_principal"] = max(set(tipos), key=tipos.count) if tipos else "PRODUCTOR"

            # Fechas
            fechas_validas = [f for f in emp["fechas"] if f and f != "nan"]
            if fechas_validas:
                emp["fecha_primera"] = min(fechas_validas)
                emp["fecha_ultima"]  = max(fechas_validas)
            else:
                emp["fecha_primera"] = ""
                emp["fecha_ultima"]  = ""

        # Construir DataFrame (siempre con columnas definidas)
        COLS_EMPRESAS = [
            "id_empresa", "nombre_original", "nombre_norm", "nombre_unif",
            "ruc", "tipo_principal", "es_productor", "es_certificador",
            "es_deposito", "es_puerto", "es_competidor", "activo",
            "fecha_primera", "fecha_ultima", "cant_movimientos",
        ]
        if not seen:
            df_empresas = pd.DataFrame(columns=COLS_EMPRESAS)
        else:
            for emp in seen.values():
                registros.append({
                    "id_empresa"       : 0,
                    "nombre_original"  : emp["nombre_original"],
                    "nombre_norm"      : emp["nombre_norm"],
                    "nombre_unif"      : emp["nombre_unif"],
                    "ruc"              : emp["ruc"],
                    "tipo_principal"   : emp["tipo_principal"],
                    "es_productor"     : emp["es_productor"],
                    "es_certificador"  : emp["es_certificador"],
                    "es_deposito"      : emp["es_deposito"],
                    "es_puerto"       : emp["es_puerto"],
                    "es_competidor"    : emp["es_competidor"],
                    "activo"           : True,
                    "fecha_primera"    : emp["fecha_primera"],
                    "fecha_ultima"     : emp["fecha_ultima"],
                    "cant_movimientos" : emp["cant_movimientos"],
                })
            df_empresas = pd.DataFrame(registros)
            df_empresas = df_empresas.sort_values("nombre_norm").reset_index(drop=True)
            df_empresas.insert(0, "id_empresa", range(1, len(df_empresas) + 1))

        self.logger.info(f"  DIM_EMPRESAS: {len(df_empresas):,} empresas únicas")
        return df_empresas

    # ─── DIM PAÍSES ─────────────────────────────────────────────────────

    def _build_paises(self) -> pd.DataFrame:
        """
        Construye la dimensión PAÍSES.
        Detecta el país de la columna 'destino' o 'empresa'.
        Genera:
            id_pais, nombre_pais, solo_deposito, region, continente
        """
        registros: list[dict] = {}

        destino_col = "destino" if "destino" in self.df.columns else None

        for _, row in self.df.iterrows():
            nombre_raw = ""
            if destino_col:
                nombre_raw = str(row.get(destino_col, "")).strip()

            if not nombre_raw or nombre_raw.lower() in ("nan", "none", ""):
                continue

            solo_dep = bool(row.get("solo_deposito", False))
            pais_norm = nombre_raw.upper().strip()

            if pais_norm not in registros:
                region, continente = self._clasificar_region(pais_norm)
                registros[pais_norm] = {
                    "id_pais"         : 0,
                    "nombre_pais"     : pais_norm,
                    "solo_deposito"   : solo_dep,
                    "region"          : region,
                    "continente"      : continente,
                }

        df_paises = pd.DataFrame(list(registros.values()))
        df_paises = df_paises.sort_values("nombre_pais").reset_index(drop=True)
        df_paises.insert(0, "id_pais", range(1, len(df_paises) + 1))

        self.logger.info(f"  DIM_PAISES: {len(df_paises):,} países únicos")
        return df_paises

    # ─── DIM PRODUCTOS ──────────────────────────────────────────────────

    def _build_productos(self) -> pd.DataFrame:
        """
        Construye la dimensión PRODUCTOS.
        """
        if "producto" not in self.df.columns:
            return pd.DataFrame()

        productos_raw = (
            self.df["producto"]
            .dropna()
            .str.strip()
            .str.upper()
            .value_counts()
            .reset_index()
        )
        productos_raw.columns = ["nombre_producto", "frecuencia"]

        # Clasificar categoría
        def clasificar_cat(producto: str) -> str:
            p = producto.upper()
            if "BOVINA" in p or "BOVINO" in p or "VACA" in p or "TORO" in p or "TERNERA" in p:
                return "BOVINO"
            if "OVINA" in p or "OVINO" in p or "CORDERO" in p or "CABRA" in p:
                return "OVINO"
            if "PORCINA" in p or "PORCINO" in p or "CERDO" in p:
                return "PORCINO"
            if "AVE" in p or "POLLO" in p or "GALLINA" in p:
                return "AVÍCOLA"
            if "ACHURA" in p or "MENUDENCIA" in p or "CHANQU" in p:
                return "SUBPRODUCTO"
            if "CUERO" in p or "SEBO" in p or "GRASA" in p or "HUESO" in p:
                return "INDUSTRIAL"
            return "OTRO"

        def unidad(producto: str) -> str:
            p = producto.upper()
            if any(t in p for t in ["CUERO", "SEBO", "GRASA", "HUESO"]):
                return "Kg"
            if "LITRO" in p:
                return "L"
            return "Kg"

        productos_raw["categoria"]     = productos_raw["nombre_producto"].apply(clasificar_cat)
        productos_raw["unidad_medida"] = productos_raw["nombre_producto"].apply(unidad)
        productos_raw = productos_raw.drop(columns=["frecuencia"])
        productos_raw.insert(0, "id_producto", range(1, len(productos_raw) + 1))

        self.logger.info(f"  DIM_PRODUCTOS: {len(productos_raw):,} productos únicos")
        return productos_raw

    # ─── DIM CORTES ─────────────────────────────────────────────────────

    def _build_cortes(self) -> pd.DataFrame:
        """
        Placeholder para dimensión CORTES.
        Se populateá cuando se tenga un catálogo oficial de cortes del MGAP.
        """
        # Placeholder vacío
        df = pd.DataFrame(columns=[
            "id_corte", "codigo_corte", "nombre_corte",
            "producto_id", "categoria_corte", "grado",
            "kilos_promedio", "activo",
        ])
        df.insert(0, "id_corte", [])
        self.logger.info("  DIM_CORTES: placeholder (requiere catálogo oficial del MGAP)")
        return df

    # ─── DIM CALENDARIO ─────────────────────────────────────────────────

    def _build_calendario(self) -> pd.DataFrame:
        """
        Construye calendario perpetuo covering el rango de fechas en los datos.
        Si no hay datos, genera 2025-2030 por defecto.
        """
        # Determinar rango de fechas
        if "fecha_movimiento" in self.df.columns:
            fechas = pd.to_datetime(
                self.df["fecha_movimiento"], errors="coerce"
            ).dropna()
            if len(fechas) > 0:
                anio_min = int(fechas.dt.year.min())
                anio_max = int(fechas.dt.year.max())
            else:
                anio_min, anio_max = 2025, 2026
        else:
            anio_min, anio_max = 2025, 2030

        import datetime
        registros: list[dict] = []

        dias_semana_es = {
            1: "Lunes", 2: "Martes", 3: "Miércoles",
            4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
        }

        for anio in range(anio_min, anio_max + 1):
            for mes in range(1, 13):
                if mes == 12:
                    last_day = datetime.date(anio, 12, 31)
                else:
                    last_day = datetime.date(anio, mes + 1, 1) - datetime.timedelta(days=1)

                for dia in range(1, last_day.day + 1):
                    d = datetime.date(anio, mes, dia)
                    dow = d.weekday() + 1

                    registros.append({
                        "id_fecha"      : 0,
                        "fecha"         : d.isoformat(),
                        "anio"          : d.year,
                        "mes"           : d.month,
                        "nombre_mes"    : d.strftime("%B"),
                        "trimestre"     : (d.month - 1) // 3 + 1,
                        "semestre"      : 1 if d.month <= 6 else 2,
                        "semana_iso"    : d.isocalendar()[1],
                        "dia_mes"       : d.day,
                        "dia_semana"    : dow,
                        "dia_nombre"    : dias_semana_es[dow],
                        "es_laboral"    : dow <= 5,
                        "festivo_uy"    : self._es_festivo(d),
                    })

        df_cal = pd.DataFrame(registros)
        df_cal.insert(0, "id_fecha", range(1, len(df_cal) + 1))
        self.logger.info(
            f"  DIM_CALENDARIO: {len(df_cal):,} días ({anio_min}–{anio_max})"
        )
        return df_cal

    # ─── HELPERS DE CLASIFICACIÓN ───────────────────────────────────────

    @staticmethod
    def _unificar_nombre(nombre: str) -> str:
        """Elimina sufijos corporativos para poder hacer match."""
        import re
        s = str(nombre).upper().strip()
        for sufijo in [
            r"\s+S\.?A\.?$", r"\s+S\.?R\.?L\.?$", r"\s+LTDA\.?$",
            r"\s+INC\.?$", r"\s+COOP\.?$",
            r"\s+SOCIEDAD\s+ANÓNIMA$", r"\s+SOCIEDAD\s+ANONIMA$",
        ]:
            s = re.sub(sufijo, "", s, flags=re.IGNORECASE)
        s = re.sub(r" {2,}", " ", s).strip()
        return s

    @staticmethod
    def _es_puerto(nombre: str) -> bool:
        """Detecta si una empresa es un puerto."""
        puertos = {"PUERTO", "PORT", "HARBOR", "PUERTO MONTEVIDEO",
                   "PUERTO DE MONTEVIDEO", "ANDAINA"}
        n = nombre.upper()
        return any(p in n for p in puertos)

    @staticmethod
    def _es_competidor(nombre: str) -> bool:
        """Detecta si es una empresa competidora conocida."""
        competidores = {"JBS", "MARCIL", "BFR", "BRF", "MINERVA",
                       "AGROSUPER", "COPERBO", "SO男士"}
        n = nombre.upper()
        return any(c in n for c in competidores)

    @staticmethod
    def _clasificar_region(pais: str) -> tuple[str, str]:
        """Clasifica región y continente de un país."""
        sudamerica = {
            "URUGUAY": ("Sudamerica", "America del Sur"),
            "ARGENTINA": ("Sudamerica", "America del Sur"),
            "BRASIL": ("Sudamerica", "America del Sur"),
            "PARAGUAY": ("Sudamerica", "America del Sur"),
            "CHILE": ("Andina", "America del Sur"),
            "PERU": ("Andina", "America del Sur"),
        }
        if pais.upper() in sudamerica:
            return sudamerica[pais.upper()]
        return ("Otro", "Otro")

    @staticmethod
    def _es_festivo(d: date) -> str:
        """Retorna nombre del festivo uruguayo si aplica."""
        festivos = {
            (1, 1): "Año Nuevo",
            (1, 6): "Día de los Reyes",
            (4, 17): "Desembarco de los 33",
            (5, 1): "Día del Trabajo",
            (5, 18): "Batalla de Las Piedras",
            (6, 19): "Día de José Gervasio Artigas",
            (7, 18): "Jura de la Constitución",
            (8, 25): "Declaración de la Independencia",
            (11, 2): "Día de los Difuntos",
            (12, 25): "Navidad",
        }
        return festivos.get((d.month, d.day), "")

"""
=================================================================================
database.py — Motor de base de datos SQLite (modelo en estrella)
=================================================================================
Crea y gestiona la base de datos SQLite con el modelo en estrella de FRIMARAL BI.

Modelo en estrella:
                    ┌─────────────────┐
                    │  MOVIMIENTOS    │  ← Tabla de hechos
                    │  (fact table)   │
                    └────────┬────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │           │         │         │           │
       ▼           ▼         ▼         ▼           ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
   │  DIM    │ │  DIM   │ │  DIM   │ │  DIM   │ │   DIM    │
   │EMPRESAS │ │ PAISES │ │PRODUCTOS│ │ CORTES │ │CALENDARIO│
   └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘

Tablas:
    dim_empresas      — Dimensión empresas
    dim_paises       — Dimensión países
    dim_productos    — Dimensión productos
    dim_cortes       — Dimensión cortes
    dim_calendario   — Dimensión calendario perpetuo
    movimientos      — Tabla de hechos (movimientos)
    log_importacion  — Log de cada importación
    log_errores      — Detalle de errores
    log_advertencias  — Detalle de advertencias

Uso:
    db = FRIMARALDatabase("frimaral_bi.db")
    db.crear_esquema()
    db.insertar_movimientos(df_movimientos)
    db.insertar_dimension("empresas", df_empresas)
    db.insertar_dimension("paises",   df_paises)
    db.insertar_dimension("productos",df_productos)
    db.insertar_calendario(df_calendario)
    db.cerrar()
"""

from __future__ import annotations

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from config import (
    DB_DIR, TABLA_HECHOS, TABLA_EMPRESAS, TABLA_PAISES,
    TABLA_PRODUCTOS, TABLA_CORTES, TABLA_CALENDARIO,
    TABLA_LOG, TABLA_LOG_ERRORES, TABLA_LOG_ADVERTENCIAS,
)
from logger import ImportLogger, ImportReport


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────

class FRIMARALDatabase:
    """
    Gestor de la base de datos SQLite del modelo en estrella FRIMARAL BI.

    Uso:
        db = FRIMARALDatabase("frimaral_bi.db")
        db.crear_esquema()
        db.insertar_movimientos(df)
        db.insertar_dimension("empresas", df_empresas)
        db.commit()
    """

    # Schema SQL — orden de creación (importancias de FK)
    SCHEMA_SQL: list[str] = [
        # ── Dimensiones ──────────────────────────────────────────────────
        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_EMPRESAS} (
            id_empresa        INTEGER PRIMARY KEY,
            nombre_original   TEXT,
            nombre_norm       TEXT NOT NULL,
            nombre_unif      TEXT,
            ruc              TEXT,
            tipo_principal    TEXT,
            es_productor      INTEGER DEFAULT 0,
            es_certificador  INTEGER DEFAULT 0,
            es_deposito      INTEGER DEFAULT 0,
            es_puerto        INTEGER DEFAULT 0,
            es_competidor    INTEGER DEFAULT 0,
            activo           INTEGER DEFAULT 1,
            fecha_primera    TEXT,
            fecha_ultima     TEXT,
            cant_movimientos INTEGER DEFAULT 0,
            UNIQUE(nombre_unif)
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_PAISES} (
            id_pais        INTEGER PRIMARY KEY,
            nombre_pais    TEXT NOT NULL UNIQUE,
            solo_deposito  INTEGER DEFAULT 0,
            region         TEXT,
            continente     TEXT
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_PRODUCTOS} (
            id_producto    INTEGER PRIMARY KEY,
            nombre_producto TEXT NOT NULL UNIQUE,
            categoria      TEXT,
            unidad_medida  TEXT DEFAULT 'Kg'
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_CORTES} (
            id_corte        INTEGER PRIMARY KEY,
            codigo_corte    TEXT UNIQUE,
            nombre_corte    TEXT NOT NULL,
            producto_id     INTEGER,
            categoria_corte TEXT,
            grado           TEXT,
            kilos_promedio  REAL,
            activo          INTEGER DEFAULT 1,
            FOREIGN KEY (producto_id) REFERENCES {TABLA_PRODUCTOS}(id_producto)
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_CALENDARIO} (
            id_fecha       INTEGER PRIMARY KEY,
            fecha          TEXT NOT NULL UNIQUE,
            anio           INTEGER NOT NULL,
            mes            INTEGER NOT NULL,
            nombre_mes     TEXT,
            trimestre      INTEGER NOT NULL,
            semestre       INTEGER NOT NULL,
            semana_iso     INTEGER,
            dia_mes        INTEGER,
            dia_semana     INTEGER,
            dia_nombre     TEXT,
            es_laboral     INTEGER DEFAULT 1,
            festivo_uy     TEXT
        );
        """,

        # ── Tabla de hechos ──────────────────────────────────────────────
        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_HECHOS} (
            id_movimiento      INTEGER PRIMARY KEY AUTOINCREMENT,
            _id_temp           INTEGER,
            nro_establecimiento TEXT,
            nombre_establecimiento TEXT,
            departamento       TEXT,
            localidad          TEXT,
            tipo_establecimiento TEXT,
            nro_productor      TEXT,
            nombre_productor   TEXT,
            ruc                TEXT,
            empresa_id         INTEGER,
            destino            TEXT,
            tipo_movimiento    TEXT,
            categoria_movimiento TEXT,
            fecha_movimiento   TEXT,
            fecha_id           INTEGER,
            nro_gre            TEXT,
            nro_certificado    TEXT,
            producto_id        INTEGER,
            kilos_netos        REAL,
            temperatura        REAL,
            solo_deposito      INTEGER DEFAULT 0,
            observaciones      TEXT,
            empresa_unificada  TEXT,
            -- FK a dimensiones
            FOREIGN KEY (empresa_id)  REFERENCES {TABLA_EMPRESAS}(id_empresa),
            FOREIGN KEY (producto_id) REFERENCES {TABLA_PRODUCTOS}(id_producto),
            FOREIGN KEY (fecha_id)   REFERENCES {TABLA_CALENDARIO}(id_fecha)
        );
        """,

        # ── Logs ─────────────────────────────────────────────────────────
        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_LOG} (
            id_log        INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id     TEXT NOT NULL,
            archivo       TEXT,
            hoja          TEXT,
            filas_total   INTEGER,
            filas_importadas INTEGER,
            filas_rechazadas INTEGER,
            errores_count INTEGER,
            advertencias  INTEGER,
            tiempo_seg    REAL,
            timestamp     TEXT NOT NULL
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {TABLA_LOG_ERRORES} (
            id_error   INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id  TEXT NOT NULL,
            regla_id   TEXT,
            fila       INTEGER,
            columna    TEXT,
            valor      TEXT,
            mensaje    TEXT,
            severity   TEXT,
            timestamp  TEXT
        );
        """,
    ]

    # Índices para rendimiento en consultas analíticas
    INDICES_SQL: list[str] = [
        f"CREATE INDEX IF NOT EXISTS idx_mov_fecha     ON {TABLA_HECHOS}(fecha_movimiento);",
        f"CREATE INDEX IF NOT EXISTS idx_mov_empresa   ON {TABLA_HECHOS}(empresa_id);",
        f"CREATE INDEX IF NOT EXISTS idx_mov_producto   ON {TABLA_HECHOS}(producto_id);",
        f"CREATE INDEX IF NOT EXISTS idx_mov_tipo      ON {TABLA_HECHOS}(tipo_movimiento);",
        f"CREATE INDEX IF NOT EXISTS idx_mov_depto     ON {TABLA_HECHOS}(departamento);",
        f"CREATE INDEX IF NOT EXISTS idx_mov_gre       ON {TABLA_HECHOS}(nro_gre);",
        f"CREATE INDEX IF NOT EXISTS idx_cal_fecha     ON {TABLA_CALENDARIO}(fecha);",
        f"CREATE INDEX IF NOT EXISTS idx_cal_anio_mes  ON {TABLA_CALENDARIO}(anio, mes);",
    ]

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path: Path = Path(db_path) if db_path else DB_DIR / "frimaral_bi.db"
        self.conn   : Optional[sqlite3.Connection] = None
        self.logger : Optional[ImportLogger] = None

    def set_logger(self, logger: ImportLogger) -> None:
        self.logger = logger

    # ─── Connection management ───────────────────────────────────────────

    @contextmanager
    def connect(self):
        """Gestor de contexto para la conexión."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")   # Mejor rendimiento
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            yield conn
        finally:
            conn.close()

    def abrir(self) -> None:
        """Abre la conexión manualmente."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")

    def cerrar(self) -> None:
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ─── Crear esquema ──────────────────────────────────────────────────

    def crear_esquema(self) -> None:
        """Crea todas las tablas del modelo en estrella."""
        self.abrir()
        with self.conn:
            for sql in self.SCHEMA_SQL:
                self.conn.executescript(sql)
            for sql in self.INDICES_SQL:
                self.conn.executescript(sql)

        if self.logger:
            self.logger.success(f"Esquema creado: {self.db_path}")

    # ─── Inserciones ───────────────────────────────────────────────────

    def insertar_dimension(
        self, tipo: str, df: pd.DataFrame, if_exists: str = "replace"
    ) -> int:
        """
        Inserta datos en una tabla de dimensión.

        Args:
            tipo: "empresas" | "paises" | "productos" | "cortes"
            df  : DataFrame con los datos
            if_exists: "replace" | "append"

        Returns:
            Cantidad de filas insertadas.
        """
        tabla_map = {
            "empresas" : TABLA_EMPRESAS,
            "paises"   : TABLA_PAISES,
            "productos": TABLA_PRODUCTOS,
            "cortes"   : TABLA_CORTES,
        }
        tabla = tabla_map.get(tipo.lower())
        if not tabla:
            raise ValueError(f"Tipo de dimensión desconocido: {tipo}")

        if df is None or df.empty:
            if self.logger:
                self.logger.info(f"  {tabla}: sin datos (skip)")
            return 0

        self.abrir()
        with self.conn:
            # Remover PK temporal si existe
            cols = [c for c in df.columns if c != "id_empresa"
                    and c != "id_pais" and c != "id_producto"
                    and c != "id_corte"]
            df_ins = df[cols].copy()
            filas = df_ins.to_sql(tabla, self.conn, if_exists=if_exists, index=False)
            self.conn.commit()

        if self.logger:
            self.logger.info(f"  {tabla}: {len(df_ins):,} registros insertados")
        return len(df_ins)

    def insertar_calendario(
        self, df: pd.DataFrame, if_exists: str = "append"
    ) -> int:
        """Inserta el calendario (dimsión especial)."""
        if df is None or df.empty:
            return 0

        self.abrir()
        with self.conn:
            # Solo insertar fechas que no existan (IGNORE)
            cols = [c for c in df.columns if c != "id_fecha"]
            df_ins = df[cols].copy()
            # Upsert: insert or ignore
            df_ins.to_sql(TABLA_CALENDARIO, self.conn,
                          if_exists="append", index=False)
            self.conn.execute(f"""
                DELETE FROM {TABLA_CALENDARIO}
                WHERE rowid IN (
                    SELECT rowid FROM {TABLA_CALENDARIO}
                    EXCEPT
                    SELECT rowid FROM {TABLA_CALENDARIO}
                    LIMIT 1
                )
            """)
            self.conn.commit()

        if self.logger:
            self.logger.info(
                f"  {TABLA_CALENDARIO}: {len(df_ins):,} días insertados"
            )
        return len(df_ins)

    def insertar_movimientos(
        self,
        df: pd.DataFrame,
        catalogos  : dict,  # {"empresas": df, "paises": df, ...}
        if_exists: str = "replace",
    ) -> int:
        """
        Inserta la tabla de hechos MOVIMIENTOS.
        Resuelve las claves subrogadas (FK) antes de insertar.

        Args:
            df: DataFrame normalizado de movimientos
            catalogos: dict con los DataFrames de dimensión ya cargados
            if_exists: "replace" | "append"
        """
        if df is None or df.empty:
            if self.logger:
                self.logger.warning("No hay movimientos para insertar")
            return 0

        self.abrir()
        with self.conn:
            # ── Cargar dimensiones en memoria para lookup ──────────────────
            dim_empresas = self._cargar_dict(
                TABLA_EMPRESAS, "nombre_unif", "id_empresa"
            )
            dim_paises = self._cargar_dict(
                TABLA_PAISES, "nombre_pais", "id_pais"
            )
            dim_productos = self._cargar_dict(
                TABLA_PRODUCTOS, "nombre_producto", "id_producto"
            )
            dim_calendario = self._cargar_dict(
                TABLA_CALENDARIO, "fecha", "id_fecha"
            )

            # ── Resolver FKs ──────────────────────────────────────────────
            def resolver_empresa(row) -> Optional[int]:
                key = str(row.get("empresa_unificada", "")).strip().upper()
                if not key:
                    return None
                return dim_empresas.get(key)

            def resolver_pais(row) -> Optional[int]:
                key = str(row.get("destino", "")).strip().upper()
                if not key:
                    return None
                return dim_paises.get(key)

            def resolver_producto(row) -> Optional[int]:
                key = str(row.get("producto", "")).strip().upper()
                if not key:
                    return None
                return dim_productos.get(key)

            def resolver_fecha(row) -> Optional[int]:
                key = str(row.get("fecha_movimiento", "")).strip()
                if not key:
                    return None
                return dim_calendario.get(key)

            # ── Construir filas con FKs ───────────────────────────────────
            filas_ok = 0
            filas_skip = 0
            registros = []

            for _, row in df.iterrows():
                emp_id = resolver_empresa(row)
                prod_id = resolver_producto(row)
                pais_id = resolver_pais(row)
                fecha_id = resolver_fecha(row)

                if emp_id is None and prod_id is None:
                    filas_skip += 1
                    continue

                reg = {
                    "_id_temp"              : row.get("_id_temp"),
                    "nro_establecimiento"   : row.get("nro_establecimiento"),
                    "nombre_establecimiento": row.get("nombre_establecimiento"),
                    "departamento"          : row.get("departamento"),
                    "localidad"             : row.get("localidad"),
                    "tipo_establecimiento"  : row.get("tipo_establecimiento"),
                    "nro_productor"         : row.get("nro_productor"),
                    "nombre_productor"      : row.get("nombre_productor"),
                    "ruc"                   : row.get("ruc"),
                    "empresa_id"            : emp_id,
                    "destino"               : row.get("destino"),
                    "tipo_movimiento"       : row.get("tipo_movimiento"),
                    "categoria_movimiento"  : row.get("categoria_movimiento"),
                    "fecha_movimiento"      : row.get("fecha_movimiento"),
                    "fecha_id"              : fecha_id,
                    "nro_gre"               : row.get("nro_gre"),
                    "nro_certificado"       : row.get("nro_certificado"),
                    "producto_id"           : prod_id,
                    "kilos_netos"           : row.get("kilos_netos"),
                    "temperatura"           : row.get("temperatura"),
                    "solo_deposito"         : int(row.get("solo_deposito", 0)),
                    "observaciones"         : row.get("observaciones"),
                    "empresa_unificada"     : row.get("empresa_unificada"),
                }
                registros.append(reg)
                filas_ok += 1

            if registros:
                df_ins = pd.DataFrame(registros)
                # Remover columna _id_temp del SQL (no existe en tabla)
                cols = [c for c in df_ins.columns if c != "_id_temp"]
                df_ins[cols].to_sql(
                    TABLA_HECHOS, self.conn,
                    if_exists=if_exists, index=False
                )
                self.conn.commit()

        if self.logger:
            self.logger.success(
                f"  {TABLA_HECHOS}: {filas_ok:,} movimientos insertados"
            )
            if filas_skip:
                self.logger.warning(
                    f"  {TABLA_HECHOS}: {filas_skip:,} filas omitidas (sin FK)"
                )

        return filas_ok

    def insertar_log(self, report: ImportReport) -> None:
        """Inserta el resultado de la importación en las tablas de log."""
        self.abrir()
        import_id = datetime.now().strftime("%Y%m%d%H%M%S")

        with self.conn:
            self.conn.execute(f"""
                INSERT INTO {TABLA_LOG}
                (import_id, archivo, hoja, filas_total, filas_importadas,
                 filas_rechazadas, errores_count, advertencias, tiempo_seg, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                import_id,
                report.stats.archivo,
                report.stats.hoja_seleccionada,
                report.stats.filas_total,
                report.stats.filas_importadas,
                report.stats.filas_rechazadas,
                report.stats.errores_count,
                report.stats.advertencias_count,
                report.stats.tiempo_total_seg,
                datetime.now().isoformat(),
            ))

            for err in report.errores:
                self.conn.execute(f"""
                    INSERT INTO {TABLA_LOG_ERRORES}
                    (import_id, regla_id, fila, columna, valor, mensaje, severity, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    import_id,
                    err.regla_id,
                    err.fila,
                    err.columna,
                    err.valor,
                    err.mensaje,
                    err.severity,
                    datetime.now().isoformat(),
                ))

            self.conn.commit()

        if self.logger:
            self.logger.success("Log guardado en base de datos")

    # ─── Helpers ────────────────────────────────────────────────────────

    def _cargar_dict(
        self, tabla: str, key_col: str, val_col: str
    ) -> dict:
        """Carga una columna como diccionario para lookup rápido."""
        try:
            df = pd.read_sql(f"SELECT {key_col}, {val_col} FROM {tabla}", self.conn)
            return dict(zip(df[key_col].str.upper(), df[val_col]))
        except Exception:
            return {}

    # ─── Consultas útiles ────────────────────────────────────────────────

    def conteo(self, tabla: str) -> int:
        """Retorna la cantidad de filas en una tabla."""
        self.abrir()
        cur = self.conn.execute(f"SELECT COUNT(*) FROM {tabla}")
        count = cur.fetchone()[0]
        self.conn.close()
        return count

    def sql_query(self, query: str) -> pd.DataFrame:
        """Ejecuta una consulta SQL y retorna un DataFrame."""
        self.abrir()
        df = pd.read_sql(query, self.conn)
        self.conn.close()
        return df

    def resumen(self) -> dict[str, int]:
        """Resumen rápido de registros por tabla."""
        tablas = [
            TABLA_HECHOS, TABLA_EMPRESAS, TABLA_PAISES,
            TABLA_PRODUCTOS, TABLA_CORTES, TABLA_CALENDARIO,
        ]
        self.abrir()
        result = {}
        for t in tablas:
            try:
                cur = self.conn.execute(f"SELECT COUNT(*) FROM {t}")
                result[t] = cur.fetchone()[0]
            except Exception:
                result[t] = -1
        self.conn.close()
        return result

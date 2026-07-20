"""
BusinessQueryRepository - Capa de acceso a datos
"""
import sqlite3
import time
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from ..database import db
from ..queries.comando_queries import QUERY_FILTRO_MERCADOS, QUERY_FILTRO_PRODUCTOS


class BusinessQueryRepository:
    """Acceso a datos para el motor de consultas."""

    def ejecutar_consulta(self, sql: str, params: dict) -> tuple[list[dict], float]:
        """
        Ejecuta una consulta SQL con parámetros y retorna (datos, tiempo_ms).
        Optimizado para rendimiento < 2 segundos.
        """
        start = time.perf_counter()

        # Reemplazar parámetros :nombre por ?
        import re
        # Normalizar :param -> ?
        def normalize_sql(s):
            # Encuentra todos los :parametros
            params_found = re.findall(r':(\w+)', s)
            for p in params_found:
                s = s.replace(f':{p}', f':{p}')  # keep as named
            return s

        with db.connect() as conn:
            conn.row_factory = sqlite3.Row
            # Usar text_factory para evitar problemas
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            datos = [dict(row) for row in rows]

        elapsed = (time.perf_counter() - start) * 1000
        return datos, elapsed

    def ejecutar_raw(self, sql: str, params: tuple = ()) -> list[dict]:
        """Ejecuta SQL plano y retorna resultados."""
        with db.connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def obtener_empresas(self) -> list[dict]:
        """Lista empresas para dropdowns."""
        return db.execute(
            "SELECT id_empresa, nombre_unif FROM dim_empresas WHERE activo = 1 ORDER BY nombre_unif"
        )

    def obtener_mercados(self) -> list[str]:
        """Lista mercados únicos."""
        rows = db.execute(QUERY_FILTRO_MERCADOS)
        return [r["mercado"] for r in rows]

    def obtener_productos(self) -> list[dict]:
        """Lista productos."""
        return db.execute(
            "SELECT id_producto, nombre_producto, categoria FROM dim_productos ORDER BY nombre_producto"
        )

    def obtener_certificadores(self) -> list[dict]:
        """Lista certificadores."""
        return db.execute(
            "SELECT id_empresa, nombre_unif FROM dim_empresas WHERE es_certificador = 1 AND activo = 1 ORDER BY nombre_unif"
        )

    def obtener_depositos(self) -> list[dict]:
        """Lista depósitos."""
        return db.execute(
            "SELECT id_empresa, nombre_unif FROM dim_empresas WHERE es_deposito = 1 AND activo = 1 ORDER BY nombre_unif"
        )

    def obtener_fechas_rango(self) -> dict:
        """Obtiene la primera y última fecha de movimiento."""
        row = db.execute_one(
            "SELECT MIN(fecha_movimiento) as min_fecha, MAX(fecha_movimiento) as max_fecha FROM movimientos"
        )
        return {
            "min": row["min_fecha"] if row else None,
            "max": row["max_fecha"] if row else None,
        }

    # ─── Historial ───────────────────────────────────────────────

    def guardar_historial(
        self,
        consulta_id: str,
        consulta_nombre: str,
        parametros: dict,
        usuario: str,
        tiempo_ms: float,
        total_registros: int,
    ) -> int:
        """Guarda una entrada en el historial. Retorna el ID."""
        from datetime import datetime
        import json

        with db.connect() as conn:
            cur = conn.execute(
                """INSERT INTO bq_historial
                   (consulta_id, consulta_nombre, parametros, usuario, timestamp, tiempo_ms, total_registros)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    consulta_id,
                    consulta_nombre,
                    json.dumps(parametros),
                    usuario,
                    datetime.now().isoformat(),
                    tiempo_ms,
                    total_registros,
                ),
            )
            conn.commit()
            return cur.lastrowid or 0

    def obtener_historial(self, limite: int = 50) -> list[dict]:
        """Obtiene las últimas entradas del historial."""
        import json
        rows = db.execute(
            f"""SELECT id, consulta_id, consulta_nombre, parametros, usuario,
                       timestamp, tiempo_ms, total_registros
                FROM bq_historial
                ORDER BY timestamp DESC
                LIMIT {limite}"""
        )
        result = []
        for r in rows:
            d = dict(r)
            d["parametros"] = json.loads(d["parametros"]) if d.get("parametros") else {}
            result.append(d)
        return result

    def crear_tabla_historial(self):
        """Crea la tabla de historial si no existe."""
        with db.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bq_historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consulta_id TEXT NOT NULL,
                    consulta_nombre TEXT NOT NULL,
                    parametros TEXT,
                    usuario TEXT DEFAULT 'system',
                    timestamp TEXT NOT NULL,
                    tiempo_ms REAL,
                    total_registros INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bq_historial_timestamp ON bq_historial(timestamp DESC)")
            conn.commit()

    # ─── Favoritos ────────────────────────────────────────────────

    def guardar_favorito(
        self,
        consulta_id: str,
        consulta_nombre: str,
        parametros: dict,
        nombre_custom: str = None,
    ) -> int:
        """Guarda una consulta como favorita."""
        import json
        with db.connect() as conn:
            cur = conn.execute(
                """INSERT INTO bq_favoritos (consulta_id, consulta_nombre, parametros_default, nombre_custom)
                   VALUES (?, ?, ?, ?)""",
                (consulta_id, consulta_nombre, json.dumps(parametros), nombre_custom),
            )
            conn.commit()
            return cur.lastrowid or 0

    def obtener_favoritos(self) -> list[dict]:
        """Obtiene favoritos."""
        import json
        rows = db.execute(
            "SELECT id, consulta_id, consulta_nombre, parametros_default, nombre_custom FROM bq_favoritos ORDER BY id DESC"
        )
        result = []
        for r in rows:
            d = dict(r)
            d["parametros_default"] = json.loads(d.get("parametros_default") or "{}")
            result.append(d)
        return result

    def eliminar_favorito(self, favorito_id: int) -> bool:
        """Elimina un favorito."""
        with db.connect() as conn:
            cur = conn.execute("DELETE FROM bq_favoritos WHERE id = ?", (favorito_id,))
            conn.commit()
            return cur.rowcount > 0

    def crear_tabla_favoritos(self):
        """Crea la tabla de favoritos si no existe."""
        with db.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bq_favoritos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consulta_id TEXT NOT NULL,
                    consulta_nombre TEXT NOT NULL,
                    parametros_default TEXT,
                    nombre_custom TEXT
                )
            """)
            conn.commit()


repo = BusinessQueryRepository()

# Inicializar tablas
repo.crear_tabla_historial()
repo.crear_tabla_favoritos()

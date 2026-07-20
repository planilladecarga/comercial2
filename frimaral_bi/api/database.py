"""
Conexión a la base de datos SQLite.
Módulo centralizado para todas las conexiones a la BD.
"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from .config import DB_PATH


class Database:
    """Gestor de conexión SQLite con rendimiento optimizado."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    @contextmanager
    def connect(self):
        """Gestor de contexto para conexión a la BD."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> list[dict]:
        """Ejecuta una consulta y retorna lista de diccionarios."""
        with self.connect() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Ejecuta consulta y retorna un solo resultado o None."""
        with self.connect() as conn:
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def execute_scalar(self, query: str, params: tuple = ()):
        """Retorna un solo valor escalar."""
        with self.connect() as conn:
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return row[0] if row else None


# Instancia global
db = Database()

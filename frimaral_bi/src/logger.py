"""
=================================================================================
logger.py — Sistema de logging y reporte de importación FRIMARAL BI
=================================================================================
Registra todo lo que ocurre durante el pipeline y genera un reporte final.

Responsabilidades:
    • Logging estructurado a archivo y consola
    • Acumulación de estadísticas durante el pipeline
    • Registro de errores individuales con fila, columna, valor y regla
    • Generación de reporte final (texto + guardado en BD)
    • Detector de elementos nuevos (empresas, países, productos no conocidos)

Uso:
    logger = ImportLogger("mi_archivo.xlsb")
    logger.info("Iniciando lectura...")
    logger.record_error("RN003", fila=5, columna="kilos_netos", valor="-10")
    logger.add_new("empresa", "Frigorífico del Norte")
    reporte = logger.generate_report()
"""

from __future__ import annotations

import time
import logging
import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from enum import Enum

from config import DEFAULT_LOG_PATH


# ─────────────────────────────────────────────────────────────────────────────
# NIVELES DE LOG
# ─────────────────────────────────────────────────────────────────────────────

class LogLevel(Enum):
    INFO     = "INFO"
    WARNING  = "WARNING"
    ERROR    = "ERROR"
    SUCCESS  = "SUCCESS"
    SKIP     = "SKIP"


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO DE UN ERROR INDIVIDUAL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ErrorEntry:
    """Un error o advertencia encontrado durante la importación."""
    regla_id   : str
    severity   : str           # "ERROR" | "WARNING"
    fila       : int
    columna    : str
    valor      : str
    mensaje    : str
    timestamp  : str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


# ─────────────────────────────────────────────────────────────────────────────
# ESTADÍSTICAS ACUMULADAS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ImportStats:
    """Estadísticas acumuladas a lo largo de todo el pipeline."""
    archivo            : str          = ""
    hojas_encontradas  : list[str]    = field(default_factory=list)
    hoja_seleccionada  : str          = ""
    columnas_detectadas: list[str]    = field(default_factory=list)
    filas_total        : int          = 0
    filas_importadas   : int          = 0
    filas_rechazadas   : int          = 0
    errores_count      : int          = 0
    advertencias_count : int          = 0
    empresas_nuevas    : set[str]     = field(default_factory=set)
    paises_nuevos      : set[str]     = field(default_factory=set)
    productos_nuevos   : set[str]     = field(default_factory=set)
    tiempo_inicio      : float        = 0.0
    tiempo_fin         : float        = 0.0
    tiempo_total_seg   : float        = 0.0

    def duracion_str(self) -> str:
        """Duración legible: Xm Ys."""
        t = self.tiempo_total_seg
        m = int(t // 60)
        s = round(t % 60, 2)
        return f"{m}m {s}s" if m else f"{s}s"

    def nuevos_resumen(self) -> dict[str, int]:
        return {
            "empresas": len(self.empresas_nuevas),
            "paises"  : len(self.paises_nuevos),
            "productos": len(self.productos_nuevos),
        }


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT LOGGER — CLASE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class ImportLogger:
    """
    Logger centralizado del proceso de importación.

    Maneja:
        • Logging a consola y archivo (.log)
        • Acumulación de estadísticas
        • Registro de errores y advertencias
        • Detección de elementos nuevos
        • Generación de reporte final

    Ejemplo:
        logger = ImportLogger("MGAP_2025.xlsb")
        logger.info("Iniciando...")
        logger.record_error("RN001", fila=3, columna="fecha", valor="abc")
        reporte = logger.finish()
    """

    def __init__(
        self,
        archivo_origen: str,
        log_path      : Optional[Path] = None,
        nivel_consola : int = logging.INFO,
    ):
        self.archivo = Path(archivo_origen).name
        self.stats   = ImportStats(archivo=self.archivo)
        self._errores: list[ErrorEntry] = []

        # Logging a archivo
        self._log_path = log_path or DEFAULT_LOG_PATH
        self._file_handler = logging.FileHandler(
            self._log_path, mode="w", encoding="utf-8"
        )
        self._file_handler.setLevel(logging.DEBUG)
        fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
        self._file_handler.setFormatter(logging.Formatter(fmt))

        # Logging a consola
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(nivel_consola)
        self._console_handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                              datefmt="%H:%M:%S")
        )

        # Logger principal
        self._log = logging.getLogger("frimaral_bi")
        self._log.setLevel(logging.DEBUG)
        self._log.handlers.clear()
        self._log.addHandler(self._file_handler)
        self._log.addHandler(self._console_handler)

        self.stats.tiempo_inicio = time.time()
        self._separator()
        self.info(f"Inicio de importación — {self.archivo}")
        self._separator()

    # ─── Métodos públicos de logging ───────────────────────────────────────

    def info    (self, msg: str) -> None: self._log.info(msg)
    def warning (self, msg: str) -> None: self._log.warning(msg)
    def error   (self, msg: str) -> None: self._log.error(msg)
    def success (self, msg: str) -> None: self._log.log(35, f"✅  {msg}")  # SUCCESS
    def skip    (self, msg: str) -> None: self._log.log(25, f"⏭️  {msg}")  # SKIP

    def separator(self) -> None:
        self._separator()

    # ─── Registro de errores y advertencias ────────────────────────────────

    def record_error(
        self,
        regla_id: str,
        fila    : int,
        columna : str,
        valor   : str,
        mensaje : str,
    ) -> None:
        """Registra un ERROR en la importación (fila no se importa)."""
        entry = ErrorEntry(
            regla_id=regla_id,
            severity="ERROR",
            fila=fila,
            columna=columna,
            valor=str(valor)[:80],
            mensaje=mensaje,
        )
        self._errores.append(entry)
        self.stats.errores_count += 1
        self._log.error(f"[{regla_id}] Fila {fila} | {columna} = '{valor[:40]}' — {mensaje}")

    def record_warning(
        self,
        regla_id: str,
        fila    : int,
        columna : str,
        valor   : str,
        mensaje : str,
    ) -> None:
        """Registra una ADVERTENCIA (fila se importa con reserva)."""
        entry = ErrorEntry(
            regla_id=regla_id,
            severity="WARNING",
            fila=fila,
            columna=columna,
            valor=str(valor)[:80],
            mensaje=mensaje,
        )
        self._errores.append(entry)
        self.stats.advertencias_count += 1
        self._log.warning(f"[{regla_id}] Fila {fila} | {columna} = '{valor[:40]}' — {mensaje}")

    # ─── Detección de elementos nuevos ────────────────────────────────────

    def add_new_empresa  (self, nombre: str) -> None: self.stats.empresas_nuevas.add(nombre)
    def add_new_pais     (self, nombre: str) -> None: self.stats.paises_nuevos.add(nombre)
    def add_new_producto (self, nombre: str) -> None: self.stats.productos_nuevos.add(nombre)

    # ─── Helpers para el importador ───────────────────────────────────────

    def set_hoja    (self, hoja: str) -> None: self.stats.hoja_seleccionada = hoja
    def set_columnas(self, cols: list[str]) -> None: self.stats.columnas_detectadas = cols
    def add_hoja    (self, hoja: str) -> None: self.stats.hojas_encontradas.append(hoja)
    def set_filas   (self, total: int) -> None: self.stats.filas_total = total

    # ─── Finalización y reporte ────────────────────────────────────────────

    def finish(self) -> "ImportReport":
        """Finaliza el logger y retorna un reporte estructurado."""
        self.stats.tiempo_fin = time.time()
        self.stats.tiempo_total_seg = self.stats.tiempo_fin - self.stats.tiempo_inicio
        reporte = self.generate_report()
        self._log.handlers.clear()
        return reporte

    def generate_report(self) -> "ImportReport":
        """
        Genera un reporte final estructurado con todas las estadísticas.
        """
        self.stats.tiempo_fin = time.time()
        self.stats.tiempo_total_seg = self.stats.tiempo_fin - self.stats.tiempo_inicio

        reporte = ImportReport(
            stats        = self.stats,
            errores      = self._errores.copy(),
            log_path     = self._log_path,
        )
        return reporte

    # ─── Internals ─────────────────────────────────────────────────────────

    def _separator(self) -> None:
        sep = "─" * 80
        self._log.debug(sep)


# ─────────────────────────────────────────────────────────────────────────────
# REPORTE FINAL — RESULTADO DEL LOGGING
# ─────────────────────────────────────────────────────────────────────────────

class ImportReport:
    """Resultado de la importación — generado por ImportLogger.finish()."""

    def __init__(
        self,
        stats  : ImportStats,
        errores: list[ErrorEntry],
        log_path: Path,
    ):
        self.stats   = stats
        self.errores = errores
        self.log_path = log_path

    def resumen_text(self) -> str:
        """Retorna un resumen legible del resultado de la importación."""
        s = self.stats
        errores = self.errores

        lineas = []


        lineas.append("╔══════════════════════════════════════════════════════════════╗")
        lineas.append("║          FRIMARAL BI — REPORTE DE IMPORTACIÓN               ║")
        lineas.append("╚══════════════════════════════════════════════════════════════╝")
        lineas.append(f"")
        lineas.append(f"  📄 Archivo          : {s.archivo}")
        lineas.append(f"  📋 Hoja             : {s.hoja_seleccionada or '—'}")
        lineas.append(f"  📊 Columnas         : {len(s.columnas_detectadas)} detectadas")
        lineas.append(f"  📝 Filas totales    : {s.filas_total:,}")
        lineas.append(f"  ✅ Filas importadas : {s.filas_importadas:,}")
        lineas.append(f"  ❌ Filas rechazadas : {s.filas_rechazadas:,}")
        lineas.append(f"  ⏱  Duración        : {s.duracion_str()}")
        lineas.append(f"  🕐 Inicio           : {datetime.fromtimestamp(s.tiempo_inicio).strftime('%H:%M:%S')}")
        lineas.append(f"  🕐 Fin              : {datetime.fromtimestamp(s.tiempo_fin).strftime('%H:%M:%S')}")
        lineas.append(f"")
        lineas.append(f"  🔴 Errores          : {s.errores_count}")
        lineas.append(f"  🟡 Advertencias     : {s.advertencias_count}")
        lineas.append(f"  📄 Log detallado    : {self.log_path}")
        lineas.append(f"")

        nuevos = s.nuevos_resumen()
        if any(nuevos.values()):
            lineas.append("  🆕 Elementos nuevos detectados:")
            if nuevos["empresas"] > 0:
                lineas.append(f"     Empresas  : {nuevos['empresas']}")
                for e in sorted(s.empresas_nuevas):
                    lineas.append(f"       • {e}")
            if nuevos["paises"] > 0:
                lineas.append(f"     Países    : {nuevos['paises']}")
                for p in sorted(s.paises_nuevos):
                    lineas.append(f"       • {p}")
            if nuevos["productos"] > 0:
                lineas.append(f"     Productos : {nuevos['productos']}")
                for p in sorted(s.productos_nuevos):
                    lineas.append(f"       • {p}")
        else:
            lineas.append("  🆕 Elementos nuevos : ninguno (catálogos actualizados)")

        lineas.append(f"")

        if errores:
            by_rule: dict[str, list[ErrorEntry]] = {}
            for e in errores:
                by_rule.setdefault(e.regla_id, []).append(e)

            lineas.append("  📋 Resumen de errores por regla:")
            for regla_id, entries in sorted(by_rule.items()):
                severities = {r.severity for r in entries}
                sev_str = ", ".join(severities)
                lineas.append(f"    {regla_id}  [{sev_str}]  —  {len(entries)} ocurrencia(s)")

        lineas.append(f"")


        lineas.append("  ─────────────────────────────────────────────────────────────")
        if s.errores_count == 0 and s.advertencias_count == 0:
            lineas.append("  ✅ IMPORTACIÓN COMPLETA — Sin errores ni advertencias")
        elif s.errores_count == 0:
            lineas.append("  ⚠️  IMPORTACIÓN COMPLETA CON ADVERTENCIAS")
        else:
            lineas.append(f"  ❌ IMPORTACIÓN FINALIZADA CON {s.errores_count} ERROR(ES)")
        lineas.append("  ─────────────────────────────────────────────────────────────")

        return "\n".join(lineas)

    def print_resumen(self) -> None:
        """Imprime el resumen en consola."""
        print(self.resumen_text())

    def errores_por_regla(self) -> dict[str, list[ErrorEntry]]:
        """Agrupa errores por regla_id."""
        result: dict[str, list[ErrorEntry]] = {}
        for e in self.errores:
            result.setdefault(e.regla_id, []).append(e)
        return result

    def errores_df(self) -> list[dict]:
        """Retorna los errores como lista de dicts (para exportar a pandas)."""
        return [
            {
                "regla_id" : e.regla_id,
                "severity" : e.severity,
                "fila"     : e.fila,
                "columna"  : e.columna,
                "valor"    : e.valor,
                "mensaje"  : e.mensaje,
                "timestamp": e.timestamp,
            }
            for e in self.errores
        ]

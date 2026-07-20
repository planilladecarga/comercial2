#!/usr/bin/env python3
"""
=================================================================================
run_importacion.py — CLI del Motor de Importación FRIMARAL BI
=================================================================================
Orquesta todo el pipeline de importación:

    1. Lectura del XLSB (importador.py)
    2. Validación de datos (validador.py)
    3. Normalización (normalizador.py)
    4. Construcción de catálogos (catalogos.py)
    5. Carga a SQLite (database.py)
    6. Generación del Libro Maestro BI (build_libro_maestro.py)

Uso:
    python run_importacion.py                                    # Sin archivo
    python run_importacion.py /ruta/al/archivo.xlsb            # Con archivo
    python run_importacion.py /ruta/al/archivo.xlsx --db mi.db # Con options

Opciones:
    --db          Ruta de la base SQLite (default: data/frimaral_bi.db)
    --hoja        Nombre de la hoja a importar (default: auto-detectar)
    --no-libro    No generar el libro maestro BI
    --reset-db    Eliminar BD existente antes de importar
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.logger        import ImportLogger
from src.importador    import XLSBImporter
from src.validador     import DataValidator
from src.normalizador  import DataNormalizer
from src.catalogos     import CatalogoBuilder
from src.database      import FRIMARALDatabase
from config            import DATA_DIR, DB_DIR


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    xlsb_path    : str,
    db_path      : str,
    hoja         : str | None,
    generar_libro: bool,
    reset_db     : bool,
) -> bool:
    """
    Ejecuta el pipeline completo de importación.

    Returns:
        True si la importación fue exitosa, False en caso contrario.
    """
    print()
    print("=" * 80)
    print("  FRIMARAL BI — Motor de Importación  v1.0.0")
    print("=" * 80)
    print()

    # ── 0. Setup inicial ─────────────────────────────────────────────────
    if reset_db and Path(db_path).exists():
        Path(db_path).unlink()
        print(f"  🗑  BD anterior eliminada: {db_path}")

    # Logger
    logger = ImportLogger(xlsb_path or "sin_archivo")
    db     = FRIMARALDatabase(db_path)
    db.set_logger(logger)

    # Crear esquema
    db.crear_esquema()

    # ── 1. Lectura ──────────────────────────────────────────────────────
    import pandas as pd
    if not xlsb_path:
        logger.warning("No se proporcionó archivo XLSB — generando Libro Maestro vacío")
        logger.set_filas(0)
        df_raw = pd.DataFrame()
    else:
        importer = XLSBImporter(xlsb_path, logger)
        result   = importer.read(hoja=hoja)
        df_raw   = result.df
        logger.set_filas(result.filas_total)

    # ── 2. Validación ───────────────────────────────────────────────────
    if xlsb_path:
        logger.info("Archivo proporcionado — ejecutando validación...")
        validator  = DataValidator(df_raw, logger)
        df_valid, df_rech = validator.validate()
        logger.stats.filas_rechazadas = len(df_rech)
        logger.stats.filas_importadas = len(df_valid)
    else:
        # Sin archivo: crear DF vacío para demo
        import pandas as pd
        df_valid = pd.DataFrame()
        logger.info("Generando estructura sin datos...")

    # ── 3. Normalización ─────────────────────────────────────────────────
    if not df_valid.empty:
        normalizer = DataNormalizer(df_valid, logger)
        df_norm    = normalizer.normalize()
    else:
        import pandas as pd
        df_norm = pd.DataFrame()
        logger.info("Sin datos para normalizar")

    # ── 4. Catálogos ────────────────────────────────────────────────────
    catalogo_builder = CatalogoBuilder(df_norm, logger)
    catalogos        = catalogo_builder.build_all()

    # ── 5. Carga a SQLite ───────────────────────────────────────────────
    logger.separator()
    logger.info("ETAPA 5 — Carga a base de datos SQLite")

    db.insertar_dimension("empresas",  catalogos.empresas)
    db.insertar_dimension("paises",   catalogos.paises)
    db.insertar_dimension("productos", catalogos.productos)
    db.insertar_calendario(catalogos.calendario)

    db.insertar_movimientos(df_norm, catalogos.as_dict())

    # Guardar log en BD
    report = logger.generate_report()
    db.insertar_log(report)

    # ── 6. Generación del Libro Maestro BI ──────────────────────────────
    if generar_libro:
        logger.separator()
        logger.info("ETAPA 6 — Generando Libro Maestro BI...")

        try:
            from build_libro_maestro import build_libro_maestro
            excel_path = build_libro_maestro(
                xlsb_path=xlsb_path,
                output_path=str(DATA_DIR / "FRIMARAL_BI_Libro_Maestro_v1_0_0.xlsx"),
            )
            logger.success(f"Libro Maestro generado: {excel_path}")
        except Exception as e:
            logger.warning(f"No se pudo generar el Libro Maestro: {e}")

    # ── 7. Resumen final ────────────────────────────────────────────────
    print()
    print(report.resumen_text())

    # Resumen de BD
    print("\n  📊 Resumen de la Base de Datos:")
    resumen = db.resumen()
    for tabla, count in resumen.items():
        print(f"    {tabla:30s}: {count:>8,} filas")

    db.cerrar()

    ok = logger.stats.errores_count == 0
    logger.finish()

    return ok


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FRIMARAL BI — Motor de Importación de archivos MGAP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_importacion.py                                     # Demo sin archivo
  python run_importacion.py datos.xlsb                          # Importar archivo
  python run_importacion.py datos.xlsb --db mi_db.db             # BD custom
  python run_importacion.py datos.xlsb --hoja "MOVIMIENTOS"     # Hoja específica
  python run_importacion.py datos.xlsb --reset-db                # Reiniciar BD
  python run_importacion.py datos.xlsb --no-libro               # Sin Excel
        """,
    )

    parser.add_argument(
        "archivo",
        nargs="?",
        default=None,
        help="Ruta al archivo XLSB/XLSX del MGAP",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Ruta de la base SQLite (default: data/frimaral_bi.db)",
    )
    parser.add_argument(
        "--hoja",
        default=None,
        help="Nombre de la hoja a importar (default: auto-detectar)",
    )
    parser.add_argument(
        "--no-libro",
        action="store_true",
        help="No generar el Libro Maestro BI en Excel",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Eliminar la base SQLite existente antes de importar",
    )

    args = parser.parse_args()

    # Verificar archivo
    if args.archivo and not Path(args.archivo).exists():
        print(f"❌  Error: archivo no encontrado: {args.archivo}")
        sys.exit(1)

    if args.db is None:
        db_path_abs = Path(__file__).parent / "data" / "frimaral_bi.db"
    else:
        db_path_abs = Path(args.db)

    # Ejecutar
    ok = run_pipeline(
        xlsb_path     = args.archivo,
        db_path       = str(db_path_abs),
        hoja          = args.hoja,
        generar_libro = not args.no_libro,
        reset_db      = args.reset_db,
    )

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

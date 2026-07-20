"""
Configuración centralizada del API del Centro de Comando Comercial.
"""
from pathlib import Path

# Ruta base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Base de datos SQLite
DB_PATH = BASE_DIR / "data" / "frimaral_bi.db"

# Servidor
HOST = "0.0.0.0"
PORT = 8000

# Umbrales de alertas
UMBRAL_DEPENDENCIA_CLIENTE = 40.0    # %
UMBRAL_CONCENTRACION_MERCADO = 70.0  # %
UMBRAL_CAIDA = -20.0                 # %
UMBRAL_MONOPRODUCTO = 80.0           # %
UMBRAL_CRECIMIENTO_ALTO = 30.0       # %
UMBRAL_DISMINUCION_IMPORTANTE = -30.0  # %
DIAS_INACTIVO = 60
DIAS_NUEVO = 90                      # días para considerar "nuevo"

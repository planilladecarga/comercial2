# FRIMARAL BI - API Centro de Comando Comercial

## Sprint 6

API REST para el Dashboard Ejecutivo del Director Comercial.

## Estructura

```
api/
├── main.py              # FastAPI app
├── config.py            # Configuración
├── database.py          # Conexión SQLite
├── models/              # Modelos de datos
├── queries/             # Consultas SQL centralizadas
├── routes/              # Rutas API
└── services/            # Lógica de negocio
```

## Ejecutar

```bash
cd frimaral_bi/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /api/comando/resumen` - Resumen ejecutivo
- `GET /api/comando/alertas` - Alertas del día
- `GET /api/comando/oportunidades` - Oportunidades
- `GET /api/comando/competencia` - Comparación competitiva
- `GET /api/comando/indicadores` - KPIs
- `GET /api/comando/mapa` - Mapa comercial
- `GET /api/comando/evolucion` - Evolución mensual
- `GET /api/comando/rankings` - Top rankings
- `GET /api/comando/filtros` - Filtros disponibles
- `GET /api/comando/completo` - Todos los datos
- `GET /health` - Health check

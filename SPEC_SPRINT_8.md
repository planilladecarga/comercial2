# SPEC.md — SPRINT 8: Commercial Intelligence Engine

## 1. Concepto & Visión

FRIMARAL BI deja de ser un sistema de consulta y se transforma en un **sistema de apoyo a la decisión comercial**. El Commercial Intelligence Engine analiza automáticamente los datos de cada empresa (Productor, Depósito, Certificador, Cliente, Mercado) y genera:

- **Score Comercial (0-100)**: Puntaje único que resume la salud comercial
- **Nivel de Riesgo**: BAJO / MEDIO / ALTO / CRÍTICO
- **Nivel de Potencial**: MUY ALTO / ALTO / MEDIO / BAJO
- **Nivel de Fidelidad**: MUY ALTA / ALTA / MEDIA / BAJA / MUY BAJA
- **Alertas de Dependencia**: Detección de concentración excesiva
- **Recomendaciones Accionables**: Acciones específicas para el equipo comercial
- **Rankings Automáticos**: Top oportunidades, riesgos, crecimiento, etc.

**Principio fundamental**: Cada Score debe ser 100% explicable. El usuario siempre entiende por qué obtuvo ese resultado.

---

## 2. Arquitectura Modular

```
commercial_intelligence/
├── __init__.py
├── motor_comercial.py          # Orquestador principal
├── scoring/
│   ├── __init__.py
│   ├── scoring_service.py      # Calcula Score Comercial 0-100
│   ├── factors/
│   │   ├── __init__.py
│   │   ├── volumen_factor.py   # Factor: Volumen Total
│   │   ├── frecuencia_factor.py # Factor: Frecuencia de Movimientos
│   │   ├── crecimiento_factor.py # Factor: Crecimiento
│   │   ├── caida_factor.py     # Factor: Caída
│   │   ├── mercado_div_factor.py # Factor: Diversificación Mercados
│   │   ├── producto_div_factor.py # Factor: Diversificación Productos
│   │   ├── depositos_factor.py  # Factor: Cantidad Depósitos
│   │   ├── certificadores_factor.py # Factor: Cantidad Certificadores
│   │   ├── estabilidad_factor.py # Factor: Estabilidad Comercial
│   │   └── historial_factor.py  # Factor: Historial
│   └── models.py               # ScoreResult, FactorResult, ScoreBreakdown
├── rules/
│   ├── __init__.py
│   ├── rules_engine.py         # Motor de reglas configurables
│   ├── rule.py                 # Modelo Rule
│   └── rule_repository.py      # Acceso a reglas en BD
├── recommendations/
│   ├── __init__.py
│   ├── recommendation_engine.py # Generador de recomendaciones
│   └── recommendation_types.py # Tipos de recomendación
├── risk/
│   ├── __init__.py
│   ├── risk_engine.py          # Motor de riesgo
│   └── risk_levels.py          # Niveles de riesgo
├── opportunity/
│   ├── __init__.py
│   └── opportunity_engine.py   # Motor de oportunidad
├── configuration/
│   ├── __init__.py
│   ├── config_repository.py    # Repositorio de configuración
│   └── default_config.py       # Configuración por defecto
├── rankings/
│   ├── __init__.py
│   └── rankings_generator.py   # Generador de rankings
└── indicators/
    ├── __init__.py
    └── indicators_calculator.py # Calculador de indicadores
```

---

## 3. Modelo de Datos

### Tabla: `config_scores`
Almacena los pesos de cada factor del Score.

```sql
CREATE TABLE config_scores (
    id_config INTEGER PRIMARY KEY,
    factor_key TEXT UNIQUE NOT NULL,  -- 'volumen', 'frecuencia', 'crecimiento', etc.
    factor_nombre TEXT NOT NULL,
    peso_default REAL NOT NULL,        -- Peso base (0-100)
    peso_actual REAL NOT NULL,         -- Peso configurable
    peso_min REAL NOT NULL,            -- Límite inferior
    peso_max REAL NOT NULL,            -- Límite superior
    activo INTEGER DEFAULT 1,
    fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: `config_reglas`
Almacena las reglas del motor de recomendaciones.

```sql
CREATE TABLE config_reglas (
    id_regla INTEGER PRIMARY KEY,
    regla_id TEXT UNIQUE NOT NULL,      -- 'REC001', 'REC002', etc.
    nombre TEXT NOT NULL,
    descripcion TEXT,
    prioridad INTEGER DEFAULT 50,       -- 1-100 (mayor = más importante)
    tipo_evaluacion TEXT NOT NULL,      -- 'SCORE', 'RIESGO', 'CRECIMIENTO', 'FRECUENCIA'
    condicion_json TEXT NOT NULL,       -- JSON con la condición
    recomendacion_json TEXT NOT NULL,   -- JSON con la recomendación
    estado INTEGER DEFAULT 1,           -- 1=activo, 0=inactivo
    categoria TEXT,                     -- 'CAPTACION', 'RETENCION', 'RECUPERACION', 'SEGUIMIENTO'
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: `scores_empresa`
Score calculado por empresa.

```sql
CREATE TABLE scores_empresa (
    id_score INTEGER PRIMARY KEY,
    id_empresa INTEGER NOT NULL,
    tipo_empresa TEXT NOT NULL,         -- 'PRODUCTOR', 'DEPOSITO', 'CERTIFICADOR', 'CLIENTE', 'MERCADO'
    score_total REAL NOT NULL,          -- 0-100
    nivel_riesgo TEXT NOT NULL,         -- 'BAJO', 'MEDIO', 'ALTO', 'CRITICO'
    nivel_potencial TEXT NOT NULL,      -- 'MUY_ALTO', 'ALTO', 'MEDIO', 'BAJO'
    nivel_fidelidad TEXT NOT NULL,      -- 'MUY_ALTA', 'ALTA', 'MEDIA', 'BAJA', 'MUY_BAJA'
    nivel_dependencia TEXT,              -- 'ALTA', 'MEDIA', 'BAJA'
    breakdown_json TEXT NOT NULL,       -- JSON con desglose de factores
    fecha_calculo TEXT NOT NULL,
    periodo_evaluado TEXT,               -- 'ultimos_6_meses', 'ultimo_anio', etc.
    FOREIGN KEY (id_empresa) REFERENCES dim_empresas(id_empresa)
);
```

### Tabla: `recomendaciones`
Recomendaciones generadas.

```sql
CREATE TABLE recomendaciones (
    id_recomendacion INTEGER PRIMARY KEY,
    id_empresa INTEGER NOT NULL,
    regla_id TEXT NOT NULL,
    recomendacion TEXT NOT NULL,
    prioridad INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    estado TEXT DEFAULT 'PENDIENTE',     -- 'PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'DESCARTADA'
    fecha_generacion TEXT NOT NULL,
    fecha_resolucion TEXT,
    notas TEXT,
    FOREIGN KEY (id_empresa) REFERENCES dim_empresas(id_empresa),
    FOREIGN KEY (regla_id) REFERENCES config_reglas(regla_id)
);
```

### Tabla: `rankings`
Rankings pre-calculados.

```sql
CREATE TABLE rankings (
    id_ranking INTEGER PRIMARY KEY,
    tipo_ranking TEXT NOT NULL,         -- 'TOP_OPORTUNIDADES', 'TOP_RIESGOS', 'TOP_CRECIMIENTO', etc.
    id_empresa INTEGER NOT NULL,
    posicion INTEGER NOT NULL,
    score_parcial REAL,                 -- Score que determinó la posición
    metricas_json TEXT,                 -- Métricas relevantes
    fecha_calculo TEXT NOT NULL,
    periodo_evaluado TEXT,
    FOREIGN KEY (id_empresa) REFERENCES dim_empresas(id_empresa)
);
```

---

## 4. Factores del Score Comercial

Cada factor devuelve un valor 0-100 y tiene un peso configurable.

| Factor | Key | Descripción | Peso Default |
|--------|-----|-------------|--------------|
| Volumen Total | `volumen` | Kg totales vs promedio del sector | 20 |
| Frecuencia | `frecuencia` | Cantidad de movimientos vs período anterior | 15 |
| Crecimiento | `crecimiento` | Variación % de volumen vs período anterior | 20 |
| Caída | `caida` | Detecta disminución sostenida (invertido) | 15 |
| Diversificación Mercados | `mercado_div` | Cantidad de mercados únicos | 10 |
| Diversificación Productos | `producto_div` | Cantidad de productos únicos | 10 |
| Depósitos | `depositos` | Cantidad de depósitos utilizados | 5 |
| Certificadores | `certificadores` | Cantidad de certificadores | 5 |

### Cálculo del Score

```
Score = Σ (factor_valor × factor_peso) / Σ pesos
```

---

## 5. Niveles de Riesgo

| Nivel | Condición |
|-------|-----------|
| **BAJO** | Score >= 70 Y sin factores negativos |
| **MEDIO** | Score 50-69 O algún factor en decaimiento |
| **ALTO** | Score 30-49 O caída > 20% |
| **CRÍTICO** | Score < 30 O caída > 40% O inactivo > 90 días |

### Señales de Riesgo
- Disminución sostenida de movimientos (3+ meses consecutivos)
- Cambio frecuente de depósito (>50% cambio en últimos 6 meses)
- Pérdida de mercados (mercados perdidos vs gained)
- Reducción de volumen >20%
- Inactividad > 60 días

---

## 6. Niveles de Potencial

| Nivel | Condición |
|-------|-----------|
| **MUY ALTO** | Crecimiento >50% Y diversificación alta |
| **ALTO** | Crecimiento >20% O penetración en nuevos mercados |
| **MEDIO** | Crecimiento 0-20% Y sin factores negativos |
| **BAJO** | Sin crecimiento O sin diversificación |

---

## 7. Niveles de Fidelidad

| Nivel | Condición |
|-------|-----------|
| **MUY ALTA** | >3 años Y mismo depósito principal |
| **ALTA** | >1 año Y <2 cambios de depósito |
| **MEDIA** | >6 meses Y sin cambios recientes |
| **BAJA** | <6 meses O cambios frecuentes |
| **MUY BAJA** | <3 meses O nuevo cliente |

---

## 8. Motor de Reglas

### Estructura de Regla

```python
@dataclass
class Rule:
    regla_id: str           # 'REC001'
    nombre: str             # 'Productor en crecimiento sin multi-depósito'
    descripcion: str        # 'Productores con >30% crecimiento que usan un solo depósito'
    prioridad: int          # 1-100
    tipo_evaluacion: str   # 'SCORE', 'RIESGO', 'CRECIMIENTO', etc.
    condicion: dict         # Condición en JSON
    recomendacion: dict     # Recomendación a generar
    estado: bool            # Activo/Inactivo
    categoria: str          # 'CAPTACION', 'RETENCION', 'RECUPERACION', 'SEGUIMIENTO'
```

### Tipos de Condición

```python
# Operadores disponibles
OPERATORS = ['gt', 'gte', 'lt', 'lte', 'eq', 'neq', 'in', 'not_in', 'between', 'contains']

# Ejemplo de condición JSON
{
    "operator": "and",
    "conditions": [
        {"field": "crecimiento_pct", "operator": "gt", "value": 30},
        {"field": "cant_depositos", "operator": "eq", "value": 1}
    ]
}
```

---

## 9. Recomendaciones Predefinidas

| ID | Nombre | Categoría | Prioridad |
|----|--------|-----------|-----------|
| REC001 | Programar visita comercial | SEGUIMIENTO | 80 |
| REC002 | Contactar nuevamente | RETENCION | 75 |
| REC003 | Recuperar cliente | RECUPERACION | 90 |
| REC004 | Mantener seguimiento | SEGUIMIENTO | 50 |
| REC005 | Analizar crecimiento | ANALISIS | 60 |
| REC006 | Explorar nuevos mercados | CAPTACION | 70 |
| REC007 | Analizar competencia | ANALISIS | 55 |
| REC008 | Proponer contrato multi-depósito | CAPTACION | 85 |
| REC009 | Alerta de dependencia excesiva | ALERTA | 95 |
| REC010 | Revisar situación de riesgo | ALERTA | 90 |

---

## 10. Rankings Automáticos

| Ranking | Descripción | Orden |
|---------|-------------|-------|
| `TOP_OPORTUNIDADES` | Empresas con mayor potencial de crecimiento | DESC por potencial |
| `TOP_RIESGOS` | Empresas con mayor riesgo detectado | DESC por riesgo |
| `TOP_CRECIMIENTO` | Empresas con mayor crecimiento % | DESC por crecimiento |
| `TOP_FIDELIDAD` | Empresas con mayor fidelidad | DESC por fidelidad |
| `TOP_PRODUCTORES` | Productores con mayor volumen | DESC por volumen |
| `TOP_MERCADOS` | Mercados con mayor volumen total | DESC por volumen |
| `TOP_COMPETIDORES` | Competidores con mayor participación | DESC por participación |

---

## 11. Indicadores Calculados

| Indicador | Descripción | Rango |
|------------|-------------|-------|
| `OPPORTUNITY_SCORE` | Potencial de oportunidad (0-100) | 0-100 |
| `RISK_SCORE` | Nivel de riesgo (0-100, menor es mejor) | 0-100 |
| `LOYALTY_SCORE` | Índice de fidelidad (0-100) | 0-100 |
| `GROWTH_SCORE` | Índice de crecimiento (0-100) | 0-100 |
| `DIVERSIFICATION_SCORE` | Índice de diversificación (0-100) | 0-100 |
| `COMPETITIVENESS_SCORE` | Índice de competitividad (0-100) | 0-100 |

---

## 12. Explicabilidad del Score

Cada Score incluye:

```python
@dataclass
class ScoreBreakdown:
    score_total: float
    nivel: str
    factores: List[FactorDetail]
    fecha_calculo: str
    periodo_evaluado: str

@dataclass
class FactorDetail:
    factor_key: str
    factor_nombre: str
    valor: float              # 0-100
    peso: float              # Peso configurado
    contribucion: float      # valor × peso / total
    comparacion_periodo: str # 'vs_mes_anterior', 'vs_promedio_sector'
    detalle: str             # '15,000 kg vs 12,000 kg promedio (+25%)'
```

---

## 13. Interfaces de Salida

### Para Dashboard Ejecutivo
```python
{
    "resumen_ejecutivo": {
        "total_empresas_analizadas": 150,
        "promedio_score": 62.5,
        "distribucion_riesgo": {"BAJO": 45, "MEDIO": 60, "ALTO": 35, "CRITICO": 10},
        "total_recomendaciones": 234,
        "rankings": {...}
    }
}
```

### Para Empresa360
```python
{
    "empresa_id": 5,
    "nombre": "CALIRAL",
    "score_comercial": 78.5,
    "nivel_riesgo": "MEDIO",
    "nivel_potencial": "ALTO",
    "nivel_fidelidad": "ALTA",
    "breakdown": {...},
    "recomendaciones": [...],
    "alertas": [...],
    "historial_scores": [...]
}
```

### Para Business Query Engine
```python
{
    "query": "scores_empresa",
    "filters": {
        "tipo_empresa": "PRODUCTOR",
        "nivel_riesgo": ["ALTO", "CRITICO"],
        "periodo": "ultimos_6_meses"
    },
    "columns": ["nombre", "score_total", "nivel_riesgo", ...]
}
```

---

## 14. API Endpoints

```
GET  /api/v1/commercial-intelligence/scores
GET  /api/v1/commercial-intelligence/scores/{id_empresa}
GET  /api/v1/commercial-intelligence/scores/{id_empresa}/breakdown
GET  /api/v1/commercial-intelligence/riesgos
GET  /api/v1/commercial-intelligence/riesgos/{id_empresa}
GET  /api/v1/commercial-intelligence/oportunidades
GET  /api/v1/commercial-intelligence/recomendaciones
POST /api/v1/commercial-intelligence/recomendaciones/{id}/actualizar
GET  /api/v1/commercial-intelligence/rankings/{tipo_ranking}
GET  /api/v1/commercial-intelligence/indicadores
GET  /api/v1/commercial-intelligence/indicadores/{id_empresa}
GET  /api/v1/commercial-intelligence/config/factores
PUT  /api/v1/commercial-intelligence/config/factores/{factor_key}
GET  /api/v1/commercial-intelligence/config/reglas
PUT  /api/v1/commercial-intelligence/config/reglas/{regla_id}
POST /api/v1/commercial-intelligence/calcular-todo
```

---

## 15. Principios de Calidad

- **Código Limpio**: Sin código duplicado, funciones pequeñas
- **SOLID**: 
  - S: Cada factor es responsable de una sola cosa
  - O: Nuevos factores sin modificar existentes
  - L: Scores específicos heredan de interfaz común
  - I: Interfaces pequeñas y específicas
  - D: Configuración inyectada, no hardcodeada
- **TypeScript Estricto**: type hints en Python, validación de tipos
- **Pruebas Unitarias**: pytest con >80% coverage en scoring, rules, recommendations
- **Pruebas de Integración**: Tests contra BD real
- **ML-Ready**: Arquitectura preparada para agregar modelos predictivos en el futuro

---

## 16. Dependencias con Módulos Existentes

```
commercial_intelligence/
├── Repositorio (empresa360/repositorio.py) — Acceso a datos
├── MotorCompetitivo (competitive_intelligence/motor_competitivo.py) — Índices existentes
├── Database (api/database.py) — Conexión BD
└── Config (api/config.py) — Configuración general
```

---

## 17. Entregables del Sprint 8

1. ✅ Tablas de configuración (`config_scores`, `config_reglas`, `scores_empresa`, `recomendaciones`, `rankings`)
2. ✅ ScoringService con 8 factores configurables
3. ✅ RulesEngine con condiciones JSON evaluables
4. ✅ RecommendationEngine con recomendaciones predefinidas
5. ✅ RiskEngine con niveles BAJO/MEDIO/ALTO/CRÍTICO
6. ✅ OpportunityEngine con niveles de potencial
7. ✅ LoyaltyEngine para calcular fidelidad
8. ✅ DependenceEngine para detectar concentración
9. ✅ RankingsGenerator para 7 rankings automáticos
10. ✅ IndicatorsCalculator para 6 indicadores
11. ✅ API endpoints completos
12. ✅ Tests unitarios (>80% coverage)
13. ✅ Documentación de explicabilidad

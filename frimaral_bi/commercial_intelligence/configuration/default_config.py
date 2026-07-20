"""
=================================================================================
default_config.py — Configuración por Defecto
=================================================================================
"""

# Configuración de factores por defecto
DEFAULT_SCORES_CONFIG = [
    {
        "factor_key": "volumen",
        "factor_nombre": "Volumen Total",
        "peso_default": 20,
        "peso_actual": 20,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "frecuencia",
        "factor_nombre": "Frecuencia de Movimientos",
        "peso_default": 15,
        "peso_actual": 15,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "crecimiento",
        "factor_nombre": "Crecimiento",
        "peso_default": 20,
        "peso_actual": 20,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "caida",
        "factor_nombre": "Caída / Estabilidad",
        "peso_default": 15,
        "peso_actual": 15,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "mercado_div",
        "factor_nombre": "Diversificación de Mercados",
        "peso_default": 10,
        "peso_actual": 10,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "producto_div",
        "factor_nombre": "Diversificación de Productos",
        "peso_default": 10,
        "peso_actual": 10,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "depositos",
        "factor_nombre": "Cantidad de Depósitos",
        "peso_default": 5,
        "peso_actual": 5,
        "peso_min": 0,
        "peso_max": 100,
    },
    {
        "factor_key": "certificadores",
        "factor_nombre": "Cantidad de Certificadores",
        "peso_default": 5,
        "peso_actual": 5,
        "peso_min": 0,
        "peso_max": 100,
    },
]

# Reglas por defecto
DEFAULT_RULES = [
    {
        "regla_id": "REC001",
        "nombre": "Programar visita comercial",
        "descripcion": "Empresa con score medio-bajo requiere atención personalizada",
        "prioridad": 80,
        "tipo_evaluacion": "SCORE",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "score_total", "operator": "gte", "value": 30},
                {"field": "score_total", "operator": "lt", "value": 60},
            ]
        },
        "recomendacion": {"texto": "Programar visita comercial para evaluar situación"},
        "estado": 1,
        "categoria": "SEGUIMIENTO",
    },
    {
        "regla_id": "REC002",
        "nombre": "Contactar nuevamente",
        "descripcion": "Empresa con disminución de actividad",
        "prioridad": 75,
        "tipo_evaluacion": "CRECIMIENTO",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "factor_crecimiento", "operator": "lt", "value": 50},
                {"field": "cant_movimientos", "operator": "gte", "value": 5},
            ]
        },
        "recomendacion": {"texto": "Contactar para conocer situación y ofrecer apoyo"},
        "estado": 1,
        "categoria": "RETENCION",
    },
    {
        "regla_id": "REC003",
        "nombre": "Recuperar cliente",
        "descripcion": "Empresa con caída significativa o inactiva",
        "prioridad": 90,
        "tipo_evaluacion": "RIESGO",
        "condicion": {
            "operator": "or",
            "conditions": [
                {"field": "factor_caida", "operator": "lt", "value": 30},
                {"field": "cant_movimientos", "operator": "eq", "value": 0},
            ]
        },
        "recomendacion": {"texto": "Priorizar recuperación - empresa en riesgo"},
        "estado": 1,
        "categoria": "RECUPERACION",
    },
    {
        "regla_id": "REC004",
        "nombre": "Mantener seguimiento",
        "descripcion": "Empresa estable con buen performance",
        "prioridad": 50,
        "tipo_evaluacion": "SCORE",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "score_total", "operator": "gte", "value": 70},
            ]
        },
        "recomendacion": {"texto": "Mantener seguimiento regular"},
        "estado": 1,
        "categoria": "SEGUIMIENTO",
    },
    {
        "regla_id": "REC005",
        "nombre": "Analizar crecimiento",
        "descripcion": "Empresa con alto crecimiento - analizar tendencias",
        "prioridad": 60,
        "tipo_evaluacion": "CRECIMIENTO",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "factor_crecimiento", "operator": "gt", "value": 80},
            ]
        },
        "recomendacion": {"texto": "Analizar factores del crecimiento para replicar"},
        "estado": 1,
        "categoria": "ANALISIS",
    },
    {
        "regla_id": "REC006",
        "nombre": "Explorar nuevos mercados",
        "descripcion": "Empresa con alto crecimiento pero baja diversificación",
        "prioridad": 70,
        "tipo_evaluacion": "DIVERSIFICACION",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "factor_crecimiento", "operator": "gt", "value": 70},
                {"field": "factor_mercado_div", "operator": "lt", "value": 50},
            ]
        },
        "recomendacion": {"texto": "Explorar expansión a nuevos mercados"},
        "estado": 1,
        "categoria": "CAPTACION",
    },
    {
        "regla_id": "REC007",
        "nombre": "Analizar competencia",
        "descripcion": "Empresa presente en mercados con alta competencia",
        "prioridad": 55,
        "tipo_evaluacion": "RIESGO",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "cant_mercados", "operator": "gte", "value": 3},
            ]
        },
        "recomendacion": {"texto": "Analizar posicionamiento frente a competidores"},
        "estado": 1,
        "categoria": "ANALISIS",
    },
    {
        "regla_id": "REC008",
        "nombre": "Proponer contrato multi-depósito",
        "descripcion": "Productor en crecimiento usando un solo depósito",
        "prioridad": 85,
        "tipo_evaluacion": "VOLUMEN",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "factor_crecimiento", "operator": "gt", "value": 60},
                {"field": "depositos", "operator": "eq", "value": 1},
            ]
        },
        "recomendacion": {"texto": "Proponer contrato multi-depósito para capturar más volumen"},
        "estado": 1,
        "categoria": "CAPTACION",
    },
    {
        "regla_id": "REC009",
        "nombre": "Alerta de dependencia excesiva",
        "descripcion": "Cliente representa más del 70% del negocio",
        "prioridad": 95,
        "tipo_evaluacion": "RIESGO",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "cant_mercados", "operator": "eq", "value": 1},
            ]
        },
        "recomendacion": {"texto": "ALERTA: Dependencia excesiva de un solo mercado"},
        "estado": 1,
        "categoria": "ALERTA",
    },
    {
        "regla_id": "REC010",
        "nombre": "Revisar situación de riesgo",
        "descripcion": "Empresa con múltiples factores de riesgo",
        "prioridad": 90,
        "tipo_evaluacion": "RIESGO",
        "condicion": {
            "operator": "and",
            "conditions": [
                {"field": "score_total", "operator": "lt", "value": 40},
            ]
        },
        "recomendacion": {"texto": "Revisar urgentemente - múltiples factores de riesgo"},
        "estado": 1,
        "categoria": "ALERTA",
    },
]

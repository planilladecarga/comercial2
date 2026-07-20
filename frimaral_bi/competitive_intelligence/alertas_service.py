"""
=================================================================================
alertas_service.py — Sistema de alertas de riesgos comerciales
=================================================================================

Detecta automáticamente riesgos comerciales:
    • Dependencia excesiva de un cliente (>40% del volumen)
    • Caída de participación en mercado
    • Concentración de mercados
    • Clientes inactivos
    • Mercados en descenso
    • Caída superior al 20% vs mes anterior
    • Productores que migraron a competidores
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from competitive_intelligence.repositorio import RepositorioCIE


@dataclass
class AlertaRiesgo:
    """Una alerta de riesgo detectada."""
    codigo  : str   # ej: "RIE001"
    tipo    : str   # "CRITICAL" | "WARNING" | "INFO"
    riesgo  : str   # Nombre del riesgo
    detalle : str
    magnitud: float  # % o valor que triggering
    prioridad: int   # 0=baja, 1=media, 2=alta

    @property
    def emoji(self) -> str:
        return {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}.get(
            self.tipo, "🔔")


@dataclass
class AlertasRiesgo:
    """Conjunto de alertas de riesgo para una empresa."""
    alertas       : list[AlertaRiesgo] = field(default_factory=list)
    count_criticos: int = 0
    count_warning : int = 0
    count_info    : int = 0

    @property
    def total(self) -> int:
        return len(self.alertas)


class AlertasService:
    """
    Detecta riesgos comerciales automáticamente.

    Códigos de alerta:
        RIE001 — Dependencia excesiva de cliente (>40% kg)
        RIE002 — Concentración de mercado (>70% en un mercado)
        RIE003 — Caída de volumen >20% vs mes anterior
        RIE004 — Cliente inactivo (>60 días sin movimiento)
        RIE005 — Mercado en descenso (>20% caída)
        RIE006 — Dependencia de un solo producto (>80% kg)
        RIE007 — Productores migran a competidores
        RIE008 — Sin actividad reciente (>60 días)
        RIE009 — Caída sostenida (3 meses consecutivos en baja)

    Uso:
        alertas = AlertasService(repo)
        riesgos = alertas.detectar(id_empresa=5)
    """

    UMBRAL_DEPENDENCIA_CLIENTE = 40.0   # %
    UMBRAL_CONCENTRACION_MERCADO = 70.0  # %
    UMBRAL_CAIDA = -20.0                # %
    UMBRAL_MONOPRODUCTO = 80.0          # %
    DIAS_INACTIVO = 60

    def __init__(self, repo: RepositorioCIE):
        self.repo = repo

    def detectar(self, id_empresa: int) -> AlertasRiesgo:
        """Detecta todos los riesgos para una empresa."""
        alertas: list[AlertaRiesgo] = []
        kg_total = self.repo.kg_total_empresa(id_empresa)

        if kg_total == 0:
            return AlertasRiesgo()

        # RIE001 — Dependencia excesiva de cliente
        alertas.extend(self._dependencia_cliente(id_empresa, kg_total))

        # RIE002 — Concentración de mercado
        alertas.extend(self._concentracion_mercado(id_empresa, kg_total))

        # RIE003 — Caída de volumen
        alertas.extend(self._caida_volumen(id_empresa))

        # RIE004 — Clientes inactivos
        alertas.extend(self._clientes_inactivos(id_empresa))

        # RIE006 — Monoproducto
        alertas.extend(self._monoproducto(id_empresa, kg_total))

        # RIE007 — Migración a competidores
        alertas.extend(self._migracion_competidores(id_empresa))

        # RIE008 — Sin actividad reciente
        alertas.extend(self._inactividad(id_empresa))

        # Ordenar por prioridad
        alertas.sort(key=lambda a: a.prioridad, reverse=True)

        return AlertasRiesgo(
            alertas        = alertas,
            count_criticos = sum(1 for a in alertas if a.tipo == "CRITICAL"),
            count_warning  = sum(1 for a in alertas if a.tipo == "WARNING"),
            count_info     = sum(1 for a in alertas if a.tipo == "INFO"),
        )

    def _dependencia_cliente(
        self, id_empresa: int, kg_total: float
    ) -> list[AlertaRiesgo]:
        alertas = []
        clis = self.repo.clientes_empresa(id_empresa)
        for c in clis:
            pct = (c["kg_total"] or 0) / kg_total * 100
            if pct > self.UMBRAL_DEPENDENCIA_CLIENTE:
                alertas.append(AlertaRiesgo(
                    codigo   = "RIE001",
                    tipo     = "CRITICAL" if pct > 60 else "WARNING",
                    riesgo   = f"Dependencia excesiva de cliente: {c['cliente']}",
                    detalle  = f"{pct:.1f}% del volumen total proviene de un solo cliente",
                    magnitud= pct,
                    prioridad = 2 if pct > 60 else 1,
                ))
        return alertas

    def _concentracion_mercado(
        self, id_empresa: int, kg_total: float
    ) -> list[AlertaRiesgo]:
        alertas = []
        mercs = self.repo.mercados_empresa(id_empresa)
        for m in mercs:
            pct = (m["kg_total"] or 0) / kg_total * 100
            if pct > self.UMBRAL_CONCENTRACION_MERCADO:
                alertas.append(AlertaRiesgo(
                    codigo   = "RIE002",
                    tipo     = "WARNING",
                    riesgo   = f"Concentración de mercado: {m['mercado']}",
                    detalle  = f"{pct:.1f}% del volumen en un solo mercado",
                    magnitud= pct,
                    prioridad = 1,
                ))
        return alertas

    def _caida_volumen(
        self, id_empresa: int
    ) -> list[AlertaRiesgo]:
        alertas = []
        from datetime import datetime
        evolucion = self.repo.kg_empresa_por_mes(id_empresa)
        if len(evolucion) < 2:
            return alertas

        actual  = evolucion[-1]
        anterior = evolucion[-2]
        var = ((actual["kg_total"] or 0) - (anterior["kg_total"] or 0))
        if anterior["kg_total"] and anterior["kg_total"] > 0:
            var_pct = (var / anterior["kg_total"]) * 100
            if var_pct <= self.UMBRAL_CAIDA:
                alertas.append(AlertaRiesgo(
                    codigo   = "RIE003",
                    tipo     = "CRITICAL" if var_pct < -40 else "WARNING",
                    riesgo   = "Caída de volumen significativa",
                    detalle  = f"{anterior['mes']}/{anterior['anio']} → "
                               f"{actual['mes']}/{actual['anio']}: {var_pct:+.1f}%",
                    magnitud= var_pct,
                    prioridad = 2 if var_pct < -40 else 1,
                ))

        # RIE009 — Caída sostenida (3 meses seguidos)
        if len(evolucion) >= 3:
            meses = evolucion[-3:]
            vars_pct = []
            for i in range(1, len(meses)):
                ant = meses[i-1]["kg_total"] or 0
                act = meses[i]["kg_total"] or 0
                if ant > 0:
                    vars_pct.append((act - ant) / ant * 100)
            if all(v < 0 for v in vars_pct) and all(v < -5 for v in vars_pct):
                alertas.append(AlertaRiesgo(
                    codigo   = "RIE009",
                    tipo     = "CRITICAL",
                    riesgo   = "Caída sostenida (3 meses consecutivos)",
                    detalle  = f"Variaciones: {' / '.join(f'{v:+.1f}%' for v in vars_pct)}",
                    magnitud= sum(vars_pct),
                    prioridad = 2,
                ))
        return alertas

    def _clientes_inactivos(
        self, id_empresa: int
    ) -> list[AlertaRiesgo]:
        alertas = []
        from datetime import datetime, timedelta
        clis = self.repo.clientes_empresa(id_empresa)
        ahora = datetime.now()
        for c in clis:
            if not c.get("kg_total"):
                continue
            # Buscar última fecha de movimiento con este cliente
            movs = self.repo.clientes_perdidos(id_empresa, dias=self.DIAS_INACTIVO)
            for m in movs:
                if m["cliente"] == c["cliente"]:
                    dias = (ahora - datetime.now()).days
                    alertas.append(AlertaRiesgo(
                        codigo   = "RIE004",
                        tipo     = "WARNING",
                        riesgo   = f"Cliente inactivo: {c['cliente']}",
                        detalle  = f"Sin movimiento desde {m.get('ultima_fecha', 'N/A')}",
                        magnitud= 0,
                        prioridad = 1,
                    ))
        return alertas

    def _monoproducto(
        self, id_empresa: int, kg_total: float
    ) -> list[AlertaRiesgo]:
        alertas = []
        prods = self.repo.productos_empresa(id_empresa)
        if prods:
            pct = (prods[0]["kg_total"] or 0) / kg_total * 100
            if pct > self.UMBRAL_MONOPRODUCTO:
                alertas.append(AlertaRiesgo(
                    codigo   = "RIE006",
                    tipo     = "WARNING",
                    riesgo   = f"Monoproducto: {prods[0]['producto']}",
                    detalle  = f"{pct:.1f}% del volumen es un solo producto",
                    magnitud= pct,
                    prioridad = 1,
                ))
        return alertas

    def _migracion_competidores(
        self, id_empresa: int
    ) -> list[AlertaRiesgo]:
        alertas = []
        perdus = self.repo.productores_que_abandonaron(id_empresa, dias=90)
        for p in perdus:
            alertas.append(AlertaRiesgo(
                codigo   = "RIE007",
                tipo     = "WARNING",
                riesgo   = f"Productor migró a competidor: {p['nombre_productor']}",
                detalle  = f"Último movimiento: {p.get('ultima_fecha', 'N/A')} — "
                           f"{(p['kg_total'] or 0):,.0f} kg históricos",
                magnitud= 0,
                prioridad = 1,
            ))
        return alertas

    def _inactividad(self, id_empresa: int) -> list[AlertaRiesgo]:
        from datetime import datetime
        alertas = []
        inact = self.repo.empresas_sin_actividad_reciente(dias=self.DIAS_INACTIVO)
        for emp in inact:
            if emp.get("id_empresa") != id_empresa:
                continue
            alertas.append(AlertaRiesgo(
                codigo   = "RIE008",
                tipo     = "CRITICAL",
                riesgo   = "Sin actividad reciente",
                detalle  = f"Último movimiento: {emp.get('ultima_fecha', 'N/A')}",
                magnitud= 0,
                prioridad = 2,
            ))
        return alertas

    def formato(self, ar: AlertasRiesgo) -> str:
        """Formatea las alertas como informe de riesgos."""
        if not ar.alertas:
            return "\n  ✅  SIN RIESGOS DETECTADOS — todo en orden"

        lines = [
            "\n  🚨  ALERTAS DE RIESGO COMERCIAL",
            "  ──────────────────────────────────────────────────────────────",
            f"  {'─'*60}",
        ]

        tipo_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_alertas = sorted(ar.alertas, key=lambda a: tipo_order.get(a.tipo, 9))

        for a in sorted_alertas:
            emoji = a.emoji
            lines.append(
                f"  {emoji} [{a.codigo}] {a.riesgo}"
            )
            lines.append(f"         └─ {a.detalle}")

        lines.append(f"  {'─'*60}")
        lines.append(
            f"  Resumen: "
            f"🚨 {ar.count_criticos}  "
            f"⚠️  {ar.count_warning}  "
            f"ℹ️  {ar.count_info}"
        )
        return "\n".join(lines)

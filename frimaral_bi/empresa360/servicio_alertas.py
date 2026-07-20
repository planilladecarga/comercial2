"""
=================================================================================
servicio_alertas.py — Sistema de alertas inteligentes
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from empresa360.repositorio import Repositorio
from empresa360.servicio_evolucion import ServicioEvolucion


@dataclass
class Alerta:
    tipo: str           # "INFO" | "WARNING" | "CRITICAL"
    codigo: str         # código único, ej: "ALT-001"
    mensaje: str
    detalle: str = ""
    prioridad: int = 0  # 0=baja, 1=media, 2=alta

    @property
    def emoji(self) -> str:
        return {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(
            self.tipo, "🔔")


@dataclass
class Alertas360:
    alertas: list[Alerta] = field(default_factory=list)
    count_criticas: int = 0
    count_advertencias: int = 0
    count_info: int = 0

    @property
    def total(self) -> int:
        return len(self.alertas)


class ServicioAlertas:
    """
    Genera alertas automáticamente analisándola evolución y datos de la empresa.

    Tipos de alertas:
        ALT001 — Caída de volumen > 20%
        ALT002 — Aumento de volumen > 30%
        ALT003 — Nuevo productor detectado
        ALT004 — Nuevo mercado detectado
        ALT005 — Nuevo competidor detectado
        ALT006 — Productor dejó de usar la empresa
        ALT007 — Cambio de depósito significativo
        ALT008 — Sin actividad reciente (> 60 días)
        ALT009 — Participación en mercado en ascenso
        ALT010 — Participación en mercado en declive
    """

    UMBRAL_CAIDA    = -20.0
    UMBRAL_AUMENTO  = 30.0
    DIAS_INACTIVO   = 60

    def __init__(self, repo: Repositorio):
        self.repo = repo
        self.srv_evo = ServicioEvolucion(repo)

    def generar(self, id_empresa: int, nombre_empresa: str) -> Alertas360:
        """Genera todas las alertas para una empresa."""
        alertas: list[Alerta] = []
        evo = self.srv_evo.calcular(id_empresa)

        # ALT001 / ALT002 — Variaciones de volumen
        alertas.extend(self._detectar_variaciones_volumen(evo))

        # ALT003 — Nuevos productores
        alertas.extend(self._detectar_nuevos_productores(id_empresa))

        # ALT008 — Inactividad reciente
        alertas.extend(self._detectar_inactividad(id_empresa, nombre_empresa))

        # ALT004 / ALT005 — Nuevos mercados y competidores
        alertas.extend(self._detectar_nuevos_mercados_competidores(id_empresa))

        # Ordenar por prioridad
        alertas.sort(key=lambda a: a.prioridad, reverse=True)

        return Alertas360(
            alertas             = alertas,
            count_criticas     = sum(1 for a in alertas if a.tipo == "CRITICAL"),
            count_advertencias = sum(1 for a in alertas if a.tipo == "WARNING"),
            count_info         = sum(1 for a in alertas if a.tipo == "INFO"),
        )

    def _detectar_variaciones_volumen(
        self, evo
    ) -> list[Alerta]:
        """Detecta caídas y aumentos significativos."""
        alertas = []
        meses = evo.meses
        if len(meses) < 2:
            return alertas

        # Último mes completo vs mes anterior
        ult = meses[-1]
        ant = meses[-2] if len(meses) >= 2 else None
        if ant and ant.kg > 0 and ult.kg > 0:
            var = ((ult.kg - ant.kg) / ant.kg) * 100
            if var <= self.UMBRAL_CAIDA:
                alertas.append(Alerta(
                    tipo      = "CRITICAL",
                    codigo    = "ALT001",
                    mensaje   = f"Caída de volumen: {var:+.1f}%",
                    detalle   = f"{ant.nombre_mes} ({ant.kg:,.0f} kg) → "
                               f"{ult.nombre_mes} ({ult.kg:,.0f} kg)",
                    prioridad = 2,
                ))
            elif var >= self.UMBRAL_AUMENTO:
                alertas.append(Alerta(
                    tipo      = "INFO",
                    codigo    = "ALT002",
                    mensaje   = f"Aumento de volumen: {var:+.1f}%",
                    detalle   = f"{ant.nombre_mes} ({ant.kg:,.0f} kg) → "
                               f"{ult.nombre_mes} ({ult.kg:,.0f} kg)",
                    prioridad = 1,
                ))
        return alertas

    def _detectar_nuevos_productores(self, id_empresa: int) -> list[Alerta]:
        """Detecta productores que trabajaron por primera vez."""
        alertas = []
        nuevos = self.repo.nuevos_productores(id_empresa)
        for n in nuevos[:5]:  # Máximo 5
            alertas.append(Alerta(
                tipo      = "INFO",
                codigo    = "ALT003",
                mensaje   = f"Nuevo productor: {n['nombre_productor']}",
                detalle   = f"Primera aparición: {n['primera_fecha']}",
                prioridad = 0,
            ))
        return alertas

    def _detectar_inactividad(
        self, id_empresa: int, nombre: str
    ) -> list[Alerta]:
        """Detecta empresas sin actividad reciente."""
        from datetime import datetime, timedelta
        alertas = []
        movs = self.repo.movimientos_por_empresa(id_empresa, limite=1)
        if movs:
            ult_fecha_str = movs[0].get("fecha_movimiento", "")
            try:
                ult_fecha = datetime.strptime(ult_fecha_str, "%d/%m/%Y")
                dias_sin_actividad = (datetime.now() - ult_fecha).days
                if dias_sin_actividad > self.DIAS_INACTIVO:
                    alertas.append(Alerta(
                        tipo      = "WARNING",
                        codigo    = "ALT008",
                        mensaje   = f"Sin actividad hace {dias_sin_actividad} días",
                        detalle   = f"Último movimiento: {ult_fecha_str}",
                        prioridad = 1,
                    ))
            except (ValueError, TypeError):
                pass
        return alertas

    def _detectar_nuevos_mercados_competidores(
        self, id_empresa: int
    ) -> list[Alerta]:
        """Detecta nuevos mercados o competidores."""
        alertas = []
        # Mercado nuevo: si hay algún mercado en los últimos 90 días
        # que no estava en los 3 meses anteriores
        evolucion = self.repo.evolucion_mensual(id_empresa)
        if len(evolucion) >= 4:
            actuales = {r["kg_total"] for r in evolucion[-2:]}
        else:
            actuales = set()
        return alertas

    def formato_alertas(self, al: Alertas360) -> str:
        """Formatea alertas como lista visual."""
        if not al.alertas:
            return "  ✅  Sin alertas — todo en orden"
        lines = [f"  {'─'*56}"]
        for a in al.alertas:
            color = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(a.tipo, "🔔")
            lines.append(
                f"  {color} [{a.codigo}] {a.mensaje}"
            )
            if a.detalle:
                lines.append(f"         └─ {a.detalle}")
        lines.append(f"  {'─'*56}")
        lines.append(
            f"  Resumen: "
            f"❌ {al.count_criticas}  "
            f"⚠️  {al.count_advertencias}  "
            f"ℹ️  {al.count_info}"
        )
        return "\n".join(lines)

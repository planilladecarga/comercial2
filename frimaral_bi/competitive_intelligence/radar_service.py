"""
=================================================================================
radar_service.py — Radar de cambios comerciales
=================================================================================

Detecta automáticamente cambios en el ecosistema comercial:
    • Nuevos productores (ganados)
    • Productores perdidos (abandonados)
    • Mercados nuevos
    • Mercados perdidos
    • Clientes nuevos
    • Clientes perdidos
    • Caídas importantes (>20%)
    • Crecimientos importantes (>30%)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from competitive_intelligence.repositorio import RepositorioCIE


@dataclass
class ItemRadar:
    nombre       : str
    kg_actual   : float
    kg_anterior : float
    variacion_pct: float
    primera_fecha: Optional[str] = None
    ultima_fecha : Optional[str] = None


@dataclass
class RadarCambios:
    """
    Resultado del radar de cambios para una empresa.
    """
    productores_nuevos  : list[ItemRadar] = field(default_factory=list)
    productores_perdidos: list[ItemRadar] = field(default_factory=list)
    mercados_nuevos     : list[ItemRadar] = field(default_factory=list)
    mercados_perdidos   : list[ItemRadar] = field(default_factory=list)
    clientes_nuevos     : list[ItemRadar] = field(default_factory=list)
    clientes_perdidos   : list[ItemRadar] = field(default_factory=list)
    crecimiento_productores: list[ItemRadar] = field(default_factory=list)
    decrecimiento_productores: list[ItemRadar] = field(default_factory=list)

    @property
    def total_cambios(self) -> int:
        return (
            len(self.productores_nuevos)  +
            len(self.productores_perdidos) +
            len(self.mercados_nuevos)      +
            len(self.mercados_perdidos)    +
            len(self.clientes_nuevos)      +
            len(self.clientes_perdidos)
        )


class RadarService:
    """
    Detecta cambios comerciales automáticamente.

    Uso:
        radar = RadarService(repo)
        cambios = radar.detectar(id_empresa=5, dias=90)
    """

    UMBRAL_CAIDA      = -20.0
    UMBRAL_CRECIMIENTO = 30.0
    DEFAULT_DIAS      = 90

    def __init__(self, repo: RepositorioCIE):
        self.repo = repo

    def detectar(
        self,
        id_empresa: int,
        dias: int = DEFAULT_DIAS,
    ) -> RadarCambios:
        """
        Detecta todos los cambios en una empresa.

        Args:
            id_empresa : ID de la empresa a analizar
            dias       : Período de análisis en días (default 90)

        Returns:
            RadarCambios con todos los movimientos detectados
        """
        r = RadarCambios()

        # ── Productores ─────────────────────────────────────────────────────
        nuevos_prod = self.repo.productores_nuevos(id_empresa, dias=dias)
        for p in nuevos_prod:
            r.productores_nuevos.append(ItemRadar(
                nombre        = p["nombre_productor"],
                kg_actual    = p["kg_total"] or 0,
                kg_anterior  = 0,
                variacion_pct= 100.0,
                primera_fecha= p["primera_fecha"],
            ))

        perdus_prod = self.repo.productores_que_abandonaron(id_empresa, dias=dias)
        for p in perdus_prod:
            r.productores_perdidos.append(ItemRadar(
                nombre        = p["nombre_productor"],
                kg_actual    = 0,
                kg_anterior  = p["kg_total"] or 0,
                variacion_pct= -100.0,
                ultima_fecha = p["ultima_fecha"],
            ))

        # Crecimiento/decrecimiento de productores
        crecimiento = self.repo.crecimiento_productores(id_empresa)
        for c in crecimiento:
            var = c.get("crecimiento_pct", 0) or 0
            if var > 0:
                r.crecimiento_productores.append(ItemRadar(
                    nombre         = c.get("nro_productor", ""),
                    kg_actual     = c.get("kg_actual", 0) or 0,
                    kg_anterior   = c.get("kg_anterior", 0) or 0,
                    variacion_pct= var,
                ))
            else:
                r.decrecimiento_productores.append(ItemRadar(
                    nombre         = c.get("nro_productor", ""),
                    kg_actual     = c.get("kg_actual", 0) or 0,
                    kg_anterior   = c.get("kg_anterior", 0) or 0,
                    variacion_pct= var,
                ))

        # ── Mercados ───────────────────────────────────────────────────────
        nuevos_merc = self.repo.mercados_nuevos(id_empresa, dias=dias)
        for m in nuevos_merc:
            r.mercados_nuevos.append(ItemRadar(
                nombre        = m["mercado"],
                kg_actual    = m["kg_total"] or 0,
                kg_anterior  = 0,
                variacion_pct= 100.0,
                primera_fecha= m["primera_fecha"],
            ))

        perdus_merc = self.repo.mercados_perdidos(id_empresa, dias=dias)
        for m in perdus_merc:
            r.mercados_perdidos.append(ItemRadar(
                nombre        = m["mercado"],
                kg_actual    = 0,
                kg_anterior  = m["kg_total"] or 0,
                variacion_pct= -100.0,
                ultima_fecha = m["ultima_fecha"],
            ))

        # ── Clientes ───────────────────────────────────────────────────────
        nuevos_cli = self.repo.clientes_nuevos(id_empresa, dias=dias)
        for c in nuevos_cli:
            r.clientes_nuevos.append(ItemRadar(
                nombre        = c["cliente"],
                kg_actual    = c["kg_total"] or 0,
                kg_anterior  = 0,
                variacion_pct= 100.0,
                primera_fecha= c["primera_fecha"],
            ))

        perdus_cli = self.repo.clientes_perdidos(id_empresa, dias=dias)
        for c in perdus_cli:
            r.clientes_perdidos.append(ItemRadar(
                nombre        = c["cliente"],
                kg_actual    = 0,
                kg_anterior  = c["kg_total"] or 0,
                variacion_pct= -100.0,
                ultima_fecha = c["ultima_fecha"],
            ))

        return r

    def formato(self, r: RadarCambios) -> str:
        """Formatea el radar como informe visual."""
        lines = [
            "\n  📡  RADAR DE CAMBIOS COMERCIALES",
            "  ──────────────────────────────────────────────────────────",
        ]

        def _seccion(titulo: str, items: list[ItemRadar], icono: str):
            if not items:
                return
            lines.append(f"\n  {icono} {titulo} ({len(items)})")
            lines.append(
                "  ┌──────────────────────────────────────────────────────────────┐"
            )
            lines.append(
                "  │ NOMBRE                                     KG ACT.   KG ANT.  VAR% │"
            )
            lines.append(
                "  ├──────────────────────────────────────────────────────────────┤"
            )
            for item in items[:8]:
                var_str = f"{item.variacion_pct:+.1f}%"
                lines.append(
                    f"  │ {item.nombre[:44]:<44} │ "
                    f"{item.kg_actual:>8,.0f} │ {item.kg_anterior:>8,.0f} │ "
                    f"{var_str:>6} │"
                )
            lines.append(
                "  └──────────────────────────────────────────────────────────────┘"
            )

        _seccion("NUEVOS PRODUCTORES",   r.productores_nuevos,   "🟢")
        _seccion("PRODUCTORES PERDIDOS", r.productores_perdidos,  "🔴")
        _seccion("NUEVOS MERCADOS",     r.mercados_nuevos,       "🟢")
        _seccion("MERCADOS PERDIDOS",    r.mercados_perdidos,    "🔴")
        _seccion("NUEVOS CLIENTES",      r.clientes_nuevos,       "🟢")
        _seccion("CLIENTES PERDIDOS",    r.clientes_perdidos,     "🔴")
        _seccion("CRECIMIENTO >30%",    r.crecimiento_productores, "📈")
        _seccion("CAÍDA >20%",           r.decrecimiento_productores,"📉")

        if r.total_cambios == 0:
            lines.append("\n  ℹ️  Sin cambios significativos detectados")

        lines.append(
            f"\n  📊 Total cambios detectados: {r.total_cambios}"
        )
        return "\n".join(lines)

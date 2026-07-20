"""
=================================================================================
vista360.py — Motor unificado de Empresa360
=================================================================================

Orquesta todos los servicios para generar una ficha 360° completa
de cualquier empresa del ecosistema MGAP Uruguay.

Uso como librería:
    from empresa360 import Vista360

    motor = Vista360("data/frimaral_bi.db")
    ficha = motor.generar_ficha("CALIRAL")
    print(ficha)

Uso como CLI:
    python -m empresa360.vista360 "CALIRAL"
    python -m empresa360.vista360 "CALIRAL" --formato json
    python -m empresa360.vista360 "CALIRAL" --seccion indicadores
    python -m empresa360.vista360 --listar
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

from empresa360.repositorio          import Repositorio
from empresa360.servicio_info        import ServicioInfo, InfoGeneral
from empresa360.servicio_roles      import ServicioRoles, RolesEmpresa
from empresa360.servicio_indicadores import ServicioIndicadores, Indicadores360
from empresa360.servicio_relaciones import ServicioRelaciones, Relaciones360
from empresa360.servicio_evolucion   import ServicioEvolucion, Evolucion360
from empresa360.servicio_competidores import ServicioCompetidores, Competidores360
from empresa360.servicio_alertas     import ServicioAlertas, Alertas360


# ─────────────────────────────────────────────────────────────────────────────
# FICHA 360 — Dataclass que contiene toda la información
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Ficha360:
    """Representa la ficha completa de una empresa."""
    nombre_empresa : str
    encontrada     : bool = False
    info           : Optional[InfoGeneral] = None
    roles          : Optional[RolesEmpresa] = None
    indicadores    : Optional[Indicadores360] = None
    relaciones     : Optional[Relaciones360] = None
    evolucion      : Optional[Evolucion360] = None
    competidores   : Optional[Competidores360] = None
    alertas        : Optional[Alertas360] = None
    errores        : list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la ficha a dict (para JSON)."""
        d = {
            "nombre_empresa": self.nombre_empresa,
            "encontrada": self.encontrada,
            "errores": self.errores,
        }
        if self.info:
            d["info"] = {
                "nombre": self.info.nombre,
                "id_empresa": self.info.id_empresa,
                "tipo_principal": self.info.tipo_principal,
                "ruc": self.info.ruc,
                "fecha_primera": self.info.fecha_primera,
                "fecha_ultima": self.info.fecha_ultima,
                "cantidad_movimientos": self.info.cantidad_movimientos,
                "activo": self.info.activo,
            }
        if self.roles:
            d["roles"] = self.roles.todos_los_roles
        if self.indicadores:
            d["indicadores"] = asdict(self.indicadores)
        if self.relaciones:
            d["productores"] = [
                {"nro": p.nro_productor, "nombre": p.nombre,
                 "kg": p.kg, "pct": p.porcentaje, "movs": p.movimientos}
                for p in self.relaciones.productores
            ]
            d["depositos"] = [
                {"nombre": d.nombre, "kg": d.kg, "pct": d.porcentaje}
                for d in self.relaciones.depositos
            ]
        if self.evolucion:
            d["evolucion"] = self._srv_evo_dict()
        if self.competidores:
            d["competidores"] = [
                {"nombre": c.nombre, "similitud": c.indice_similitud,
                 "razon": c.razon_principal}
                for c in self.competidores.top_competidores[:10]
            ]
        if self.alertas:
            d["alertas"] = [
                {"codigo": a.codigo, "tipo": a.tipo,
                 "mensaje": a.mensaje, "detalle": a.detalle}
                for a in self.alertas.alertas
            ]
        return d

    def _srv_evo_dict(self) -> dict:
        if not self.evolucion:
            return {}
        return {
            "kg_maximo": self.evolucion.kg_maximo,
            "kg_promedio": self.evolucion.kg_promedio,
            "tendencia": self.evolucion.tendencia,
            "meses": [
                {"periodo": f"{m.nombre_mes} {m.anio}",
                 "kg": m.kg, "movimientos": m.movimientos,
                 "variacion_pct": m.variacion_pct}
                for m in self.evolucion.meses
            ]
        }


# ─────────────────────────────────────────────────────────────────────────────
# VISTA 360 — Motor principal
# ─────────────────────────────────────────────────────────────────────────────

class Vista360:
    """
    Motor unificado de inteligencia comercial.

    Uso:
        motor = Vista360("data/frimaral_bi.db")
        ficha = motor.generar_ficha("CALIRAL")
    """

    def __init__(self, db_path: str = "data/frimaral_bi.db"):
        self.repo         = Repositorio(db_path)
        self.srv_info     = ServicioInfo(self.repo)
        self.srv_roles    = ServicioRoles(self.repo)
        self.srv_ind      = ServicioIndicadores(self.repo)
        self.srv_rel      = ServicioRelaciones(self.repo)
        self.srv_evo      = ServicioEvolucion(self.repo)
        self.srv_comp     = ServicioCompetidores(self.repo)
        self.srv_alertas  = ServicioAlertas(self.repo)

    def generar_ficha(
        self,
        nombre_empresa: str,
        incluir_alertas: bool = True,
    ) -> Ficha360:
        """
        Genera la ficha 360° completa de una empresa.

        Args:
            nombre_empresa : Nombre o parte del nombre de la empresa.
            incluir_alertas: Si True, calcula alertas (más lento).

        Returns:
            Ficha360 con todos los módulos detectados.
        """
        ficha = Ficha360(nombre_empresa=nombre_empresa)

        # 1. Información general
        info = self.srv_info.obtener(nombre_empresa)
        if not info:
            ficha.errores.append(f"Empresa no encontrada: {nombre_empresa}")
            return ficha

        ficha.encontrada = True
        ficha.info = info
        id_empresa = info.id_empresa

        # 2. Roles
        ficha.roles = self.srv_roles.detectar(id_empresa)

        # 3. Indicadores
        ficha.indicadores = self.srv_ind.calcular(id_empresa)

        # 4. Relaciones
        ficha.relaciones = self.srv_rel.obtener(id_empresa)

        # 5. Evolución mensual
        ficha.evolucion = self.srv_evo.calcular(id_empresa)

        # 6. Competidores
        ficha.competidores = self.srv_comp.detectar(id_empresa)

        # 7. Alertas
        if incluir_alertas:
            ficha.alertas = self.srv_alertas.generar(id_empresa, info.nombre)

        return ficha

    def listar_empresas(self) -> list[dict[str, Any]]:
        """Lista todas las empresas disponibles."""
        return self.repo.listar_empresas()

    # ─── Formateadores ──────────────────────────────────────────────────────

    def formatear(self, ficha: Ficha360, seccion: str = "completa") -> str:
        """
        Formatea una ficha como texto legible.

        Args:
            ficha  : Ficha360 generada por generar_ficha()
            seccion: "completa" | "info" | "indicadores" | "relaciones"
                     | "evolucion" | "competidores" | "alertas"
        """
        if not ficha.encontrada:
            return f"❌ Empresa no encontrada: {ficha.nombre_empresa}"

        if seccion == "info":
            return self._formato_info(ficha)
        if seccion == "indicadores":
            return self._formato_indicadores(ficha)
        if seccion == "relaciones":
            return self._formato_relaciones(ficha)
        if seccion == "evolucion":
            return self._formato_evolucion(ficha)
        if seccion == "competidores":
            return self._formato_competidores(ficha)
        if seccion == "alertas":
            return self._formato_alertas(ficha)

        return self._formato_completa(ficha)

    def _formato_info(self, ficha: Ficha360) -> str:
        if not ficha.info:
            return "Sin información"
        return self.srv_info.formato_tarjeta(ficha.info)

    def _formato_indicadores(self, ficha: Ficha360) -> str:
        if not ficha.indicadores:
            return "Sin indicadores"
        return self.srv_ind.formato_tabla(ficha.indicadores)

    def _formato_relaciones(self, ficha: Ficha360) -> str:
        if not ficha.relaciones:
            return "Sin relaciones"
        lines = ["\n  PRODUCTORES RELACIONADOS", self.srv_rel.formato_productores(ficha.relaciones)]
        lines.append("\n  DEPÓSITOS UTILIZADOS")
        lines.append(self.srv_rel.formato_depositos(ficha.relaciones))
        return "\n".join(lines)

    def _formato_evolucion(self, ficha: Ficha360) -> str:
        if not ficha.evolucion:
            return "Sin evolución"
        return self.srv_evo.formato_tabla(ficha.evolucion)

    def _formato_competidores(self, ficha: Ficha360) -> str:
        if not ficha.competidores:
            return "Sin competidores"
        return self.srv_comp.formato_tabla(ficha.competidores)

    def _formato_alertas(self, ficha: Ficha360) -> str:
        if not ficha.alertas:
            return "✅ Sin alertas"
        return self.srv_alertas.formato_alertas(ficha.alertas)

    def _formato_completa(self, ficha: Ficha360) -> str:
        """Genera la ficha completa formateada."""
        nombre = ficha.nombre_empresa
        lines = [
            "\n",
            "═" * 64,
            f"  🏢  EMPRESA 360°  —  {ficha.info.nombre if ficha.info else nombre}",
            "═" * 64,
            "",
        ]

        # Info
        if ficha.info:
            lines.append(self.srv_info.formato_tarjeta(ficha.info))
            lines.append("")

        # Roles
        if ficha.roles:
            lines.append("  ROLES DETECTADOS")
            lines.append(f"  {self.srv_roles.formato_roles(ficha.roles)}")
            lines.append("")

        # Indicadores
        if ficha.indicadores:
            lines.append("  INDICADORES CLAVE")
            lines.append(self.srv_ind.formato_tabla(ficha.indicadores))
            lines.append("")

        # Relaciones
        if ficha.relaciones:
            lines.append("  PRODUCTORES RELACIONADOS (Top 10)")
            lines.append(self.srv_rel.formato_productores(ficha.relaciones, top=10))
            lines.append("")
            lines.append("  DEPÓSITOS UTILIZADOS")
            lines.append(self.srv_rel.formato_depositos(ficha.relaciones))
            lines.append("")

        # Evolución
        if ficha.evolucion:
            lines.append("  EVOLUCIÓN MENSUAL")
            lines.append(self.srv_evo.formato_tabla(ficha.evolucion))
            lines.append("")

        # Competidores
        if ficha.competidores:
            lines.append("  COMPETIDORES DETECTADOS")
            lines.append(self.srv_comp.formato_tabla(ficha.competidores, top=8))
            lines.append("")

        # Alertas
        if ficha.alertas:
            lines.append("  SISTEMA DE ALERTAS")
            lines.append(self.srv_alertas.formato_alertas(ficha.alertas))
            lines.append("")

        lines.append("═" * 64)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI — Interface de línea de comandos
# ─────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Empresa360 — Motor de Inteligencia Comercial FRIMARAL BI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "empresa", nargs="?", default=None,
        help="Nombre de la empresa a analizar"
    )
    parser.add_argument(
        "--db", default="data/frimaral_bi.db",
        help="Ruta a la base SQLite (default: data/frimaral_bi.db)"
    )
    parser.add_argument(
        "--seccion", default="completa",
        choices=["completa", "info", "indicadores", "relaciones",
                 "evolucion", "competidores", "alertas"],
        help="Sección a mostrar"
    )
    parser.add_argument(
        "--formato", default="texto",
        choices=["texto", "json"],
        help="Formato de salida"
    )
    parser.add_argument(
        "--listar", action="store_true",
        help="Lista todas las empresas disponibles"
    )
    parser.add_argument(
        "--sin-alertas", action="store_true",
        help="Omite el cálculo de alertas (más rápido)"
    )

    args = parser.parse_args()

    # Resolver db_path relativo a este script
    db_path = Path(__file__).parent.parent / args.db
    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}", file=sys.stderr)
        sys.exit(1)

    motor = Vista360(str(db_path))

    # Listar empresas
    if args.listar:
        empresas = motor.listar_empresas()
        print(f"\n  🏢  EMPRESAS DISPONIBLES ({len(empresas)} total)\n")
        print("  ┌────┬──────────────────────────────────────────┬────────┬────────────┐")
        print("  │ #  │ NOMBRE                                    │ TIPO   │ MOVIMS.   │")
        print("  ├────┼──────────────────────────────────────────┼────────┼────────────┤")
        for i, emp in enumerate(empresas, 1):
            nom = emp.get("nombre_unif", "")[:40]
            tip = emp.get("tipo_principal", "—")[:8]
            mov = emp.get("cant_movimientos", 0)
            print(f"  │ {i:>3} │ {nom:<42} │ {tip:<8} │ {mov:>10,} │")
        print("  └────┴──────────────────────────────────────────┴────────┴────────────┘")
        return

    # Mostrar empresa
    if not args.empresa:
        print("❌ Especifica una empresa o usa --listar", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    ficha = motor.generar_ficha(
        args.empresa,
        incluir_alertas=not args.sin_alertas,
    )

    if args.formato == "json":
        print(json.dumps(ficha.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(motor.formatear(ficha, seccion=args.seccion))


if __name__ == "__main__":
    _cli()

"""
=============================================================================
seed_data.py — Genera datos de demostración realistas para FRIMARAL BI
=============================================================================
Puebla la base SQLite con datos creíbles para testing del Sprint 3.

Autor  : FRIMARAL BI Team
Versión: 1.0.0
=============================================================================
"""

import sqlite3
import random
import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "frimaral_bi.db")
DB_PATH = os.path.abspath(DB_PATH)

def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Limpiar tablas ──────────────────────────────────────────────────────
    for table in ["movimientos", "dim_cortes", "dim_empresas",
                  "dim_paises", "dim_productos", "dim_calendario"]:
        cur.execute(f"DELETE FROM {table}")
    conn.commit()
    print("✅ Tablas limpiadas")

    # ── DIM_PRODUCTOS ─────────────────────────────────────────────────────
    # Schema: id_producto (AI), nombre_producto, categoria, unidad_medida
    productos = [
        ("CB-001", "Carne Bovina Fresca",       "Bovino",   "Kg"),
        ("CB-002", "Carne Bovina Congelada",    "Bovino",   "Kg"),
        ("CO-001", "Carne Ovina Fresca",        "Ovino",    "Kg"),
        ("CO-002", "Carne Ovina Congelada",     "Ovino",    "Kg"),
        ("PB-001", "Achuras Bovinas",           "Bovino",   "Kg"),
        ("CU-001", "Cueros Bovinos",            "Subprod.", "Kg"),
        ("SB-001", "Sebo Bovino",               "Subprod.", "Kg"),
        ("MC-001", "Menudencias Ovinas",        "Ovino",    "Kg"),
    ]
    cur.executemany(
        "INSERT INTO dim_productos (nombre_producto,categoria,unidad_medida) VALUES(?,?,?)",
        [(p[1],p[2],p[3]) for p in productos])
    print(f"✅ dim_productos: {len(productos)} registros")

    # ── DIM_PAISES ─────────────────────────────────────────────────────────
    # Schema: id_pais(AI), nombre_pais, solo_deposito, region, continente
    paises = [
        ("Uruguay",                         0, "Cono Sur",        "América"),
        ("Brasil",                          0, "Cono Sur",        "América"),
        ("Argentina",                       0, "Cono Sur",        "América"),
        ("Chile",                           0, "Pacifico Sur",    "América"),
        ("China",                           0, "Asia-Pacífico",   "Asia"),
        ("Rusia",                           0, "Europa-Este",     "Europa"),
        ("Unión Europea",                   0, "Europa",          "Europa"),
        ("Estados Unidos",                   0, "Norte",          "América"),
        ("Israel (Solo a Depósitos)",       1, "Mediterráneo",   "Asia"),
        ("Arabia Saudita (Solo a Depósitos)",1,"Medio Oriente",  "Asia"),
        ("Hong Kong",                        0, "Asia-Pacífico",   "Asia"),
        ("Marruecos (Solo a Depósitos)",    1, "Norte África",   "África"),
    ]
    cur.executemany(
        "INSERT INTO dim_paises (nombre_pais,solo_deposito,region,continente) VALUES(?,?,?,?)",
        paises)
    print(f"✅ dim_paises: {len(paises)} registros")

    # ── DIM_EMPRESAS ───────────────────────────────────────────────────────
    # Schema: id_empresa(AI), nombre_original, nombre_norm, nombre_unif,
    #         ruc, tipo_principal, es_productor, es_certificador,
    #         es_deposito, es_puerto, es_competidor, activo,
    #         fecha_primera, fecha_ultima, cant_movimientos
    empresas = [
        ("CALIRAL S.A.",
         "CALIRAL S.A.", "CALIRAL S.A.",
         "020123450011", "Matadero", 1, 0, 1, 1, 0, 1, 1,
         "2015-01-01", "2025-12-31", 0),
        ("FRIGORÍFICO SAN JACINTO S.A.",
         "FRIGORIFICO SAN JACINTO S.A.", "FRIGORIFICO SAN JACINTO S.A.",
         "020123450012", "Matadero", 1, 0, 1, 1, 0, 1, 1,
         "2010-01-01", "2025-12-31", 0),
        ("DEPÓSITO CALIRAL",
         "DEPOSITO CALIRAL", "DEPOSITO CALIRAL",
         "020123450013", "Depósito", 0, 0, 1, 0, 0, 1, 1,
         "2015-01-01", "2025-12-31", 0),
        ("DEPÓSITO SAN JACINTO",
         "DEPOSITO SAN JACINTO", "DEPOSITO SAN JACINTO",
         "020123450014", "Depósito", 0, 0, 1, 0, 0, 1, 1,
         "2018-01-01", "2025-12-31", 0),
        ("FRIGORÍFICO ARBIGA HNOS.",
         "FRIGORIFICO ARBIGA HNOS.", "FRIGORIFICO ARBIGA HNOS.",
         "020123450015", "Matadero", 1, 0, 1, 1, 1, 1, 1,
         "2005-01-01", "2025-12-31", 0),
        ("CUTCSA ALIMENTOS S.A.",
         "CUTCSA ALIMENTOS S.A.", "CUTCSA ALIMENTOS S.A.",
         "020234560017", "Distribuidor", 0, 0, 0, 0, 1, 1, 1,
         "2015-03-01", "2025-12-31", 0),
        ("RUFFONI S.A.",
         "RUFFONI S.A.", "RUFFONI S.A.",
         "020345670018", "Minorista", 0, 0, 0, 0, 1, 1, 1,
         "2018-07-01", "2025-12-31", 0),
        ("INAC - Instituto Nacional de Carnes",
         "INAC", "INAC",
         "020000000001", "Certificadora", 0, 1, 0, 0, 0, 1, 1,
         "2000-01-01", "2025-12-31", 0),
        ("SGS URUGUAY",
         "SGS URUGUAY", "SGS URUGUAY",
         "020000000002", "Certificadora", 0, 1, 0, 0, 0, 1, 1,
         "2020-01-01", "2025-12-31", 0),
        ("PUERTO DE MONTEVIDEO",
         "Puerto Montevideo", "Puerto Montevideo",
         "020000000010", "Puerto", 0, 0, 0, 1, 0, 1, 1,
         "2000-01-01", "2025-12-31", 0),
    ]
    cur.executemany("""
        INSERT INTO dim_empresas
        (id_empresa,nombre_original,nombre_norm,nombre_unif,ruc,tipo_principal,
         es_productor,es_certificador,es_deposito,es_puerto,
         es_competidor,activo,fecha_primera,fecha_ultima,cant_movimientos)
        VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", empresas)
    print(f"✅ dim_empresas: {len(empresas)} registros")

    # ── DIM_CORTES ────────────────────────────────────────────────────────
    # Schema: id_corte(AI), codigo_corte, nombre_corte, producto_id,
    #         categoria_corte, grado, kilos_promedio, activo
    cortes = [
        ("COR-001","Bife Ancho",         1,"Premium",  "A", 3.5),
        ("COR-002","Bife Angosto",        1,"Premium",  "A", 2.0),
        ("COR-003","Tira de Asado",       1,"Standard", "B", 1.5),
        ("COR-004","Vacío",              1,"Standard", "B", 2.5),
        ("COR-005","Entraña",            1,"Premium",  "A", 0.8),
        ("COR-006","Osobuco",            1,"Standard", "C", 1.2),
        ("COR-007","Nalga",              1,"Standard", "B", 2.8),
        ("COR-008","Cuadrada",           1,"Standard", "B", 2.3),
        ("COR-009","Falda",              1,"Económica","C", 1.8),
        ("COR-010","Achuras",            5,"Standard", "C", 2.0),
        ("COR-011","Carne Ovina Cortes",  2,"Premium",  "A", 1.5),
        ("COR-012","Pernil Ovino",        2,"Standard", "B", 2.0),
    ]
    cur.executemany("""
        INSERT INTO dim_cortes
        (codigo_corte,nombre_corte,producto_id,categoria_corte,grado,kilos_promedio,activo)
        VALUES(?,?,?,?,?,?,1)""", cortes)
    print(f"✅ dim_cortes: {len(cortes)} registros")

    # ── DIM_CALENDARIO ────────────────────────────────────────────────────
    # Schema: id_fecha(AI), fecha, anio, mes, nombre_mes, trimestre,
    #         semestre, semana_iso, dia_mes, dia_semana, dia_nombre,
    #         es_laboral, festivo_uy
    start = date(2025, 1, 1)
    end   = date(2025, 12, 31)
    delta = end - start

    holidays = {
        (1,1):"Año Nuevo", (1,6):"Día de los Reyes",
        (4,19):"Desembarco 33 Orientales", (5,1):"Día del Trabajo",
        (5,18):"Batalla de Las Piedras", (6,19):"Natalicio de Artigas",
        (7,18):"Jura de la Constitución", (8,25):"Declaración Independencia",
        (11,2):"Día de los Difuntos", (12,25):"Navidad",
    }
    days_map = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    cal_rows = []
    for i in range(delta.days + 1):
        d = start + timedelta(days=i)
        mes  = d.month
        trim = (mes - 1) // 3 + 1
        sem  = (mes - 1) // 6 + 1
        dow  = d.weekday()
        fest = holidays.get((mes, d.day), None)
        cal_rows.append((
            d.strftime("%Y-%m-%d"), d.year, mes,
            d.strftime("%B"), trim, sem,
            d.isocalendar()[1], d.day,
            dow + 1, days_map[dow],
            1 if dow < 5 else 0,
            fest
        ))

    cur.executemany("""
        INSERT INTO dim_calendario
        (fecha,anio,mes,nombre_mes,trimestre,semestre,semana_iso,
         dia_mes,dia_semana,dia_nombre,es_laboral,festivo_uy)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", cal_rows)
    print(f"✅ dim_calendario: {len(cal_rows)} registros (2025)")

    # ── MOVIMIENTOS ───────────────────────────────────────────────────────
    # Schema: id_movimiento(AI), _id_temp, nro_establecimiento,
    #         nombre_establecimiento, departamento, localidad,
    #         tipo_establecimiento, nro_productor, nombre_productor,
    #         ruc, empresa_id, destino, tipo_movimiento,
    #         categoria_movimiento, fecha_movimiento, fecha_id,
    #         nro_gre, nro_certificado, producto_id, kilos_netos,
    #         temperatura, solo_deposito, observaciones, empresa_unificada
    tipo_mov  = ["Faena","Certificación","Despacho","Transferencia"]
    cat_mov   = ["Nacional","Exportación","Depósito"]
    deptos    = ["Montevideo","Canelones","Soriano","Cerro Largo","Durazno",
                 "Flores","Florida","Lavalleja","Paysandú","Río Negro",
                 "Rivera","Rocha","Salto","San José","Tacuarembó","Treinta y Tres"]
    localds   = ["Montevideo","Las Piedras","San José de Mayo","Paysandú",
                  "Salto","Rivera","Cerro Largo","Durazno","Florida","Rocha"]
    productors = [
        ("P-0001","Juan Carlos Martínez"),
        ("P-0002","María Elena González"),
        ("P-0003","Pedro Luis Rodríguez"),
        ("P-0004","Ana Beatriz Fernández"),
        ("P-0005","Carlos Alberto López"),
        ("P-0006","Laura Patricia Silva"),
        ("P-0007","José Manuel Torres"),
        ("P-0008","Marta Isabel Velázquez"),
        ("P-0009","Roberto Carlos Mehta"),
        ("P-0010","Claudia Beatriz Romero"),
        ("P-0011","Francisco Alejandro Acosta"),
        ("P-0012","Diana Patricia González"),
        ("P-0013","Miguel Ángel Rodríguez"),
        ("P-0014","Sandra Mabel Pereira"),
        ("P-0015","Hugo Fernando Núñez"),
    ]

    export_destinos = [
        "Brasil","Argentina","Chile","China","Rusia",
        "Unión Europea","Estados Unidos","Hong Kong"
    ]
    solo_dep_destinos = [
        "Israel (Solo a Depósitos)",
        "Arabia Saudita (Solo a Depósitos)",
        "Marruecos (Solo a Depósitos)",
    ]

    random.seed(42)
    movs = []
    mov_id = 1

    for day_offset in range(180):
        d = start + timedelta(days=day_offset)
        if d.weekday() >= 5:
            continue

        fecha_str = d.strftime("%Y-%m-%d")

        for _ in range(random.randint(4, 15)):
            prod_id    = random.randint(1, 5)
            empresa_id = random.choice([1, 2, 3, 4, 5])
            tipo       = random.choice(tipo_mov)
            cat        = random.choice(cat_mov)
            p_idx      = random.randint(0, len(productors)-1)
            p_num, p_nom = productors[p_idx]
            depto      = random.choice(deptos)
            locald     = random.choice(localds)
            kilos      = round(random.uniform(50, 2500), 2)
            gre        = f"GRE-2025-{mov_id:06d}"
            cert       = f"CERT-2025-{random.randint(1000,9999)}"
            temp       = round(random.uniform(-5, 5), 1)
            estab_num  = f"{random.randint(1,999):04d}"
            estab_nom  = f"Estab. {estab_num}"
            ruc        = f"02{random.randint(10000000,99999999)}"

            # Determinar destino
            if cat == "Exportación":
                if random.random() < 0.2:
                    destino   = random.choice(solo_dep_destinos)
                    solo_dep  = 1
                else:
                    destino   = random.choice(export_destinos)
                    solo_dep  = 0
            else:
                destino   = "Uruguay"
                solo_dep  = 0

            fecha_id   = day_offset + 1

            movs.append((
                estab_num, estab_nom, depto, locald,
                random.choice(["Productor","Certificador","Ambos"]),
                p_num, p_nom, ruc,
                empresa_id, destino, tipo, cat,
                fecha_str, fecha_id,
                gre, cert, prod_id,
                kilos, temp, solo_dep,
                f"Obs-{mov_id}", f"Empresa {empresa_id}"
            ))
            mov_id += 1

    cur.executemany("""
        INSERT INTO movimientos
        (id_movimiento,_id_temp,nro_establecimiento,nombre_establecimiento,
         departamento,localidad,tipo_establecimiento,nro_productor,nombre_productor,
         ruc,empresa_id,destino,tipo_movimiento,categoria_movimiento,
         fecha_movimiento,fecha_id,nro_gre,nro_certificado,producto_id,
         kilos_netos,temperatura,solo_deposito,observaciones,empresa_unificada)
        VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", movs)

    # Actualizar cant_movimientos en dim_empresas
    cur.execute("""
        UPDATE dim_empresas
        SET cant_movimientos = (
            SELECT COUNT(*) FROM movimientos WHERE empresa_id = dim_empresas.id_empresa
        )
    """)
    print(f"✅ movimientos: {len(movs)} registros")

    conn.commit()

    # Verificar
    print("\n📊 Resumen final:")
    for t in ["movimientos","dim_empresas","dim_paises",
              "dim_productos","dim_calendario","dim_cortes"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"   {t}: {cur.fetchone()[0]:,} filas")

    conn.close()
    print("\n🎲 Datos de demostración generados correctamente.")


if __name__ == "__main__":
    seed()

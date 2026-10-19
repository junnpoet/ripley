#!/usr/bin/env python3
"""
Script para consultar y mostrar un resumen rápido de entidades y conteo de registros
en la base de datos MySQL (OLTP o DW), sin necesidad de generar archivos Excel.
"""

import os
import sys
import argparse
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "ripley_user")
DB_PASS = os.getenv("MYSQL_PASSWORD", "ripley_pass")


# Clasificación semántica de entidades para presentación estructurada
OLTP_SECTIONS = [
    (
        "OPERACIONAL & TRANSACCIONAL (JULIO 2026)",
        [
            "DETALLE_COMPROBANTE",
            "COMPROBANTE_PAGO",
            "PAGO_COMPROBANTE",
            "LOG_AFLUENCIA_IOT",
            "ASIGNACION_CAJA",
        ],
    ),
    (
        "CATÁLOGO COMERCIAL & EXISTENCIAS",
        [
            "PRODUCTO",
            "INVENTARIO_TIENDA",
            "PROVEEDOR",
            "MARCA",
            "SUBCATEGORIA",
            "CATEGORIA",
            "LINEA_COMERCIAL",
        ],
    ),
    (
        "CLIENTES & SOPORTE SUNAT",
        [
            "CLIENTE",
            "TIPO_CLIENTE",
            "TIPO_DOCUMENTO",
            "METODO_PAGO",
        ],
    ),
    (
        "INFRAESTRUCTURA & PERSONAL",
        [
            "TIENDA",
            "CAJA_POS",
            "ZONA_TIENDA",
            "DISPOSITIVO_SENSOR",
            "EMPLEADO",
            "ROL_EMPLEADO",
            "TURNO_TRABAJO",
            "UBIGEO",
        ],
    ),
]


def get_db_summary(db_name):
    """Consulta la lista de tablas y su cantidad exacta de registros."""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=db_name,
            charset="utf8mb4",
            autocommit=True,
        )
    except Exception as e:
        print(f"\n❌ Error al conectar a la base de datos '{db_name}': {e}")
        print("💡 Verifica que el contenedor esté corriendo con: make db-up")
        return None

    counts = {}
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES;")
        tables = [r[0] for r in cur.fetchall()]

        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{table}`;")
            counts[table] = cur.fetchone()[0]

    conn.close()
    return counts


def display_oltp_summary(counts, db_name="ripley_oltp"):
    """Formatea e imprime el resumen de la base transaccional OLTP."""
    print("=" * 68)
    print(f"📊 RESUMEN DE LA BASE DE DATOS: {db_name}")
    print(f"🔗 Conexión: {DB_USER}@{DB_HOST}:{DB_PORT}/{db_name}")
    print("=" * 68)

    displayed_tables = set()
    total_records = sum(counts.values())

    for section_title, table_list in OLTP_SECTIONS:
        section_tables = [t for t in table_list if t in counts]
        if not section_tables:
            continue

        print(f"\n  [{section_title}]")
        for table in section_tables:
            filas = counts[table]
            displayed_tables.add(table)
            print(f"  ✓ [{filas:>7,d} filas]  {table}")

    # Otras tablas que no estén en la categorización previa
    remaining = [t for t in sorted(counts.keys()) if t not in displayed_tables]
    if remaining:
        print("\n  [OTRAS ENTIDADES]")
        for table in remaining:
            print(f"  ✓ [{counts[table]:>7,d} filas]  {table}")

    print("\n" + "=" * 68)
    print("📈 TOTALES GENERALES:")
    print(f"  • Entidades / Tablas analizadas: {len(counts)}")
    print(f"  • Registros totales en la base:  {total_records:,}")
    print("=" * 68)


def display_dw_summary(counts, db_name="ripley_dw"):
    """Formatea e imprime el resumen dimensional de Data Warehouse."""
    print("=" * 68)
    print(f"📊 RESUMEN DE DATA WAREHOUSE: {db_name}")
    print(f"🔗 Conexión: {DB_USER}@{DB_HOST}:{DB_PORT}/{db_name}")
    print("=" * 68)

    facts = [t for t in sorted(counts.keys()) if t.startswith("FACT_")]
    dims = [t for t in sorted(counts.keys()) if t.startswith("DIM_")]
    others = [t for t in sorted(counts.keys()) if not t.startswith("FACT_") and not t.startswith("DIM_")]

    if facts:
        print("\n  [TABLAS DE HECHOS (FACT TABLES)]")
        for t in facts:
            print(f"  ✓ [FACT | {counts[t]:>7,d} filas]  {t}")

    if dims:
        print("\n  [DIMENSIONES CONFORMADAS (KIMBALL)]")
        for t in dims:
            print(f"  ✓ [DIM  | {counts[t]:>7,d} filas]  {t}")

    if others:
        print("\n  [OTRAS TABLAS]")
        for t in others:
            print(f"  ✓ [{counts[t]:>7,d} filas]  {t}")

    total_records = sum(counts.values())
    print("\n" + "=" * 68)
    print("📈 TOTALES GENERALES DW:")
    print(f"  • Tablas dimensionales/hechos: {len(counts)}")
    print(f"  • Registros totales en DW:     {total_records:,}")
    print("=" * 68)


def main():
    parser = argparse.ArgumentParser(description="Muestra resumen de tablas y conteo de registros en MySQL.")
    parser.add_argument("--dw", action="store_true", help="Consultar base de datos Data Warehouse (ripley_dw)")
    parser.add_argument("--all", action="store_true", help="Consultar ambas bases de datos (OLTP y DW)")
    parser.add_argument("database", nargs="?", default=None, help="Nombre opcional de base de datos específica")

    args = parser.parse_args()

    if args.all:
        oltp_counts = get_db_summary("ripley_oltp")
        if oltp_counts:
            display_oltp_summary(oltp_counts, "ripley_oltp")
        print("\n")
        dw_counts = get_db_summary("ripley_dw")
        if dw_counts:
            display_dw_summary(dw_counts, "ripley_dw")
    elif args.dw or args.database == "ripley_dw":
        counts = get_db_summary("ripley_dw")
        if counts:
            display_dw_summary(counts, "ripley_dw")
    else:
        target_db = args.database if args.database else "ripley_oltp"
        counts = get_db_summary(target_db)
        if counts:
            if "dw" in target_db.lower():
                display_dw_summary(counts, target_db)
            else:
                display_oltp_summary(counts, target_db)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para reiniciar y limpiar la base de datos Ripley OLTP desde cero.
Recrea todas las tablas vacías en 3NF a partir de database/oltp/01_schema.sql.
"""

import os
import sys
from pathlib import Path
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "ripley_user")
DB_PASS = os.getenv("MYSQL_PASSWORD", "ripley_pass")
DB_NAME = os.getenv("MYSQL_DATABASE", "ripley_oltp")
SCHEMA_FILE = Path("database/oltp/01_schema.sql")


def main():
    print("=" * 65)
    print("🧹 REINICIANDO BASE DE DATOS RIPLEY OLTP (RESET DESDE CERO)")
    print(f"🔗 Conectando a {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}...")
    print("=" * 65)

    if not SCHEMA_FILE.exists():
        print(f"❌ Error: No se encontró el archivo de esquema en {SCHEMA_FILE}")
        sys.exit(1)

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            charset="utf8mb4",
            autocommit=False,
        )
    except Exception as e:
        print(f"❌ Error de conexión a MySQL: {e}")
        print("💡 Verifica que el contenedor esté corriendo con: make db-up")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            cur.execute("SET NAMES utf8mb4;")
            cur.execute("SET CHARACTER SET utf8mb4;")
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

            # Dividir sentencias SQL por punto y coma ignorando comentarios de bloque
            statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

            for stmt in statements:
                # Omitir comandos de creación de base de datos si ya estamos conectados
                if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                    continue
                cur.execute(stmt)

            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()

        # Verificar tablas resultantes
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tables = [r[0] for r in cur.fetchall()]

        print("\n" + "=" * 65)
        print("✅ BASE DE DATOS REINICIADA EXITOSAMENTE")
        print(f"📋 Se recrearon las {len(tables)} tablas vacías según el esquema 3NF:")
        for t in tables:
            print(f"   • {t}")
        print("=" * 65)
        print("💡 Ahora puedes ejecutar 'make seed-data' para repoblar la base de datos.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante el reinicio de tablas: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

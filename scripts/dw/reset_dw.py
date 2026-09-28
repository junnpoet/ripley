#!/usr/bin/env python3
"""
Script para reiniciar y limpiar la base de datos Ripley Data Warehouse (ripley_dw) desde cero.
Recrea todas las tablas dimensionales y de hechos a partir de database/dw/01_schema.sql
e inserta los registros comodín (-1) según el estándar Ralph Kimball.
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
DB_ROOT_PASS = os.getenv("MYSQL_ROOT_PASSWORD", "rootpassword")
DB_NAME = "ripley_dw"

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT_DIR / "database" / "dw" / "01_schema.sql"


def ensure_database_and_grants():
    """Asegura que ripley_dw exista y ripley_user tenga permisos completos."""
    try:
        # Primero intentamos conectar directamente como ripley_user a ripley_dw
        test_conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            charset="utf8mb4",
        )
        test_conn.close()
        return
    except Exception:
        pass

    # Si falla, usamos root para crear la BD y otorgar privilegios
    try:
        root_conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user="root",
            password=DB_ROOT_PASS,
            charset="utf8mb4",
            autocommit=True,
        )
        with root_conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            cur.execute(f"GRANT ALL PRIVILEGES ON `{DB_NAME}`.* TO '{DB_USER}'@'%';")
            cur.execute("FLUSH PRIVILEGES;")
        root_conn.close()
    except Exception as e:
        print(f"⚠️ Nota de verificación de permisos administrativos: {e}")


def main():
    print("=" * 65)
    print("🧹 REINICIANDO DATA WAREHOUSE RIPLEY (RESET DESDE CERO)")
    print(f"🔗 Conectando a {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}...")
    print("=" * 65)

    if not SCHEMA_FILE.exists():
        print(f"❌ Error: No se encontró el archivo de esquema en {SCHEMA_FILE}")
        sys.exit(1)

    ensure_database_and_grants()

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
        print(f"❌ Error de conexión a MySQL ({DB_NAME}): {e}")
        print("💡 Verifica que el contenedor esté corriendo con: make db-up")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            cur.execute("SET NAMES utf8mb4;")
            cur.execute("SET CHARACTER SET utf8mb4;")
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

            # Dividir sentencias SQL por punto y coma ignorando comentarios de bloque
            statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

            executed_count = 0
            for stmt in statements:
                # Omitir sentencias de creación o cambio de base de datos ya que estamos conectados a ella
                clean_stmt = stmt.strip()
                if clean_stmt.upper().startswith("CREATE DATABASE") or clean_stmt.upper().startswith("USE "):
                    continue
                cur.execute(stmt)
                executed_count += 1

            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conn.commit()

        print(f"✅ Esquema del Data Warehouse ejecutado exitosamente ({executed_count} sentencias).")

        # Verificar tablas creadas
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tables = [row[0] for row in cur.fetchall()]

            print(f"\n📊 Tablas activas en '{DB_NAME}' ({len(tables)} tablas):")
            for table in sorted(tables):
                cur.execute(f"SELECT COUNT(*) FROM `{table}`;")
                count = cur.fetchone()[0]
                table_type = "DIMENSIÓN" if table.startswith("DIM_") else "HECHO"
                print(f"   - [{table_type:9s}] {table:25s}: {count:5d} filas")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante la ejecución del DDL del Data Warehouse: {e}")
        sys.exit(1)
    finally:
        conn.close()

    print("\n✨ Data Warehouse reseteado y listo con comodines Kimball (-1).")


if __name__ == "__main__":
    main()

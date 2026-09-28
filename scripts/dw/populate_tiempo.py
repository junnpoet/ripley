#!/usr/bin/env python3
"""
Poblador determinista de dimensiones temporales para Ripley Data Warehouse (ripley_dw).
Genera e inserta:
  - DIM_FECHA: Calendario 2025-2027 (1,096 días), feriados peruanos oficiales y temporadas comerciales Ripley.
  - DIM_HORA: 1,440 minutos del día, franjas horarias, turnos operacionales y clasificación de Horas Pico/Valle.
Exporta también el script SQL estático en database/dw/02_seed_tiempo.sql.
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "ripley_user")
DB_PASS = os.getenv("MYSQL_PASSWORD", "ripley_pass")
DB_NAME = "ripley_dw"

ROOT_DIR = Path(__file__).resolve().parents[2]
SQL_OUTPUT_FILE = ROOT_DIR / "database" / "dw" / "02_seed_tiempo.sql"

START_DATE = date(2025, 1, 1)
END_DATE = date(2027, 12, 31)

SPANISH_MONTHS = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

SPANISH_DAYS = [
    "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
]

# Feriados fijos en Perú (mes, día)
FIXED_PERU_HOLIDAYS = {
    (1, 1): "Año Nuevo",
    (5, 1): "Día del Trabajo",
    (6, 7): "Batalla de Arica y Día de la Bandera",
    (6, 29): "San Pedro y San Pablo",
    (7, 23): "Día de la Fuerza Aérea",
    (7, 28): "Fiestas Patrias (Independencia)",
    (7, 29): "Fiestas Patrias (Fuerzas Armadas)",
    (8, 6): "Batalla de Junín",
    (8, 30): "Santa Rosa de Lima",
    (10, 8): "Combate de Angamos",
    (11, 1): "Día de Todos los Santos",
    (12, 8): "Inmaculada Concepción",
    (12, 9): "Batalla de Ayacucho",
    (12, 25): "Navidad",
}

# Feriados móviles Semana Santa (Jueves y Viernes Santo)
MOVABLE_HOLIDAYS = {
    date(2025, 4, 17): "Jueves Santo",
    date(2025, 4, 18): "Viernes Santo",
    date(2026, 4, 2): "Jueves Santo",
    date(2026, 4, 3): "Viernes Santo",
    date(2027, 3, 25): "Jueves Santo",
    date(2027, 3, 26): "Viernes Santo",
}


def get_temporada_comercial(dt: date) -> str:
    """Clasifica la temporada comercial retail de Ripley según la fecha."""
    m, d = dt.month, dt.day

    # Campaña Navidad y Fin de Año
    if m == 12:
        return "Navidad y Fin de Año"
    # Black Friday / Cyber Ripley
    if m == 11 and d >= 20:
        return "Black Friday"
    # Cyber Wow de Octubre
    if m == 10 and 20 <= d <= 27:
        return "Cyber Wow"
    # Fiestas Patrias
    if m == 7 and d >= 15:
        return "Fiestas Patrias"
    # Día del Padre
    if m == 6 and 10 <= d <= 20:
        return "Día del Padre"
    # Día de la Madre
    if m == 5 and d <= 15:
        return "Día de la Madre"
    # Campaña Escolar
    if (m == 2 and d >= 15) or (m == 3 and d <= 15):
        return "Campaña Escolar"
    # Liquidación Verano
    if (m == 1) or (m == 2 and d < 15):
        return "Liquidación Verano"

    return "Regular"


def generate_dim_fecha_data():
    records = []
    curr = START_DATE
    while curr <= END_DATE:
        id_fecha = curr.year * 10000 + curr.month * 100 + curr.day
        anio = curr.year
        mes = curr.month
        trimestre = (mes - 1) // 3 + 1
        nombre_mes = SPANISH_MONTHS[mes]
        dia = curr.day
        numero_dia_semana = curr.isoweekday()  # 1 = Lunes, 7 = Domingo
        nombre_dia = SPANISH_DAYS[numero_dia_semana - 1]
        es_fin_de_semana = numero_dia_semana in (6, 7)

        # Feriado
        es_feriado = (curr.month, curr.day) in FIXED_PERU_HOLIDAYS or curr in MOVABLE_HOLIDAYS
        temporada = get_temporada_comercial(curr)

        records.append({
            "id_fecha": id_fecha,
            "fecha": curr.isoformat(),
            "anio": anio,
            "trimestre": trimestre,
            "mes": mes,
            "nombre_mes": nombre_mes,
            "dia": dia,
            "nombre_dia": nombre_dia,
            "numero_dia_semana": numero_dia_semana,
            "es_fin_de_semana": 1 if es_fin_de_semana else 0,
            "es_feriado": 1 if es_feriado else 0,
            "temporada_comercial": temporada,
        })
        curr += timedelta(days=1)
    return records


def generate_dim_hora_data():
    records = []
    for h in range(24):
        for m in range(60):
            id_hora = h * 100 + m
            franja = f"{h:02d}:00 - {h:02d}:59"

            # Clasificación de tipo horario
            if 18 <= h <= 20:
                tipo_horario = "Hora Pico"
            elif 11 <= h <= 17 or h == 21:
                tipo_horario = "Hora Normal"
            else:
                tipo_horario = "Hora Valle"

            # Turno laboral
            if 7 <= h <= 14:
                turno = "Mañana"
            elif 15 <= h <= 22:
                turno = "Tarde"
            else:
                turno = "Noche/Madrugada"

            records.append({
                "id_hora": id_hora,
                "hora_entera": h,
                "minuto": m,
                "franja_horaria": franja,
                "tipo_horario": tipo_horario,
                "turno": turno,
            })
    return records


def write_sql_seed_file(fechas, horas):
    """Genera el script SQL estático database/dw/02_seed_tiempo.sql."""
    SQL_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SQL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("-- =============================================================================\n")
        f.write("-- DATA WAREHOUSE RIPLEY (ripley_dw) - SEED ESTÁTICO DE DIMENSIONES TEMPORALES\n")
        f.write("-- Generado automáticamente por scripts/dw/populate_tiempo.py\n")
        f.write("-- Tablas: DIM_FECHA (2025-2027) y DIM_HORA (1440 minutos del día)\n")
        f.write("-- =============================================================================\n\n")
        f.write("USE `ripley_dw`;\n")
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET CHARACTER SET utf8mb4;\n\n")

        # Inserción en DIM_FECHA en lotes
        f.write("-- -----------------------------------------------------------------------------\n")
        f.write(f"-- 1. DIM_FECHA: {len(fechas)} DÍAS (2025-01-01 AL 2027-12-31)\n")
        f.write("-- -----------------------------------------------------------------------------\n")
        f.write("INSERT IGNORE INTO `DIM_FECHA` (`id_fecha`, `fecha`, `anio`, `trimestre`, `mes`, `nombre_mes`, `dia`, `nombre_dia`, `numero_dia_semana`, `es_fin_de_semana`, `es_feriado`, `temporada_comercial`) VALUES\n")
        fecha_rows = []
        for r in fechas:
            fecha_rows.append(
                f"({r['id_fecha']}, '{r['fecha']}', {r['anio']}, {r['trimestre']}, {r['mes']}, '{r['nombre_mes']}', {r['dia']}, '{r['nombre_dia']}', {r['numero_dia_semana']}, {r['es_fin_de_semana']}, {r['es_feriado']}, '{r['temporada_comercial']}')"
            )
        f.write(",\n".join(fecha_rows))
        f.write(";\n\n")

        # Inserción en DIM_HORA en lotes
        f.write("-- -----------------------------------------------------------------------------\n")
        f.write(f"-- 2. DIM_HORA: {len(horas)} MINUTOS (00:00 A 23:59)\n")
        f.write("-- -----------------------------------------------------------------------------\n")
        f.write("INSERT IGNORE INTO `DIM_HORA` (`id_hora`, `hora_entera`, `minuto`, `franja_horaria`, `tipo_horario`, `turno`) VALUES\n")
        hora_rows = []
        for r in horas:
            hora_rows.append(
                f"({r['id_hora']}, {r['hora_entera']}, {r['minuto']}, '{r['franja_horaria']}', '{r['tipo_horario']}', '{r['turno']}')"
            )
        f.write(",\n".join(hora_rows))
        f.write(";\n")

    print(f"📄 Archivo SQL generado: {SQL_OUTPUT_FILE.relative_to(ROOT_DIR)}")


def insert_into_database(fechas, horas):
    """Inserta las dimensiones generadas directamente en MySQL ripley_dw."""
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
        print(f"❌ Error al conectar a {DB_NAME}: {e}")
        print("💡 Verifica que el contenedor esté corriendo con make db-up y make dw-reset")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            cur.execute("SET NAMES utf8mb4;")
            cur.execute("SET CHARACTER SET utf8mb4;")

            # Inserción DIM_FECHA
            sql_fecha = """
                INSERT IGNORE INTO `DIM_FECHA` (
                    `id_fecha`, `fecha`, `anio`, `trimestre`, `mes`, `nombre_mes`,
                    `dia`, `nombre_dia`, `numero_dia_semana`, `es_fin_de_semana`,
                    `es_feriado`, `temporada_comercial`
                ) VALUES (
                    %(id_fecha)s, %(fecha)s, %(anio)s, %(trimestre)s, %(mes)s, %(nombre_mes)s,
                    %(dia)s, %(nombre_dia)s, %(numero_dia_semana)s, %(es_fin_de_semana)s,
                    %(es_feriado)s, %(temporada_comercial)s
                );
            """
            cur.executemany(sql_fecha, fechas)

            # Inserción DIM_HORA
            sql_hora = """
                INSERT IGNORE INTO `DIM_HORA` (
                    `id_hora`, `hora_entera`, `minuto`, `franja_horaria`, `tipo_horario`, `turno`
                ) VALUES (
                    %(id_hora)s, %(hora_entera)s, %(minuto)s, %(franja_horaria)s, %(tipo_horario)s, %(turno)s
                );
            """
            cur.executemany(sql_hora, horas)

            conn.commit()

        # Validar conteos
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM `DIM_FECHA`;")
            count_fechas = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `DIM_HORA`;")
            count_horas = cur.fetchone()[0]

            print(f"✅ Inserción en base de datos completada exitosamente:")
            print(f"   - DIM_FECHA: {count_fechas} registros (incluye comodín -1)")
            print(f"   - DIM_HORA : {count_horas} registros (incluye comodín -1)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error al insertar datos temporales en MySQL: {e}")
        sys.exit(1)
    finally:
        conn.close()


def main():
    print("=" * 65)
    print("⏳ GENERANDO DIMENSIONES TEMPORALES DETERMINISTAS (ripley_dw)")
    print(f"📅 Rango de Fechas: {START_DATE} al {END_DATE}")
    print("=" * 65)

    fechas = generate_dim_fecha_data()
    horas = generate_dim_hora_data()

    print(f"🔹 Generados {len(fechas)} días calendarios.")
    print(f"🔹 Generados {len(horas)} franjas de minutos diarios.")

    # Generar SQL estático
    write_sql_seed_file(fechas, horas)

    # Poblar base de datos activa
    insert_into_database(fechas, horas)

    print("\n🎉 Dimensiones temporales listas para análisis dimensional.")


if __name__ == "__main__":
    main()

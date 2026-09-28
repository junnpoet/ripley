#!/usr/bin/env python3
"""
Generador masivo de datos transaccionales para Ripley OLTP.
Produce suficiente volumen de transacciones para alcanzar ~11,000 registros
en la tabla de hechos FACT_VENTAS (DETALLE_COMPROBANTE), junto con telemetría IoT,
distribución realista de horas pico vs. horas valle, e inyección controlada de
anomalías de calidad de datos para justificar las reglas del proceso ETL.
"""

import os
import sys
import random
from datetime import datetime, timedelta, time
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "ripley_user")
DB_PASS = os.getenv("MYSQL_PASSWORD", "ripley_pass")
DB_NAME = os.getenv("MYSQL_DATABASE", "ripley_oltp")

TARGET_FACT_ROWS = 11200  # Para obtener ~11,000 hechos válidos tras depurar anulados
START_DATE = datetime(2026, 7, 1)
END_DATE = datetime(2026, 8, 31)  # 62 días de operación comercial


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=False,
    )


# -----------------------------------------------------------------------------
# Catálogos Maestros Ampliados
# -----------------------------------------------------------------------------

EXPANDED_CLIENTS = [
    ("00000000", "Clientes", "Varios", None, None, 1, False, 0),
    ("45892140", "Andrea", "Morales Soto", "andrea.m@gmail.com", "987112233", 2, True, 2400),
    ("72109845", "Mateo", "Vásquez Díaz", "mvasquez@hotmail.com", "991223344", 2, True, 1850),
    ("10293847", "Camila", "Cáceres Ramos", "cami.c@outlook.com", "976334455", 1, False, 320),
    ("41238901", "Rodrigo", "Herrera Gil", "r.herrera@yahoo.com", "965445566", 2, True, 5200),
    ("73491028", "Valeria", "Gutiérrez Peña", "valeria.g@gmail.com", "954556677", 1, False, 110),
    ("09812345", "Sebastián", "Navarro Castro", "sebas.nav@gmail.com", "943667788", 2, True, 3100),
    ("44556677", "Luciana", "Ponce Quintana", "lponce@empresa.com.pe", "932778899", 3, True, 4200),
    ("71239845", "Joaquín", "Delgado Ruiz", "jdelgado@outlook.com", "921889900", 1, False, 90),
    ("40918273", "Daniela", "Mendoza Cruz", "daniela.m@gmail.com", "910990011", 2, True, 1950),
    ("76543210", "Alejandro", "Cordero Salazar", "acordero@gmail.com", "987001122", 1, False, 450),
    ("10456789", "Mariana", "Ríos Paredes", "mrios@hotmail.com", "976112233", 2, True, 2800),
    ("43210987", "Gabriel", "Chávez Luna", "gchavez@outlook.com", "965223344", 1, False, 60),
    ("75612349", "Paula", "Benavides Silva", "paula.b@gmail.com", "954334455", 2, True, 3600),
    ("48901234", "Esteban", "Torres Aguirre", "etorres@gmail.com", "943445566", 3, True, 6100),
]

EXPANDED_PRODUCTS = [
    ("SKU-MRQ-JN01", "77512340001", "Jean Marquis Flare Skinny Azul", 1, 1, 2, 129.90, 48.00, False),
    ("SKU-MRQ-PL02", "77512340006", "Polo Marquis Básico Algodón Pima", 1, 1, 2, 49.90, 16.50, False),
    ("SKU-MRQ-BL03", "77512340007", "Blusa Marquis Satinada Manga Larga", 1, 1, 2, 89.90, 32.00, False),
    ("SKU-BRB-CS02", "77512340002", "Casaca Barbados Bomber Urbana", 2, 2, 2, 199.90, 75.00, False),
    ("SKU-BRB-SW04", "77512340008", "Sweater Barbados Cuello Redondo", 2, 2, 2, 99.90, 36.00, False),
    ("SKU-BRB-CH05", "77512340009", "Chaleco Acolchado Barbados Térmico", 2, 2, 2, 149.90, 52.00, False),
    ("SKU-NIK-RN03", "00883410003", "Zapatillas Nike Pegasus 40 Black", 3, 4, 3, 489.90, 240.00, False),
    ("SKU-NIK-TR06", "00883410010", "Polo Deportivo Nike Dri-FIT", 3, 4, 3, 119.90, 45.00, False),
    ("SKU-NIK-CS07", "00883410011", "Casaca Cortaviento Nike Windrunner", 3, 4, 3, 299.90, 135.00, False),
    ("SKU-SAM-TV04", "88060910004", "Smart TV Samsung 65 Neo QLED 4K", 4, 3, 1, 3499.00, 2150.00, True),
    ("SKU-SAM-S24", "88060910012", "Smartphone Samsung Galaxy S24 Ultra", 5, 3, 1, 5299.00, 3850.00, False),
    ("SKU-SAM-SB06", "88060910013", "Barra de Sonido Samsung Dolby Atmos", 4, 3, 1, 799.00, 420.00, False),
    ("SKU-APP-IP05", "01942520005", "Apple iPhone 15 Pro 128GB Titanio", 5, 5, 1, 4899.00, 3700.00, False),
    ("SKU-APP-AW07", "01942520014", "Apple Watch Series 9 GPS 45mm", 5, 5, 1, 1899.00, 1380.00, False),
    ("SKU-APP-AP08", "01942520015", "Auriculares Apple AirPods Pro Gen 2", 5, 5, 1, 999.00, 680.00, False),
    ("SKU-MRQ-VT09", "77512340016", "Vestido Marquis Corto Estampado", 1, 1, 2, 139.90, 46.00, False),
    ("SKU-BRB-JN10", "77512340017", "Jean Barbados Regular Fit Denim", 1, 2, 2, 119.90, 42.00, False),
    ("SKU-SAM-TV08", "88060910018", "Smart TV Samsung 55 Crystal UHD 4K", 4, 3, 1, 1699.00, 1050.00, True),
    ("SKU-NIK-ZN09", "00883410019", "Zapatillas Nike Revolution 7 Running", 3, 4, 3, 249.90, 110.00, False),
    ("SKU-BRB-PL11", "77512340020", "Polo Barbados Cuello V Estampado", 1, 2, 2, 59.90, 19.00, False),
]

EXPANDED_EMPLOYEES = [
    ("45892147", "Carlos Alberto", "Gómez Mendoza", 1, 1, "2023-03-15"),
    ("72145896", "María Fernanda", "Rojas Silva", 1, 1, "2024-01-10"),
    ("48963251", "Lucía Andrea", "Paredes Castro", 2, 1, "2024-06-01"),
    ("10254789", "Jorge Luis", "Vargas Salazar", 3, 1, "2022-08-20"),
    ("70258963", "Ana Sofía", "Torres Benítez", 1, 2, "2023-11-05"),
    ("43901245", "Diego Alonso", "Navarrete Flores", 1, 2, "2024-02-15"),
    ("76123489", "Claudia Elena", "Cabrera Hurtado", 2, 2, "2024-05-20"),
    ("15478963", "Renato Andrés", "Guerrero Vidal", 1, 3, "2023-09-12"),
    ("74125896", "Paola Vanessa", "Santillán Cueva", 1, 3, "2024-03-01"),
    ("42896314", "Fernando José", "Medina Orellana", 2, 3, "2024-04-18"),
]

# -----------------------------------------------------------------------------
# Catálogos Maestros Completos (Autosuficientes)
# -----------------------------------------------------------------------------

BASE_UBIGEOS = [
    ("150131", "Lima", "Lima", "Santiago de Surco"),
    ("150136", "Lima", "Lima", "San Miguel"),
    ("040103", "Arequipa", "Arequipa", "Cayma"),
]

BASE_TIENDAS = [
    (1, "RIP-JOK", "Ripley Jockey Plaza", "Av. Javier Prado Este 4200", "150131", 12500.00, 3500, "Activa"),
    (2, "RIP-SMI", "Ripley San Miguel", "Av. La Marina 2000", "150136", 8200.00, 2200, "Activa"),
    (3, "RIP-AQP", "Ripley Mall Aventura Arequipa", "Av. Porongoche 500", "040103", 9400.00, 2600, "Activa"),
]

BASE_TURNOS = [
    (1, "Mañana Apertura", "10:00:00", "14:00:00"),
    (2, "Tarde Pico", "14:00:00", "18:30:00"),
    (3, "Noche Cierre", "18:30:00", "22:00:00"),
]

BASE_ROLES = [
    (1, "Cajero Principal"),
    (2, "Cajero Volante"),
    (3, "Supervisor de Cajas"),
    (4, "Jefe de Tienda"),
]

BASE_PROVEEDORES = [
    (1, "20100070970", "Samsung Electronics Peru S.A.C.", "Juan Rivera", "01-7100000", "ventas@samsung.pe", "Credito 60 dias", "Activo"),
    (2, "20512345678", "Textil San Cristóbal S.A.", "Elena Morales", "01-4752000", "contacto@san-cristobal.pe", "Credito 30 dias", "Activo"),
    (3, "20334455667", "Nike European Operations Netherlands BV", "Gonzalo Peña", "01-6154000", "pe.ventas@nike.com", "Credito 45 dias", "Activo"),
]

BASE_LINEAS = [
    (1, "LIN-MOD", "Moda y Calzado"),
    (2, "LIN-TEC", "Electro y Tecnología"),
    (3, "LIN-DEC", "Decohogar"),
]

BASE_CATEGORIAS = [
    (1, 1, "Moda Mujer"),
    (2, 1, "Calzado Deportivo"),
    (3, 2, "Televisores y Audio"),
    (4, 2, "Smartphones"),
]

BASE_SUBCATEGORIAS = [
    (1, 1, "Jeans y Pantalones"),
    (2, 1, "Casacas y Abrigos"),
    (3, 2, "Zapatillas Running"),
    (4, 3, "Smart TV OLED"),
    (5, 4, "Celulares Gama Alta"),
]

BASE_MARCAS = [
    (1, "Marquis", True),
    (2, "Barbados", True),
    (3, "Samsung", False),
    (4, "Nike", False),
    (5, "Apple", False),
]

BASE_TIPOS_DOC = [
    (1, "01", "DNI - Documento Nacional de Identidad"),
    (2, "04", "Carnet de Extranjería"),
    (3, "06", "RUC - Registro Único de Contribuyentes"),
    (4, "07", "Pasaporte"),
]

BASE_TIPOS_CLIENTE = [
    (1, "Cliente Regular"),
    (2, "Cliente Tarjeta Ripley"),
    (3, "Colaborador Ripley"),
]

BASE_METODOS_PAGO = [
    (1, "TARJ_RIPLEY", "Tarjeta Ripley Clásica / Mastercard", False),
    (2, "TARJ_DEBITO", "Tarjeta Débito Visa / Mastercard", True),
    (3, "TARJ_CREDITO", "Tarjeta Crédito Externa (Visa/Mastercard/Amex)", True),
    (4, "EFECTIVO", "Efectivo Nuevos Soles", False),
    (5, "BILLETERA_DIGITAL", "Billetera Digital Yape / Plin", False),
]

ALL_CAJAS = [
    # Tienda 1: Jockey Plaza
    (1, 1, "Caja Tradicional", 1, "00:1A:2B:3C:4D:01"),
    (1, 2, "Caja Tradicional", 1, "00:1A:2B:3C:4D:02"),
    (1, 3, "Self-Checkout", 1, "00:1A:2B:3C:4D:03"),
    (1, 4, "Self-Checkout", 2, "00:1A:2B:3C:4D:04"),
    # Tienda 2: San Miguel
    (2, 1, "Caja Tradicional", 1, "00:1A:2B:3C:4E:01"),
    (2, 2, "Self-Checkout", 1, "00:1A:2B:3C:4E:02"),
    (2, 3, "Caja Tradicional", 1, "00:1A:2B:3C:4E:03"),
    (2, 4, "Self-Checkout", 2, "00:1A:2B:3C:4E:04"),
    # Tienda 3: Arequipa
    (3, 1, "Caja Tradicional", 1, "00:1A:2B:3C:4F:01"),
    (3, 2, "Caja Tradicional", 1, "00:1A:2B:3C:4F:02"),
    (3, 3, "Self-Checkout", 1, "00:1A:2B:3C:4F:03"),
    (3, 4, "Self-Checkout", 2, "00:1A:2B:3C:4F:04"),
]

ALL_ZONAS = [
    (1, "Acceso Principal Av. Javier Prado", "Acceso Exterior", 1200),
    (1, "Acceso Nivel 2 Boulevard Jockey", "Acceso Exterior", 900),
    (1, "Batería Cajas Centrales Nivel 1", "Bateria de Cajas", 400),
    (2, "Acceso Principal Av. La Marina", "Acceso Exterior", 1000),
    (2, "Batería Cajas Nivel 1", "Bateria de Cajas", 350),
    (3, "Acceso Principal Mall Aventura", "Acceso Exterior", 1100),
    (3, "Batería Cajas Central", "Bateria de Cajas", 400),
]

ALL_SENSORES = [
    (1, "IOT-CAM3D-JP-01", "Camara 3D Conteo Estereoscopico", "192.168.10.101"),
    (1, "IOT-CAM3D-JP-02", "Camara 3D Conteo Estereoscopico", "192.168.10.102"),
    (2, "IOT-TOF-JP-03", "Sensor ToF Infrarrojo", "192.168.10.103"),
    (4, "IOT-CAM3D-SM-01", "Camara 3D Conteo Estereoscopico", "192.168.20.101"),
    (4, "IOT-TOF-SM-02", "Sensor ToF Infrarrojo", "192.168.20.102"),
    (6, "IOT-CAM3D-AQP-01", "Camara 3D Conteo Estereoscopico", "192.168.30.101"),
    (6, "IOT-TOF-AQP-02", "Sensor ToF Infrarrojo", "192.168.30.102"),
]


def setup_masters(conn):
    """Puebla de forma completa y autosuficiente todos los catálogos maestros."""
    print("📋 Verificando y poblando catálogos maestros...")
    with conn.cursor() as cur:
        cur.execute("SET NAMES utf8mb4;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

        # Estructura Geográfica y Tiendas
        cur.executemany("INSERT IGNORE INTO `UBIGEO` (`id_ubigeo`, `departamento`, `provincia`, `distrito`) VALUES (%s, %s, %s, %s)", BASE_UBIGEOS)
        cur.executemany("INSERT IGNORE INTO `TIENDA` (`id_tienda`, `codigo_tienda`, `nombre`, `direccion`, `id_ubigeo`, `superficie_m2`, `aforo_maximo`, `estado`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", BASE_TIENDAS)
        cur.executemany("INSERT IGNORE INTO `TURNO_TRABAJO` (`id_turno`, `nombre_turno`, `hora_inicio`, `hora_fin`) VALUES (%s, %s, %s, %s)", BASE_TURNOS)
        cur.executemany("INSERT IGNORE INTO `ROL_EMPLEADO` (`id_rol`, `nombre_rol`) VALUES (%s, %s)", BASE_ROLES)
        cur.executemany("INSERT IGNORE INTO `CAJA_POS` (`id_tienda`, `numero_caja`, `tipo_caja`, `piso_ubicacion`, `mac_address`) VALUES (%s, %s, %s, %s, %s)", ALL_CAJAS)

        # Catálogo de Productos
        cur.executemany("INSERT IGNORE INTO `PROVEEDOR` (`id_proveedor`, `ruc`, `razon_social`, `contacto_comercial`, `telefono`, `email`, `condicion_pago`, `estado`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", BASE_PROVEEDORES)
        cur.executemany("INSERT IGNORE INTO `LINEA_COMERCIAL` (`id_linea`, `codigo_linea`, `nombre_linea`) VALUES (%s, %s, %s)", BASE_LINEAS)
        cur.executemany("INSERT IGNORE INTO `CATEGORIA` (`id_categoria`, `id_linea`, `nombre_categoria`) VALUES (%s, %s, %s)", BASE_CATEGORIAS)
        cur.executemany("INSERT IGNORE INTO `SUBCATEGORIA` (`id_subcategoria`, `id_categoria`, `nombre_subcategoria`) VALUES (%s, %s, %s)", BASE_SUBCATEGORIAS)
        cur.executemany("INSERT IGNORE INTO `MARCA` (`id_marca`, `nombre_marca`, `es_marca_propia`) VALUES (%s, %s, %s)", BASE_MARCAS)
        cur.executemany(
            """
            INSERT IGNORE INTO `PRODUCTO`
            (`sku`, `codigo_barras`, `nombre_producto`, `id_subcategoria`, `id_marca`, `id_proveedor`, `precio_lista`, `costo_estandar`, `requiere_despacho`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            EXPANDED_PRODUCTS,
        )

        # Clientes y Medios de Pago
        cur.executemany("INSERT IGNORE INTO `TIPO_DOCUMENTO` (`id_tipo_doc`, `codigo_sunat`, `descripcion`) VALUES (%s, %s, %s)", BASE_TIPOS_DOC)
        cur.executemany("INSERT IGNORE INTO `TIPO_CLIENTE` (`id_tipo_cliente`, `nombre_tipo`) VALUES (%s, %s)", BASE_TIPOS_CLIENTE)
        cur.executemany("INSERT IGNORE INTO `METODO_PAGO` (`id_metodo_pago`, `codigo_metodo`, `descripcion`, `aplica_comision`) VALUES (%s, %s, %s, %s)", BASE_METODOS_PAGO)
        cur.executemany(
            """
            INSERT IGNORE INTO `CLIENTE` 
            (`id_tipo_doc`, `numero_documento`, `nombres`, `apellidos`, `email`, `telefono`, `id_tipo_cliente`, `es_titular_tarjeta_ripley`, `puntos_ripley_acumulados`)
            VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            EXPANDED_CLIENTS,
        )

        # Empleados
        cur.executemany(
            """
            INSERT IGNORE INTO `EMPLEADO`
            (`dni`, `nombres`, `apellidos`, `id_rol`, `id_tienda_base`, `fecha_ingreso`)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            EXPANDED_EMPLOYEES,
        )

        # Zonas y Sensores IoT
        cur.executemany("INSERT IGNORE INTO `ZONA_TIENDA` (`id_tienda`, `nombre_zona`, `tipo_zona`, `aforo_limite`) VALUES (%s, %s, %s, %s)", ALL_ZONAS)
        cur.executemany("INSERT IGNORE INTO `DISPOSITIVO_SENSOR` (`id_zona`, `codigo_sensor`, `tipo_sensor`, `ip_dispositivo`) VALUES (%s, %s, %s, %s)", ALL_SENSORES)

        # Inventario Inicial para cada tienda y producto
        cur.execute("SELECT id_tienda FROM `TIENDA`;")
        tiendas = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id_producto FROM `PRODUCTO`;")
        productos = [r[0] for r in cur.fetchall()]

        inventarios = []
        for t_id in tiendas:
            for p_id in productos:
                inventarios.append((t_id, p_id, 30, 80, 0, 10))

        cur.executemany(
            """
            INSERT IGNORE INTO `INVENTARIO_TIENDA`
            (`id_tienda`, `id_producto`, `stock_piso_venta`, `stock_almacen`, `stock_comprometido`, `punto_reorden`)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            inventarios,
        )

        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

    conn.commit()
    print("  ✓ Todos los maestros e inventarios inicializados.")


def generate_transactions(conn):
    """Genera las transacciones con distribución de horas pico y anomalías ETL."""
    print("\n🛒 Generando transacciones comerciales (objetivo: ~11,000 hechos)...")

    with conn.cursor() as cur:
        # Obtener IDs reales de la base de datos
        cur.execute("SELECT id_producto, precio_lista, costo_estandar FROM PRODUCTO WHERE estado='Activo';")
        products = cur.fetchall()  # [(id, precio, costo), ...]

        cur.execute("SELECT id_cliente FROM CLIENTE;")
        client_ids = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT id_caja, id_tienda FROM CAJA_POS WHERE estado='Operativa';")
        cajas = cur.fetchall()  # [(id_caja, id_tienda), ...]

        cur.execute("SELECT id_empleado, id_tienda_base FROM EMPLEADO WHERE estado='Activo';")
        empleados = cur.fetchall()

        cur.execute("SELECT id_metodo_pago FROM METODO_PAGO;")
        payment_methods = [row[0] for row in cur.fetchall()]

    # Mapeo de cajas por tienda y empleados por tienda
    cajas_by_tienda = {}
    for c_id, t_id in cajas:
        cajas_by_tienda.setdefault(t_id, []).append(c_id)

    emp_by_tienda = {}
    for e_id, t_id in empleados:
        emp_by_tienda.setdefault(t_id, []).append(e_id)

    # Limpiar eventos transaccionales previos para evitar duplicación
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("TRUNCATE TABLE `DETALLE_COMPROBANTE`;")
        cur.execute("TRUNCATE TABLE `PAGO_COMPROBANTE`;")
        cur.execute("TRUNCATE TABLE `COMPROBANTE_PAGO`;")
        cur.execute("TRUNCATE TABLE `ASIGNACION_CAJA`;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()

    # 1. Generar Asignaciones de caja por día y turno
    print("  → Creando sesiones de apertura de caja (ASIGNACION_CAJA)...")
    curr_date = START_DATE
    asignaciones = []  # (id_caja, id_empleado, id_turno, fecha, apertura, cierre, saldo_ini, saldo_fin)

    while curr_date <= END_DATE:
        for t_id in [1, 2, 3]:
            store_cajas = cajas_by_tienda.get(t_id, [])
            store_emps = emp_by_tienda.get(t_id, [])
            if not store_cajas or not store_emps:
                continue

            for caja_id in store_cajas:
                emp_id = random.choice(store_emps)
                # Turno 2 (Tarde Pico) cubre las horas pico principales
                for turno_id, h_ini, h_fin in [(1, "10:00:00", "14:00:00"), (2, "14:00:00", "18:30:00"), (3, "18:30:00", "22:00:00")]:
                    apertura = datetime.combine(curr_date.date(), datetime.strptime(h_ini, "%H:%M:%S").time())
                    cierre = datetime.combine(curr_date.date(), datetime.strptime(h_fin, "%H:%M:%S").time())
                    asignaciones.append((caja_id, emp_id, turno_id, curr_date.date(), apertura, cierre, 300.0, 4200.0))

        curr_date += timedelta(days=1)

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO `ASIGNACION_CAJA`
            (`id_caja`, `id_empleado`, `id_turno`, `fecha_operacion`, `hora_apertura`, `hora_cierre`, `saldo_inicial`, `saldo_final`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            asignaciones,
        )
    conn.commit()

    # Mapeo rápido de asignaciones para asociar a comprobantes
    with conn.cursor() as cur:
        cur.execute("SELECT id_asignacion, id_caja, id_empleado, fecha_operacion, hora_apertura, hora_cierre FROM ASIGNACION_CAJA;")
        asig_rows = cur.fetchall()

    asig_map = {}  # (id_caja, date, turno_hora) -> (id_asig, id_emp)
    for asig_id, c_id, e_id, f_op, h_ap, h_ci in asig_rows:
        asig_map.setdefault((c_id, f_op), []).append((asig_id, e_id, h_ap, h_ci))

    print(f"  ✓ {len(asignaciones)} sesiones de caja generadas.")

    # 2. Generación de Comprobantes, Detalles y Pagos
    print("  → Generando tickets de venta y líneas atómicas...")
    total_days = (END_DATE - START_DATE).days + 1
    # Calculamos tickets diarios necesarios para sumar ~11,200 líneas (aprox. 3 líneas por ticket = ~3,750 tickets)
    tickets_target = 3900
    tickets_per_day_base = tickets_target // total_days

    comprobantes_batch = []
    detalles_batch = []
    pagos_batch = []

    correlativo_counter = 100000
    comp_id_virtual = 1  # Para referenciar detalles antes del insert si autoincrement

    curr_date = START_DATE
    anomalias_anulados = 0
    anomalias_outliers_tiempo = 0

    while curr_date <= END_DATE:
        is_weekend = curr_date.weekday() >= 5
        # En fines de semana hay 40% más de afluencia y compras
        daily_tickets_count = int(tickets_per_day_base * (1.45 if is_weekend else 0.95))
        for _ in range(daily_tickets_count):
            available_tiendas = [t for t in [1, 2, 3] if t in cajas_by_tienda and cajas_by_tienda[t]]
            weights = [50 if t == 1 else 30 if t == 2 else 20 for t in available_tiendas]
            tienda_id = random.choices(available_tiendas, weights=weights)[0]
            caja_id = random.choice(cajas_by_tienda[tienda_id])

            # DISTRIBUCIÓN DE HORAS PICO:
            # 65% probabilidad de ocurrir en Horas Pico (18:00 - 21:00) o (13:00 - 15:00)
            rand_val = random.random()
            if rand_val < 0.65:
                # Hora Pico de tarde/noche (18:00 a 21:00)
                hora = random.randint(18, 20)
                minuto = random.randint(0, 59)
                segundo = random.randint(0, 59)
                # Tiempos de atención y espera más altos por saturación
                tiempo_espera = random.randint(240, 750)  # 4 a 12 min en cola
                tiempo_atencion = random.randint(110, 320)
            elif rand_val < 0.85:
                # Hora Normal / Almuerzo (13:00 a 16:00)
                hora = random.randint(13, 15)
                minuto = random.randint(0, 59)
                segundo = random.randint(0, 59)
                tiempo_espera = random.randint(60, 240)
                tiempo_atencion = random.randint(80, 200)
            else:
                # Hora Valle (10:00 a 12:59 o 21:00 a 22:00)
                hora = random.choice([10, 11, 12, 21])
                minuto = random.randint(0, 59)
                segundo = random.randint(0, 59)
                tiempo_espera = random.randint(20, 90)
                tiempo_atencion = random.randint(60, 150)

            fecha_hora_emision = datetime(curr_date.year, curr_date.month, curr_date.day, hora, minuto, segundo)
            fecha_hora_inicio = fecha_hora_emision - timedelta(seconds=tiempo_atencion)

            # Buscar sesión de caja adecuada
            sessions = asig_map.get((caja_id, curr_date.date()), [])
            if sessions:
                asig_id, emp_id, _, _ = random.choice(sessions)
            else:
                asig_id, emp_id = 1, 1

            # Inyección de Anomalía 1: Outlier de tiempo de atención (1% de los casos)
            if random.random() < 0.012:
                anomalias_outliers_tiempo += 1
                tiempo_atencion = random.choice([0, 3600, 4200])  # Error en caja express o caja congelada

            # Inyección de Anomalía 2: Comprobante Anulado o Devuelto (4.5% de los casos)
            if random.random() < 0.045:
                estado = random.choice(["Anulado", "Devuelto"])
                anomalias_anulados += 1
            else:
                estado = "Emitido"

            # Cliente (15% probabilidad de "Cliente Varios" o no identificado)
            if random.random() < 0.15:
                cliente_id = 1  # Clientes Varios (DNI 00000000)
            else:
                cliente_id = random.choice(client_ids)

            tipo_comp = "Factura" if random.random() < 0.15 else "Boleta de Venta"
            serie = f"B00{tienda_id}" if tipo_comp == "Boleta de Venta" else f"F00{tienda_id}"
            correlativo_counter += 1

            # Generar líneas de detalle (1 a 5 items por ticket)
            num_items = random.choices([1, 2, 3, 4, 5], weights=[25, 40, 20, 10, 5])[0]
            ticket_subtotal = 0.0
            ticket_descuento = 0.0

            ticket_detalles = []
            for _ in range(num_items):
                prod_id, p_lista, c_costo = random.choice(products)
                cant = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
                
                # Descuento ocasional por Tarjeta Ripley o promoción
                desc_unit = float(p_lista) * 0.15 if random.random() < 0.25 else 0.0
                p_venta = float(p_lista) - desc_unit
                subtotal_linea = round(p_venta * cant, 2)

                ticket_subtotal += subtotal_linea
                ticket_descuento += round(desc_unit * cant, 2)

                ticket_detalles.append((comp_id_virtual, prod_id, cant, round(p_venta, 2), float(c_costo), round(desc_unit, 2), subtotal_linea))

            # Cálculo impositivo peruano (18% IGV)
            monto_total = round(ticket_subtotal, 2)
            subtotal_gravado = round(monto_total / 1.18, 2)
            igv = round(monto_total - subtotal_gravado, 2)

            comprobantes_batch.append((
                comp_id_virtual, tienda_id, caja_id, emp_id, cliente_id, asig_id,
                tipo_comp, serie, correlativo_counter,
                fecha_hora_inicio, fecha_hora_emision, tiempo_atencion,
                subtotal_gravado, igv, ticket_descuento, monto_total, estado
            ))

            detalles_batch.extend(ticket_detalles)

            # Pago del comprobante
            metodo_pago = random.choice(payment_methods)
            pagos_batch.append((
                comp_id_virtual, metodo_pago, monto_total,
                f"AUTH-{random.randint(100000, 999999)}", fecha_hora_emision
            ))

            comp_id_virtual += 1

        curr_date += timedelta(days=1)

    print(f"  ✓ Generados {len(comprobantes_batch)} comprobantes y {len(detalles_batch)} líneas de detalle.")
    print(f"    - Anomalías inyectadas: {anomalias_anulados} anulados/devueltos, {anomalias_outliers_tiempo} outliers de tiempo.")

    # Inserción masiva en lotes de 1,000 registros
    print("  → Insertando en MySQL (lotes masivos para alto rendimiento)...")
    batch_size = 1000
    with conn.cursor() as cur:
        # 1. Comprobantes
        for i in range(0, len(comprobantes_batch), batch_size):
            chunk = comprobantes_batch[i:i + batch_size]
            cur.executemany(
                """
                INSERT INTO `COMPROBANTE_PAGO`
                (`id_comprobante`, `id_tienda`, `id_caja`, `id_empleado`, `id_cliente`, `id_asignacion`,
                 `tipo_comprobante`, `serie`, `numero_correlativo`, `fecha_hora_inicio_atencion`,
                 `fecha_hora_emision`, `tiempo_atencion_segundos`, `subtotal_gravado`, `igv`,
                 `total_descuento`, `monto_total`, `estado`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                chunk,
            )

        # 2. Detalles
        for i in range(0, len(detalles_batch), batch_size):
            chunk = detalles_batch[i:i + batch_size]
            cur.executemany(
                """
                INSERT INTO `DETALLE_COMPROBANTE`
                (`id_comprobante`, `id_producto`, `cantidad`, `precio_unitario_venta`,
                 `costo_unitario_historico`, `descuento_unitario`, `subtotal_linea`)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                chunk,
            )

        # 3. Pagos
        for i in range(0, len(pagos_batch), batch_size):
            chunk = pagos_batch[i:i + batch_size]
            cur.executemany(
                """
                INSERT INTO `PAGO_COMPROBANTE`
                (`id_comprobante`, `id_metodo_pago`, `monto_pagado`, `numero_operacion_pos`, `fecha_hora_pago`)
                VALUES (%s, %s, %s, %s, %s)
                """,
                chunk,
            )

    conn.commit()


def generate_iot_telemetry(conn):
    """Genera lecturas de afluencia IoT sincronizadas para el Drill-Across de horas pico."""
    print("\n📡 Generando telemetría de afluencia IoT (sensores cada 30 min)...")

    with conn.cursor() as cur:
        cur.execute("SELECT id_dispositivo, id_zona FROM DISPOSITIVO_SENSOR WHERE estado='Activo';")
        sensors = cur.fetchall()

    if not sensors:
        print("⚠️ No hay sensores activos.")
        return

    iot_batch = []
    curr_date = START_DATE

    while curr_date <= END_DATE:
        is_weekend = curr_date.weekday() >= 5
        base_mult = 1.35 if is_weekend else 1.0

        for sens_id, _ in sensors:
            # Horario comercial: 10:00 a 22:00 en intervalos de 30 minutos
            for h in range(10, 22):
                for m in [0, 30]:
                    dt = datetime(curr_date.year, curr_date.month, curr_date.day, h, m, 0)

                    # Flujo según hora pico (18:00 a 21:00 mayor afluencia)
                    if 18 <= h <= 20:
                        entradas = int(random.randint(180, 320) * base_mult)
                        salidas = int(random.randint(70, 160) * base_mult)
                        aforo = int(random.randint(1400, 2800) * base_mult)
                    elif 13 <= h <= 15:
                        entradas = int(random.randint(90, 160) * base_mult)
                        salidas = int(random.randint(80, 140) * base_mult)
                        aforo = int(random.randint(800, 1500) * base_mult)
                    else:
                        entradas = int(random.randint(30, 80) * base_mult)
                        salidas = int(random.randint(25, 75) * base_mult)
                        aforo = int(random.randint(350, 800) * base_mult)

                    iot_batch.append((sens_id, dt, entradas, salidas, aforo))

        curr_date += timedelta(days=1)

    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("TRUNCATE TABLE `LOG_AFLUENCIA_IOT`;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

        for i in range(0, len(iot_batch), 1000):
            chunk = iot_batch[i:i + 1000]
            cur.executemany(
                """
                INSERT INTO `LOG_AFLUENCIA_IOT`
                (`id_dispositivo`, `fecha_hora_lectura`, `conteo_entradas`, `conteo_salidas`, `aforo_instantaneo_calculado`)
                VALUES (%s, %s, %s, %s, %s)
                """,
                chunk,
            )

    conn.commit()
    print(f"  ✓ {len(iot_batch)} lecturas de telemetría IoT insertadas exitosamente.")


def main():
    print("=" * 70)
    print("🚀 GENERADOR DE DATOS DE ALTA CARGA - PROYECTO RIPLEY IN")
    print(f"🎯 Meta: ~{TARGET_FACT_ROWS} filas en DETALLE_COMPROBANTE (FACT_VENTAS)")
    print(f"📅 Rango de fechas: {START_DATE.strftime('%Y-%m-%d')} a {END_DATE.strftime('%Y-%m-%d')}")
    print("=" * 70)

    try:
        conn = get_connection()
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        sys.exit(1)

    try:
        setup_masters(conn)
        generate_transactions(conn)
        generate_iot_telemetry(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM `DETALLE_COMPROBANTE`;")
            total_detalles = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `COMPROBANTE_PAGO`;")
            total_tickets = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `LOG_AFLUENCIA_IOT`;")
            total_iot = cur.fetchone()[0]

        print("\n" + "=" * 70)
        print("🎉 GENERACIÓN Y CARGA MASIVA COMPLETADA")
        print(f"  📦 Total Comprobantes (Tickets):     {total_tickets:,}")
        print(f"  🛒 Total DETALLE_COMPROBANTE:       {total_detalles:,} (alimentará FACT_VENTAS)")
        print(f"  📡 Total Registros IoT:             {total_iot:,} (alimentará FACT_AFLUENCIA_TIENDA)")
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

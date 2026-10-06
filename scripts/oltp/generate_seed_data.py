#!/usr/bin/env python3
"""
Generador masivo de datos transaccionales para Ripley OLTP.
Produce catálogo a escala de tienda por departamento (~5,000 productos, 38 subcategorías,
44 marcas, 25 proveedores, 15,000 registros de inventario), padrón de clientes (~6,000 registros),
dotación de personal por sede, transacciones comerciales masivas (~50,000 comprobantes con
distribución de Pareto en ventas y horas pico) y telemetría IoT sincronizada.
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

TARGET_PRODUCTS = 5000       # Catálogo ampliado de retail multidepartamental
TARGET_TICKETS = 50000       # Transacciones comerciales objetivo
NUM_CLIENTES = 6000          # Base de clientes registrados
CHUNK_SIZE = 5000            # Lotes de inserción masiva
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
# Catálogos Maestros de Infraestructura y Negocio
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
    # Tienda 1: Jockey Plaza (4 Cajas)
    (1, 1, "Caja Tradicional", 1, "00:1A:2B:3C:4D:01"),
    (1, 2, "Caja Tradicional", 1, "00:1A:2B:3C:4D:02"),
    (1, 3, "Self-Checkout", 1, "00:1A:2B:3C:4D:03"),
    (1, 4, "Self-Checkout", 2, "00:1A:2B:3C:4D:04"),
    # Tienda 2: San Miguel (4 Cajas)
    (2, 1, "Caja Tradicional", 1, "00:1A:2B:3C:4E:01"),
    (2, 2, "Self-Checkout", 1, "00:1A:2B:3C:4E:02"),
    (2, 3, "Caja Tradicional", 1, "00:1A:2B:3C:4E:03"),
    (2, 4, "Self-Checkout", 2, "00:1A:2B:3C:4E:04"),
    # Tienda 3: Arequipa (4 Cajas)
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

EXPANDED_EMPLOYEES = [
    # Tienda 1: Jockey Plaza (12 colaboradores)
    ("45892147", "Carlos Alberto", "Gómez Mendoza", 1, 1, "2023-03-15"),
    ("72145896", "María Fernanda", "Rojas Silva", 1, 1, "2024-01-10"),
    ("48963251", "Lucía Andrea", "Paredes Castro", 1, 1, "2024-06-01"),
    ("10254789", "Jorge Luis", "Vargas Salazar", 3, 1, "2022-08-20"),
    ("41258963", "Renzo Gabriel", "Carrillo Tapia", 1, 1, "2023-05-11"),
    ("70142589", "Fiorella Milagros", "Sánchez Huamán", 1, 1, "2023-11-20"),
    ("44896325", "Álvaro Daniel", "Montoya Rivas", 2, 1, "2024-02-01"),
    ("73258961", "Diana Carolina", "Castillo Flores", 1, 1, "2024-03-15"),
    ("46985214", "Christian Jesús", "Morales Gil", 2, 1, "2024-04-10"),
    ("71526398", "Brenda Jimena", "Navarro Díaz", 1, 1, "2023-09-01"),
    ("43652147", "Víctor Manuel", "Ramos Peña", 3, 1, "2022-10-15"),
    ("10985214", "Eduardo José", "Benavides Luna", 4, 1, "2021-06-01"),

    # Tienda 2: San Miguel (9 colaboradores)
    ("70258963", "Ana Sofía", "Torres Benítez", 1, 2, "2023-11-05"),
    ("43901245", "Diego Alonso", "Navarrete Flores", 1, 2, "2024-02-15"),
    ("76123489", "Claudia Elena", "Cabrera Hurtado", 2, 2, "2024-05-20"),
    ("42158796", "Sebastián Andrés", "García Vidal", 1, 2, "2023-08-14"),
    ("71896541", "Valeria Nicole", "Quispe Mamani", 1, 2, "2024-01-22"),
    ("45632198", "Mateo Rodrigo", "Chávez Salazar", 1, 2, "2024-03-01"),
    ("74521489", "Camila Alejandra", "Mendoza Ruiz", 2, 2, "2024-04-18"),
    ("40258963", "Javier Hernán", "Ponce Espinoza", 3, 2, "2022-12-01"),
    ("15987452", "Hugo David", "Alarcón Romero", 4, 2, "2021-09-10"),

    # Tienda 3: Mall Aventura Arequipa (9 colaboradores)
    ("15478963", "Renato Andrés", "Guerrero Vidal", 1, 3, "2023-09-12"),
    ("74125896", "Paola Vanessa", "Santillán Cueva", 1, 3, "2024-03-01"),
    ("42896314", "Fernando José", "Medina Orellana", 2, 3, "2024-04-18"),
    ("70589632", "Gabriela Jimena", "Valdivia Condori", 1, 3, "2023-07-20"),
    ("44785214", "Manuel Ricardo", "Tello Villanueva", 1, 3, "2023-10-05"),
    ("72365418", "Adriana Lucía", "Huamán Mamani", 1, 3, "2024-02-10"),
    ("46123987", "David Gonzalo", "Pacheco Zúñiga", 2, 3, "2024-05-02"),
    ("75896321", "César Augusto", "Bustamante Prado", 3, 3, "2022-11-15"),
    ("12365478", "Mario Francisco", "Solís Meléndez", 4, 3, "2021-08-01"),
]


# -----------------------------------------------------------------------------
# Estructura Jerárquica Comercial y Proveedores Ampliada
# -----------------------------------------------------------------------------

BASE_LINEAS = [
    (1, "LIN-MOD", "Moda y Calzado"),
    (2, "LIN-TEC", "Electro y Tecnología"),
    (3, "LIN-DEC", "Decohogar"),
    (4, "LIN-BEL", "Belleza y Perfumería"),
    (5, "LIN-DEP", "Deportes y Outdoor"),
    (6, "LIN-INF", "Infantil y Juguetería"),
]

BASE_CATEGORIAS = [
    # Línea 1: Moda y Calzado
    (1, 1, "Moda Mujer"),
    (2, 1, "Moda Hombre"),
    (3, 1, "Calzado y Zapatillas"),
    # Línea 2: Electro y Tecnología
    (4, 2, "Televisores y Audio"),
    (5, 2, "Smartphones y Telefonía"),
    (6, 2, "Cómputo y Laptops"),
    (7, 2, "Electrohogar y Línea Blanca"),
    # Línea 3: Decohogar
    (8, 3, "Dormitorio y Colchones"),
    (9, 3, "Muebles de Sala y Comedor"),
    (10, 3, "Menaje y Cocina"),
    # Línea 4: Belleza y Perfumería
    (11, 4, "Perfumería y Fragancias"),
    (12, 4, "Cuidado Facial y Maquillaje"),
    # Línea 5: Deportes y Outdoor
    (13, 5, "Ropa y Calzado Deportivo"),
    (14, 5, "Máquinas y Fitness"),
    # Línea 6: Infantil y Juguetería
    (15, 6, "Juguetes y Juegos de Mesa"),
    (16, 6, "Moda Infantil y Bebés"),
]

BASE_SUBCATEGORIAS = [
    # Moda Mujer
    (1, 1, "Jeans y Denim Mujer"),
    (2, 1, "Blusas, Tops y Polos Mujer"),
    (3, 1, "Casacas y Abrigos Mujer"),
    (4, 1, "Vestidos y Faldas"),
    # Moda Hombre
    (5, 2, "Jeans y Pantalones Hombre"),
    (6, 2, "Polos y Camisas Hombre"),
    (7, 2, "Casacas y Chompas Hombre"),
    # Calzado
    (8, 3, "Zapatillas Urbanas"),
    (9, 3, "Zapatos y Botines"),
    # Televisores y Audio
    (10, 4, "Smart TV 4K, OLED y QLED"),
    (11, 4, "Barras de Sonido y Audio"),
    # Smartphones y Telefonía
    (12, 5, "Smartphones Gama Alta y Media"),
    (13, 5, "Smartwatches y Wearables"),
    # Cómputo
    (14, 6, "Laptops y Notebooks"),
    (15, 6, "Monitores y Accesorios"),
    # Electrohogar
    (16, 7, "Refrigeradoras y Congeladoras"),
    (17, 7, "Lavadoras y Secadoras"),
    (18, 7, "Cocinas, Hornos y Microondas"),
    # Dormitorio
    (19, 8, "Colchones y Box Spring"),
    (20, 8, "Ropa de Cama, Sábanas y Plumones"),
    (21, 8, "Almohadas y Accesorios de Cama"),
    # Muebles
    (22, 9, "Sofás, Seccionales y Sillones"),
    (23, 9, "Juegos de Comedor y Sillas"),
    # Menaje
    (24, 10, "Baterías de Cocina y Sartenes"),
    (25, 10, "Vajilla, Vasos y Cristalería"),
    # Perfumería
    (26, 11, "Perfumes y Fragancias Mujer"),
    (27, 11, "Perfumes y Fragancias Hombre"),
    # Cuidado Facial
    (28, 12, "Tratamiento Facial y Cremas"),
    # Deportes
    (29, 13, "Zapatillas de Running"),
    (30, 13, "Ropa Deportiva Training"),
    (31, 14, "Trotadoras y Máquinas de Ejercicio"),
    (32, 14, "Mancuernas y Accesorios de Fuerza"),
    # Juguetes
    (33, 15, "Figuras de Acción y Muñecas"),
    (34, 15, "Juegos de Construcción y Mesa"),
    # Infantil
    (35, 16, "Ropa y Bodys para Bebés"),
    (36, 16, "Coches y Sillas para Auto"),
]

BASE_MARCAS = [
    # Marcas Propias Ripley (10)
    (1, "Marquis", True),
    (2, "Barbados", True),
    (3, "Index", True),
    (4, "Harvest", True),
    (5, "Aziz", True),
    (6, "Ripley Home", True),
    (7, "Tatienne", True),
    (8, "Cloudbreak", True),
    (9, "Regatta", True),
    (10, "Navigata", True),
    # Marcas Comerciales Externas (34)
    (11, "Samsung", False),
    (12, "Apple", False),
    (13, "LG", False),
    (14, "Sony", False),
    (15, "Xiaomi", False),
    (16, "HP", False),
    (17, "Lenovo", False),
    (18, "Asus", False),
    (19, "Oster", False),
    (20, "Bosch", False),
    (21, "Mabe", False),
    (22, "Electrolux", False),
    (23, "Nike", False),
    (24, "Adidas", False),
    (25, "Puma", False),
    (26, "Under Armour", False),
    (27, "Skechers", False),
    (28, "Vans", False),
    (29, "Converse", False),
    (30, "Paraíso", False),
    (31, "Rosen", False),
    (32, "Forli", False),
    (33, "Drimer", False),
    (34, "Carolina Herrera", False),
    (35, "Paco Rabanne", False),
    (36, "Dior", False),
    (37, "L'Oréal", False),
    (38, "Clinique", False),
    (39, "Lego", False),
    (40, "Hasbro", False),
    (41, "Mattel", False),
    (42, "Monark", False),
    (43, "Oxford", False),
    (44, "Chicco", False),
]

BASE_PROVEEDORES = [
    (1, "20100070970", "Samsung Electronics Peru S.A.C.", "Juan Rivera", "01-7100000", "ventas@samsung.pe", "Credito 60 dias", "Activo"),
    (2, "20512345678", "Textil San Cristóbal S.A.", "Elena Morales", "01-4752000", "contacto@san-cristobal.pe", "Credito 30 dias", "Activo"),
    (3, "20334455667", "Nike European Operations Netherlands BV", "Gonzalo Peña", "01-6154000", "pe.ventas@nike.com", "Credito 45 dias", "Activo"),
    (4, "20601234567", "Apple Perú S.R.L.", "Mariana Thorne", "01-5128000", "distribucion@apple.pe", "Credito 30 dias", "Activo"),
    (5, "20100123456", "Productos Paraíso del Perú S.A.C.", "Héctor Barrientos", "01-6142000", "corporativo@paraiso.pe", "Credito 60 dias", "Activo"),
    (6, "20258963147", "Rosen Perú S.A.", "Patricia Véliz", "01-7053000", "ventas@rosen.pe", "Credito 45 dias", "Activo"),
    (7, "20345678901", "Sony Perú S.R.L.", "Ricardo Fujimori", "01-6188000", "corporativo@sony.pe", "Credito 30 dias", "Activo"),
    (8, "20456789012", "LG Electronics Perú S.A.", "Claudia Benavides", "01-7109000", "b2b@lge.pe", "Credito 60 dias", "Activo"),
    (9, "20501478963", "Adidas Perú S.A.C.", "Mauricio Castro", "01-6117000", "ventas@adidas.pe", "Credito 45 dias", "Activo"),
    (10, "20514789632", "Puma Sports Perú S.A.C.", "Vanessa Salazar", "01-6184500", "contacto@puma.pe", "Credito 30 dias", "Activo"),
    (11, "20301478965", "BSH Electrodomésticos S.A.C. (Bosch)", "Raúl Méndez", "01-2139000", "ventas@bshg.com", "Credito 60 dias", "Activo"),
    (12, "20102589631", "Oster de Perú S.A.", "Silvia Campos", "01-6194000", "pedidos@oster.pe", "Credito 45 dias", "Activo"),
    (13, "20547896321", "HP Inc. Perú S.R.L.", "Felipe Torres", "01-7005000", "ventas@hp.com.pe", "Credito 30 dias", "Activo"),
    (14, "20569874123", "Lenovo Perú S.R.L.", "Karina Ramos", "01-6189500", "comercial@lenovo.pe", "Credito 30 dias", "Activo"),
    (15, "20336589741", "L'Oréal Perú S.A.", "Daniela Prado", "01-2114000", "pedidos@loreal.com", "Credito 45 dias", "Activo"),
    (16, "20412589632", "Puig Perú S.A.", "Esteban Vildoso", "01-6127800", "distribucion@puig.pe", "Credito 30 dias", "Activo"),
    (17, "20603698521", "Lego System A/S Sucursal Perú", "Andrea Cáceres", "01-5129900", "ventas@lego.pe", "Credito 30 dias", "Activo"),
    (18, "20503698521", "Hasbro Perú S.A.C.", "Jorge Del Busto", "01-6183300", "comercial@hasbro.pe", "Credito 45 dias", "Activo"),
    (19, "20258741369", "Mattel Perú S.A.", "Rosa María Alva", "01-4458900", "contacto@mattel.pe", "Credito 45 dias", "Activo"),
    (20, "20103698524", "Monark Perú S.A.", "César Hurtado", "01-6134000", "ventas@monark.pe", "Credito 60 dias", "Activo"),
    (21, "20458796321", "Devanlay Perú S.A.C.", "Guillermo Silva", "01-4758900", "textil@devanlay.pe", "Credito 30 dias", "Activo"),
    (22, "20332589614", "Forli Perú S.A.C.", "Arturo Vega", "01-6148000", "contacto@forli.com.pe", "Credito 60 dias", "Activo"),
    (23, "20258963478", "Mabe Perú S.A.", "Luz Marina Ruiz", "01-7108800", "ventas@mabe.com.pe", "Credito 45 dias", "Activo"),
    (24, "20604587963", "Xiaomi Perú S.A.C.", "Kevin Zhang", "01-7089900", "distribucion@xiaomi.pe", "Credito 30 dias", "Activo"),
    (25, "20521478963", "Distribuidora D'Bebé S.A.C.", "Patricia Wong", "01-6192200", "pedidos@dbebe.pe", "Credito 30 dias", "Activo"),
]


# -----------------------------------------------------------------------------
# Generadores Dinámicos: Clientes y Productos Masivos
# -----------------------------------------------------------------------------

def generate_clients_dataset(count=NUM_CLIENTES):
    """Genera el padrón diverso y representativo de clientes peruanos."""
    first_names_m = [
        "Carlos", "Luis", "Juan", "José", "Miguel", "Jorge", "Diego", "Fernando", "Alejandro", "Mateo",
        "Sebastián", "Rodrigo", "Joaquín", "Esteban", "Gabriel", "Renzo", "Christian", "Álvaro", "Víctor", "Manuel",
        "Gonzalo", "Rafael", "Mario", "David", "Ricardo", "Daniel", "Eduardo", "Hugo", "César", "Javier",
    ]
    first_names_f = [
        "María", "Ana", "Lucía", "Andrea", "Camila", "Valeria", "Paula", "Daniela", "Mariana", "Claudia",
        "Paola", "Gabriela", "Sofía", "Fiorella", "Carmen", "Rosa", "Patricia", "Diana", "Brenda", "Natalia",
        "Romina", "Alejandra", "Jimena", "Ximena", "Cecilia", "Milagros", "Adriana", "Fernanda", "Vanessa", "Carolina",
    ]
    surnames = [
        "Quispe", "Flores", "Rodríguez", "Sánchez", "García", "Rojas", "Díaz", "Torres", "Chávez", "Mendoza",
        "Ramos", "Castillo", "Morales", "Vásquez", "Castro", "Navarrete", "Gutiérrez", "Gil", "Navarro", "Ponce",
        "Quintana", "Delgado", "Ruiz", "Benavides", "Silva", "Aguirre", "Salazar", "Paredes", "Luna", "Gómez",
        "Vargas", "Benítez", "Guerrero", "Santillán", "Cueva", "Orellana", "Hurtado", "Vidal", "Valdivia", "Huamán",
        "Mamani", "Condori", "Tello", "Villanueva", "Medina", "Cabrera", "Herrera", "Cáceres", "Peña", "Alarcón",
    ]
    email_domains = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com"]
    all_first_names = first_names_m + first_names_f
    used_documents = set()

    clients = [(1, "00000000", "Clientes", "Varios", None, None, 1, False, 0, "2023-01-01 08:00:00")]
    used_documents.add((1, "00000000"))

    start_reg = datetime(2023, 1, 1)
    end_reg = datetime(2026, 6, 30)
    delta_days = (end_reg - start_reg).days

    for _ in range(count):
        fn = random.choice(all_first_names)
        sn1 = random.choice(surnames)
        sn2 = random.choice(surnames)
        apellidos = f"{sn1} {sn2}"

        doc_rand = random.random()
        if doc_rand < 0.82:
            tipo_doc = 1  # DNI
            doc_num = str(random.randint(10000000, 79999999))
        elif doc_rand < 0.92:
            tipo_doc = 3  # RUC
            doc_num = f"10{random.randint(10000000, 79999999)}{random.randint(0, 9)}"
        elif doc_rand < 0.97:
            tipo_doc = 2  # Carnet Extranjería
            doc_num = f"00{random.randint(1000000, 9999999)}"
        else:
            tipo_doc = 4  # Pasaporte
            doc_num = f"PE{random.randint(100000, 999999)}"

        while (tipo_doc, doc_num) in used_documents:
            doc_num = str(random.randint(10000000, 79999999))
        used_documents.add((tipo_doc, doc_num))

        tipo_cli_rand = random.random()
        if tipo_cli_rand < 0.60:
            id_tipo_cliente = 1
            es_titular_tarjeta = random.random() < 0.08
        elif tipo_cli_rand < 0.95:
            id_tipo_cliente = 2
            es_titular_tarjeta = True
        else:
            id_tipo_cliente = 3
            es_titular_tarjeta = True

        puntos = random.randint(300, 16000) if es_titular_tarjeta else (random.randint(0, 400) if random.random() < 0.20 else 0)
        domain = random.choice(email_domains)
        email = f"{fn.lower()}.{sn1.lower()}{random.randint(1, 999)}@{domain}"
        telefono = f"9{random.randint(10000000, 99999999)}"
        reg_dt = start_reg + timedelta(days=random.randint(0, delta_days), seconds=random.randint(0, 86399))

        clients.append((
            tipo_doc, doc_num, fn, apellidos, email, telefono,
            id_tipo_cliente, es_titular_tarjeta, puntos, reg_dt.strftime("%Y-%m-%d %H:%M:%S")
        ))

    return clients


def generate_products_dataset(target_count=TARGET_PRODUCTS):
    """
    Genera 5,000 productos realistas cubriendo los 6 departamentos comerciales de Ripley.
    Asigna precios coherentes, márgenes mayoristas, marcas auténticas y reglas de despacho.
    """
    # Mapeo de marcas
    brand_names = {b[0]: b[1] for b in BASE_MARCAS}

    # Definición de plantillas por subcategoría:
    # (id_subcat, [marcas], [proveedores], plantilla_nombre, precio_min, precio_max, requiere_despacho)
    templates = [
        # Moda Mujer
        (1, [1, 3, 5, 7], [2, 21], "Jean {brand} {fit} Denim {color}", 89.90, 199.90, False),
        (2, [1, 3, 5, 7], [2, 21], "Blusa {brand} {style} Manga {sleeve} {color}", 49.90, 129.90, False),
        (3, [1, 3, 7, 8], [2, 21], "Casaca {brand} {jacket} Acolchada {color}", 149.90, 329.90, False),
        (4, [1, 3, 5, 7], [2, 21], "Vestido {brand} {dress_type} {pattern} {color}", 99.90, 249.90, False),
        # Moda Hombre
        (5, [2, 4, 8, 9, 10], [2, 21], "Jean {brand} Regular Fit Denim {color}", 89.90, 189.90, False),
        (6, [2, 4, 8, 9, 10], [2, 21], "Polo {brand} Algodón Pima Cuello {neck} {color}", 39.90, 89.90, False),
        (7, [2, 4, 8, 9, 10], [2, 21], "Casaca {brand} Bomber Urbana {color}", 139.90, 299.90, False),
        # Calzado Urbano y Formal
        (8, [23, 24, 25, 27, 28, 29], [3, 9, 10], "Zapatillas {brand} Urbanas {model} {color}", 179.90, 429.90, False),
        (9, [1, 2, 5], [2], "Zapatos {brand} Formales de Cuero {color}", 149.90, 289.90, False),
        # Televisores y Audio
        (10, [11, 13, 14, 15], [1, 7, 8, 24], "Smart TV {brand} {tv_size} 4K UHD {display_tech}", 1199.00, 5499.00, True),
        (11, [11, 13, 14], [1, 7, 8], "Barra de Sonido {brand} Dolby Atmos {watts}W", 499.00, 1899.00, False),
        # Smartphones y Wearables
        (12, [11, 12, 15], [1, 4, 24], "Smartphone {brand} {phone_line} {storage}GB {color}", 899.00, 5299.00, False),
        (13, [11, 12, 15], [1, 4, 24], "Smartwatch {brand} {watch_line} GPS {dial_size}mm", 499.00, 1999.00, False),
        # Cómputo y Laptops
        (14, [16, 17, 18, 12], [4, 13, 14], "Laptop {brand} {lap_line} 15.6 Core i{core} {ram}GB RAM", 1799.00, 5499.00, False),
        (15, [11, 13, 16], [1, 8, 13], "Monitor Gamer {brand} {mon_size} Full HD 144Hz", 599.00, 1599.00, False),
        # Electrohogar / Línea Blanca
        (16, [11, 13, 20, 21, 22, 23], [1, 8, 11, 23], "Refrigeradora {brand} No Frost {liters}L Inverter", 1499.00, 4599.00, True),
        (17, [11, 13, 20, 22, 23], [1, 8, 11, 23], "Lavadora Automática {brand} {kg}Kg Carga Frontal", 1199.00, 3299.00, True),
        (18, [19, 20, 23], [11, 12, 23], "Cocina {brand} 4 Hornillas Encendido Eléctrico {color}", 799.00, 2199.00, True),
        # Dormitorio y Colchones
        (19, [30, 31, 32, 33], [5, 6, 22], "Colchón {brand} Ortopédico Ergo {bed_size}", 799.00, 2699.00, True),
        (20, [1, 2, 6], [2], "Juego de Sábanas {brand} 300 Hilos {bed_size}", 99.90, 229.90, False),
        (21, [6, 30, 31], [5, 6], "Almohada {brand} Memory Foam Cervical Antialérgica", 59.90, 149.90, False),
        # Muebles de Sala y Comedor
        (22, [6], [2], "Sofá Seccional {brand} Tela Lino {seats} Cuerpos {color}", 1299.00, 3599.00, True),
        (23, [6], [2], "Juego de Comedor {brand} 6 Sillas Madera Paraíso", 1499.00, 3199.00, True),
        # Menaje y Cocina
        (24, [19, 20], [11, 12], "Batería de Cocina {brand} Antiadherente {pieces} Piezas", 189.90, 499.90, False),
        (25, [6], [2], "Juego de Vajilla {brand} Cerámica {pieces_v} Piezas", 119.90, 299.90, False),
        # Perfumería y Cuidado Personal
        (26, [34, 35, 36, 38], [15, 16], "Perfume {brand} {perf_f} Eau de Parfum {ml}ml", 199.90, 589.90, False),
        (27, [34, 35, 36], [15, 16], "Perfume {brand} {perf_m} Eau de Toilette {ml}ml", 189.90, 549.90, False),
        (28, [37, 38], [15], "Crema Facial {brand} Tratamiento Antiedad Revitalift", 79.90, 249.90, False),
        # Deportes y Fitness
        (29, [23, 24, 25, 26], [3, 9, 10], "Zapatillas {brand} Running {run_model} Pro", 229.90, 549.90, False),
        (30, [23, 24, 25, 26], [3, 9, 10], "Polo Deportivo {brand} Dri-FIT Transpirable {color}", 69.90, 149.90, False),
        (31, [42, 43], [20], "Trotadora Eléctrica {brand} Motor {hp}HP Inclinación Digital", 1699.00, 4299.00, True),
        (32, [42, 43], [20], "Set Mancuernas Ajustables {brand} {kg_m}Kg con Soporte", 149.90, 499.90, False),
        # Infantil y Juguetería
        (33, [39, 40, 41], [17, 18, 19], "Figura de Acción {brand} {toy_line} Articulada", 49.90, 189.90, False),
        (34, [39, 40], [17, 18], "Set de Construcción {brand} Edición Coleccionista", 89.90, 429.90, False),
        (35, [1, 7, 44], [2, 25], "Pack 3 Bodys Algodón Orgánico {brand} Bebé {color}", 49.90, 99.90, False),
        (36, [44], [25], "Coche Travel System {brand} Reclinable con Silla Auto", 699.00, 1899.00, True),
    ]

    fits = ["Skinny", "Slim", "Regular", "Flare", "Oversize", "Straight"]
    colors = ["Azul", "Negro", "Blanco", "Gris", "Beige", "Verde Militar", "Rojo", "Azul Marino", "Celeste", "Marrón", "Palo Rosa"]
    styles = ["Satinada", "Casual", "Elegante", "Estampada", "Básica"]
    sleeves = ["Larga", "Corta", "3/4"]
    jackets = ["Bomber", "Parka", "Cortaviento", "Denim", "Puffer"]
    dress_types = ["Corto", "Midi", "Largo de Fiesta", "Camisero"]
    patterns = ["Floral", "Liso", "Rayas", "Animal Print"]
    necks = ["Redondo", "V", "Polo"]
    models_urb = ["Air Max", "Superstar", "Smash", "Classic Leather", "Old Skool", "Chuck 70", "D'Lites"]
    run_models = ["Pegasus", "Ultraboost", "Nitro", "Ghost", "Floatride", "Gel-Nimbus"]
    tv_sizes = ["50\"", "55\"", "65\"", "75\"", "85\""]
    disp_techs = ["Neo QLED", "Crystal UHD", "NanoCell", "OLED Evo", "Triluminos"]
    watts = [240, 320, 450, 600]
    phone_lines = ["Galaxy S24", "Galaxy A55", "iPhone 15", "iPhone 13", "Redmi Note 13", "Xiaomi 14 Ultra"]
    watch_lines = ["Watch Series 9", "Galaxy Watch 6", "Redmi Watch 4", "Band 8 Pro"]
    lap_lines = ["Pavilion", "IdeaPad", "ZenBook", "MacBook Air", "TUF Gaming", "ThinkPad"]
    bed_sizes = ["1.5 Plazas", "2 Plazas", "Queen Size", "King Size"]
    perf_f = ["Good Girl", "La Vie Est Belle", "J'adore", "Black Opium", "212 VIP Rose"]
    perf_m = ["Sauvage", "1 Million", "Invictus", "Acqua Di Gio", "212 Men Heroes"]

    products = []
    used_skus = set()
    used_barcodes = set()

    for i in range(1, target_count + 1):
        tmpl = random.choice(templates)
        subcat_id = tmpl[0]
        brand_id = random.choice(tmpl[1])
        brand_name = brand_names[brand_id]
        prov_id = random.choice(tmpl[2])

        sku = f"SKU-{brand_name[:3].upper()}-{subcat_id:02d}-{i:05d}"
        barcode = f"775{i:08d}"

        price = round(random.uniform(tmpl[4], tmpl[5]), 2)
        # Margen comercial estándar: costo 42% a 60% del precio de venta
        cost = round(price * random.uniform(0.42, 0.60), 2)
        requiere_despacho = tmpl[6]

        name = tmpl[3].format(
            brand=brand_name,
            fit=random.choice(fits),
            color=random.choice(colors),
            style=random.choice(styles),
            sleeve=random.choice(sleeves),
            jacket=random.choice(jackets),
            dress_type=random.choice(dress_types),
            pattern=random.choice(patterns),
            neck=random.choice(necks),
            model=random.choice(models_urb),
            tv_size=random.choice(tv_sizes),
            display_tech=random.choice(disp_techs),
            watts=random.choice(watts),
            phone_line=random.choice(phone_lines),
            storage=random.choice([128, 256, 512]),
            watch_line=random.choice(watch_lines),
            dial_size=random.choice([40, 44, 45, 49]),
            lap_line=random.choice(lap_lines),
            core=random.choice([5, 7, 9]),
            ram=random.choice([8, 16, 32]),
            mon_size=random.choice(["24\"", "27\"", "32\""]),
            liters=random.choice([250, 380, 450, 520]),
            kg=random.choice([10, 13, 16, 19]),
            bed_size=random.choice(bed_sizes),
            seats=random.choice([2, 3, 4]),
            pieces=random.choice([5, 7, 10]),
            pieces_v=random.choice([16, 20, 30]),
            perf_f=random.choice(perf_f),
            perf_m=random.choice(perf_m),
            ml=random.choice([50, 80, 100]),
            run_model=random.choice(run_models),
            hp=random.choice(["2.0", "2.5", "3.0"]),
            kg_m=random.choice([15, 20, 30]),
            toy_line=random.choice(["Marvel Avengers", "Star Wars", "Barbie Fashion", "Transformers"]),
        )

        products.append((
            i, sku, barcode, name, subcat_id, brand_id, prov_id, price, cost, requiere_despacho, "Activo"
        ))

    return products


def setup_masters(conn):
    """Puebla de forma completa y autosuficiente todos los catálogos maestros y el inventario."""
    print("📋 Verificando y sincronizando catálogos maestros...")
    with conn.cursor() as cur:
        cur.execute("SET NAMES utf8mb4;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

        # Estructura Geográfica, Tiendas y Cajas
        cur.executemany("INSERT IGNORE INTO `UBIGEO` (`id_ubigeo`, `departamento`, `provincia`, `distrito`) VALUES (%s, %s, %s, %s)", BASE_UBIGEOS)
        cur.executemany("INSERT IGNORE INTO `TIENDA` (`id_tienda`, `codigo_tienda`, `nombre`, `direccion`, `id_ubigeo`, `superficie_m2`, `aforo_maximo`, `estado`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", BASE_TIENDAS)
        cur.executemany("INSERT IGNORE INTO `TURNO_TRABAJO` (`id_turno`, `nombre_turno`, `hora_inicio`, `hora_fin`) VALUES (%s, %s, %s, %s)", BASE_TURNOS)
        cur.executemany("INSERT IGNORE INTO `ROL_EMPLEADO` (`id_rol`, `nombre_rol`) VALUES (%s, %s)", BASE_ROLES)
        cur.executemany("INSERT IGNORE INTO `CAJA_POS` (`id_tienda`, `numero_caja`, `tipo_caja`, `piso_ubicacion`, `mac_address`) VALUES (%s, %s, %s, %s, %s)", ALL_CAJAS)

        # Jerarquía Comercial: Líneas, Categorías, Subcategorías, Marcas y Proveedores
        cur.execute("TRUNCATE TABLE `SUBCATEGORIA`;")
        cur.execute("TRUNCATE TABLE `CATEGORIA`;")
        cur.execute("TRUNCATE TABLE `LINEA_COMERCIAL`;")
        cur.execute("TRUNCATE TABLE `MARCA`;")
        cur.execute("TRUNCATE TABLE `PROVEEDOR`;")

        cur.executemany("INSERT INTO `PROVEEDOR` (`id_proveedor`, `ruc`, `razon_social`, `contacto_comercial`, `telefono`, `email`, `condicion_pago`, `estado`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", BASE_PROVEEDORES)
        cur.executemany("INSERT INTO `LINEA_COMERCIAL` (`id_linea`, `codigo_linea`, `nombre_linea`) VALUES (%s, %s, %s)", BASE_LINEAS)
        cur.executemany("INSERT INTO `CATEGORIA` (`id_categoria`, `id_linea`, `nombre_categoria`) VALUES (%s, %s, %s)", BASE_CATEGORIAS)
        cur.executemany("INSERT INTO `SUBCATEGORIA` (`id_subcategoria`, `id_categoria`, `nombre_subcategoria`) VALUES (%s, %s, %s)", BASE_SUBCATEGORIAS)
        cur.executemany("INSERT INTO `MARCA` (`id_marca`, `nombre_marca`, `es_marca_propia`) VALUES (%s, %s, %s)", BASE_MARCAS)

        # Catálogo Ampliado de Productos (~5,000 SKUs)
        cur.execute("SELECT COUNT(*) FROM `PRODUCTO`;")
        current_prod_count = cur.fetchone()[0]

        if current_prod_count < TARGET_PRODUCTS:
            print(f"  → Generando catálogo masivo de {TARGET_PRODUCTS:,} productos...")
            products_data = generate_products_dataset(TARGET_PRODUCTS)
            cur.execute("TRUNCATE TABLE `PRODUCTO`;")

            insert_prod_sql = """
                INSERT INTO `PRODUCTO`
                (`id_producto`, `sku`, `codigo_barras`, `nombre_producto`, `id_subcategoria`, `id_marca`,
                 `id_proveedor`, `precio_lista`, `costo_estandar`, `requiere_despacho`, `estado`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for i in range(0, len(products_data), 1000):
                cur.executemany(insert_prod_sql, products_data[i:i + 1000])
            print(f"  ✓ {len(products_data):,} productos cargados exitosamente.")
        else:
            print(f"  ✓ Catálogo de productos ya cuenta con {current_prod_count:,} registros.")

        # Tablas de Apoyo de Clientes, Documentos y Medios de Pago
        cur.executemany("INSERT IGNORE INTO `TIPO_DOCUMENTO` (`id_tipo_doc`, `codigo_sunat`, `descripcion`) VALUES (%s, %s, %s)", BASE_TIPOS_DOC)
        cur.executemany("INSERT IGNORE INTO `TIPO_CLIENTE` (`id_tipo_cliente`, `nombre_tipo`) VALUES (%s, %s)", BASE_TIPOS_CLIENTE)
        cur.executemany("INSERT IGNORE INTO `METODO_PAGO` (`id_metodo_pago`, `codigo_metodo`, `descripcion`, `aplica_comision`) VALUES (%s, %s, %s, %s)", BASE_METODOS_PAGO)

        # Empleados y Sensores IoT
        cur.executemany(
            """
            INSERT IGNORE INTO `EMPLEADO`
            (`dni`, `nombres`, `apellidos`, `id_rol`, `id_tienda_base`, `fecha_ingreso`)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            EXPANDED_EMPLOYEES,
        )
        cur.executemany("INSERT IGNORE INTO `ZONA_TIENDA` (`id_tienda`, `nombre_zona`, `tipo_zona`, `aforo_limite`) VALUES (%s, %s, %s, %s)", ALL_ZONAS)
        cur.executemany("INSERT IGNORE INTO `DISPOSITIVO_SENSOR` (`id_zona`, `codigo_sensor`, `tipo_sensor`, `ip_dispositivo`) VALUES (%s, %s, %s, %s)", ALL_SENSORES)

        # Generación del Padrón de Clientes
        cur.execute("SELECT COUNT(*) FROM `CLIENTE`;")
        current_client_count = cur.fetchone()[0]

        if current_client_count < NUM_CLIENTES:
            print(f"  → Generando padrón ampliado de {NUM_CLIENTES:,} clientes...")
            clients_data = generate_clients_dataset(NUM_CLIENTES)
            cur.execute("TRUNCATE TABLE `CLIENTE`;")

            insert_client_sql = """
                INSERT INTO `CLIENTE`
                (`id_tipo_doc`, `numero_documento`, `nombres`, `apellidos`, `email`, `telefono`,
                 `id_tipo_cliente`, `es_titular_tarjeta_ripley`, `puntos_ripley_acumulados`, `fecha_registro`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for i in range(0, len(clients_data), 2000):
                cur.executemany(insert_client_sql, clients_data[i:i + 2000])
            print(f"  ✓ {len(clients_data):,} clientes registrados exitosamente.")

        # Sincronización de Inventarios en Tienda (3 sedes x 5,000 SKUs = 15,000 registros)
        print("  → Sincronizando existencias de almacén e inventarios por tienda...")
        cur.execute("TRUNCATE TABLE `INVENTARIO_TIENDA`;")
        cur.execute("SELECT id_tienda FROM `TIENDA`;")
        tiendas = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id_producto FROM `PRODUCTO`;")
        productos = [r[0] for r in cur.fetchall()]

        inventarios = []
        for t_id in tiendas:
            for p_id in productos:
                stock_piso = random.randint(15, 60)
                stock_alm = random.randint(30, 200)
                reorden = random.randint(10, 25)
                inventarios.append((t_id, p_id, stock_piso, stock_alm, 0, reorden))

        insert_inv_sql = """
            INSERT INTO `INVENTARIO_TIENDA`
            (`id_tienda`, `id_producto`, `stock_piso_venta`, `stock_almacen`, `stock_comprometido`, `punto_reorden`)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        for i in range(0, len(inventarios), 3000):
            cur.executemany(insert_inv_sql, inventarios[i:i + 3000])

        print(f"  ✓ {len(inventarios):,} registros de inventario inicializados.")

        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

    conn.commit()
    print("  ✓ Todos los maestros, catálogos e inventarios están listos.")


def generate_transactions(conn):
    """
    Genera las transacciones comerciales a gran escala (~50,000 comprobantes).
    Aplica distribución de Pareto en productos y clientes, horas pico, cálculo SUNAT y lotes masivos.
    """
    print(f"\n🛒 Generando transacciones comerciales (objetivo: ~{TARGET_TICKETS:,} comprobantes)...")

    with conn.cursor() as cur:
        cur.execute("SELECT id_producto, precio_lista, costo_estandar FROM PRODUCTO WHERE estado='Activo' ORDER BY id_producto;")
        products = cur.fetchall()

        cur.execute("SELECT id_cliente, es_titular_tarjeta_ripley FROM CLIENTE ORDER BY id_cliente;")
        client_rows = cur.fetchall()

        cur.execute("SELECT id_caja, id_tienda FROM CAJA_POS WHERE estado='Operativa';")
        cajas = cur.fetchall()

        cur.execute("SELECT id_empleado, id_tienda_base FROM EMPLEADO WHERE estado='Activo';")
        empleados = cur.fetchall()

    cajas_by_tienda = {}
    for c_id, t_id in cajas:
        cajas_by_tienda.setdefault(t_id, []).append(c_id)

    emp_by_tienda = {}
    for e_id, t_id in empleados:
        emp_by_tienda.setdefault(t_id, []).append(e_id)

    # 1. Ponderación Pareto de Productos (Top sellers vs. Long-tail)
    # Top 10% (500 productos) concentra ~60% de unidades vendidas
    # Siguiente 25% (1,250 productos) concentra ~25%
    # 65% restante (3,250 productos) representa compras ocasionales (~15%)
    prod_weights = []
    for idx in range(len(products)):
        if idx < 500:
            prod_weights.append(random.randint(30, 65))
        elif idx < 1750:
            prod_weights.append(random.randint(7, 18))
        else:
            prod_weights.append(random.randint(1, 3))

    # Pre-muestreo vectorizado de productos para máxima velocidad
    total_items_to_sample = int(TARGET_TICKETS * 2.15) + 5000
    sampled_product_pool = random.choices(products, weights=prod_weights, k=total_items_to_sample)
    prod_pool_pointer = 0

    # 2. Ponderación Pareto de Clientes
    client_ids = [r[0] for r in client_rows]
    client_titular_map = {r[0]: bool(r[1]) for r in client_rows}

    client_weights = []
    for c_id in client_ids:
        if c_id == 1:
            client_weights.append(7200)  # ~14.5% Clientes Varios
        elif client_titular_map[c_id]:
            client_weights.append(random.randint(6, 16))
        else:
            client_weights.append(random.randint(1, 4))

    precomputed_clients = random.choices(client_ids, weights=client_weights, k=TARGET_TICKETS + 2000)
    client_idx_pointer = 0

    # Limpiar tablas transaccionales
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("TRUNCATE TABLE `DETALLE_COMPROBANTE`;")
        cur.execute("TRUNCATE TABLE `PAGO_COMPROBANTE`;")
        cur.execute("TRUNCATE TABLE `COMPROBANTE_PAGO`;")
        cur.execute("TRUNCATE TABLE `ASIGNACION_CAJA`;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()

    # 3. Generar Asignaciones de Caja por día y turno
    print("  → Creando sesiones de apertura y cierre de caja (ASIGNACION_CAJA)...")
    curr_date = START_DATE
    asignaciones = []

    turnos_def = [
        (1, "10:00:00", "14:00:00"),
        (2, "14:00:00", "18:30:00"),
        (3, "18:30:00", "22:00:00"),
    ]

    while curr_date <= END_DATE:
        for t_id in [1, 2, 3]:
            store_cajas = cajas_by_tienda.get(t_id, [])
            store_emps = emp_by_tienda.get(t_id, [])
            if not store_cajas or not store_emps:
                continue

            for caja_id in store_cajas:
                for turno_id, h_ini, h_fin in turnos_def:
                    emp_id = random.choice(store_emps)
                    apertura = datetime.combine(curr_date.date(), datetime.strptime(h_ini, "%H:%M:%S").time())
                    cierre = datetime.combine(curr_date.date(), datetime.strptime(h_fin, "%H:%M:%S").time())
                    asignaciones.append((caja_id, emp_id, turno_id, curr_date.date(), apertura, cierre, 300.0, 4800.0))

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

    # Mapeo indexado de asignaciones
    with conn.cursor() as cur:
        cur.execute("SELECT id_asignacion, id_caja, id_empleado, fecha_operacion, hora_apertura, hora_cierre FROM ASIGNACION_CAJA;")
        asig_rows = cur.fetchall()

    asig_map = {}
    for asig_id, c_id, e_id, f_op, h_ap, h_ci in asig_rows:
        asig_map.setdefault((c_id, f_op), []).append((asig_id, e_id, h_ap, h_ci))

    print(f"  ✓ {len(asignaciones):,} sesiones de caja generadas.")

    # 4. Planificación de Tickets Diarios
    base_daily_tickets = int(TARGET_TICKETS / (44 * 0.95 + 18 * 1.45))

    correlativos = {
        ("Boleta de Venta", "B001"): 100000,
        ("Boleta de Venta", "B002"): 100000,
        ("Boleta de Venta", "B003"): 100000,
        ("Factura", "F001"): 100000,
        ("Factura", "F002"): 100000,
        ("Factura", "F003"): 100000,
    }

    comprobantes_chunk = []
    detalles_chunk = []
    pagos_chunk = []

    comp_id_virtual = 1
    total_detalles_count = 0
    anomalias_anulados = 0
    anomalias_outliers_tiempo = 0

    chunk_counter = 1
    total_chunks_expected = TARGET_TICKETS // CHUNK_SIZE

    print("  → Generando tickets y detalles en lotes masivos...")

    curr_date = START_DATE
    while curr_date <= END_DATE:
        is_weekend = curr_date.weekday() >= 5
        daily_tickets_count = int(base_daily_tickets * (1.45 if is_weekend else 0.95))

        for _ in range(daily_tickets_count):
            available_tiendas = [t for t in [1, 2, 3] if t in cajas_by_tienda and cajas_by_tienda[t]]
            tienda_id = random.choices(available_tiendas, weights=[50, 30, 20])[0]
            caja_id = random.choice(cajas_by_tienda[tienda_id])

            rand_val = random.random()
            if rand_val < 0.65:
                hora = random.randint(18, 20)
                minuto = random.randint(0, 59)
                segundo = random.randint(0, 59)
                tiempo_atencion = random.randint(110, 320)
            elif rand_val < 0.85:
                hora = random.randint(13, 15)
                minuto = random.randint(0, 59)
                segundo = random.randint(0, 59)
                tiempo_atencion = random.randint(80, 200)
            else:
                hora = random.choice([10, 11, 12, 21])
                minuto = random.randint(0, 59)
                segundo = random.randint(0, 59)
                tiempo_atencion = random.randint(60, 150)

            fecha_hora_emision = datetime(curr_date.year, curr_date.month, curr_date.day, hora, minuto, segundo)
            fecha_hora_inicio = fecha_hora_emision - timedelta(seconds=tiempo_atencion)

            sessions = asig_map.get((caja_id, curr_date.date()), [])
            asig_id, emp_id = 1, 1
            if sessions:
                for s_asig, s_emp, s_ini, s_fin in sessions:
                    if s_ini <= fecha_hora_emision <= s_fin:
                        asig_id, emp_id = s_asig, s_emp
                        break
                else:
                    asig_id, emp_id, _, _ = sessions[0]

            # Inyección de Anomalías ETL
            if random.random() < 0.012:
                anomalias_outliers_tiempo += 1
                tiempo_atencion = random.choice([0, 3600, 4200])

            if random.random() < 0.045:
                estado = random.choice(["Anulado", "Devuelto"])
                anomalias_anulados += 1
            else:
                estado = "Emitido"

            cliente_id = precomputed_clients[client_idx_pointer]
            client_idx_pointer += 1
            es_titular = client_titular_map.get(cliente_id, False)

            tipo_comp = "Factura" if random.random() < 0.15 else "Boleta de Venta"
            serie = f"B00{tienda_id}" if tipo_comp == "Boleta de Venta" else f"F00{tienda_id}"
            correlativos[(tipo_comp, serie)] += 1
            num_correlativo = correlativos[(tipo_comp, serie)]

            # Canasta de compra (1 a 5 ítems por ticket)
            num_items = random.choices([1, 2, 3, 4, 5], weights=[35, 35, 18, 8, 4])[0]
            ticket_subtotal = 0.0
            ticket_descuento = 0.0
            ticket_detalles = []

            # Obtener ítems del pool muestreado con Pareto
            ticket_prods = []
            seen_pids = set()
            while len(ticket_prods) < num_items:
                candidate = sampled_product_pool[prod_pool_pointer]
                prod_pool_pointer = (prod_pool_pointer + 1) % len(sampled_product_pool)
                if candidate[0] not in seen_pids:
                    seen_pids.add(candidate[0])
                    ticket_prods.append(candidate)

            for prod_id, p_lista, c_costo in ticket_prods:
                cant = random.choices([1, 2, 3], weights=[80, 15, 5])[0]

                if es_titular and random.random() < 0.35:
                    desc_unit = float(p_lista) * random.choice([0.15, 0.20, 0.25])
                elif random.random() < 0.10:
                    desc_unit = float(p_lista) * 0.10
                else:
                    desc_unit = 0.0

                p_venta = float(p_lista) - desc_unit
                subtotal_linea = round(p_venta * cant, 2)
                ticket_subtotal += subtotal_linea
                ticket_descuento += round(desc_unit * cant, 2)

                ticket_detalles.append((
                    comp_id_virtual, prod_id, cant, round(p_venta, 2),
                    float(c_costo), round(desc_unit, 2), subtotal_linea
                ))

            monto_total = round(ticket_subtotal, 2)
            subtotal_gravado = round(monto_total / 1.18, 2)
            igv = round(monto_total - subtotal_gravado, 2)

            comprobantes_chunk.append((
                comp_id_virtual, tienda_id, caja_id, emp_id, cliente_id, asig_id,
                tipo_comp, serie, num_correlativo,
                fecha_hora_inicio, fecha_hora_emision, tiempo_atencion,
                subtotal_gravado, igv, ticket_descuento, monto_total, estado
            ))

            detalles_chunk.extend(ticket_detalles)

            if es_titular and random.random() < 0.70:
                metodo_pago = 1  # Tarjeta Ripley
            else:
                metodo_pago = random.choices([2, 3, 4, 5], weights=[35, 30, 15, 20])[0]

            pagos_chunk.append((
                comp_id_virtual, metodo_pago, monto_total,
                f"AUTH-{random.randint(100000, 999999)}", fecha_hora_emision
            ))

            comp_id_virtual += 1

            if len(comprobantes_chunk) >= CHUNK_SIZE:
                _insert_chunk(conn, comprobantes_chunk, detalles_chunk, pagos_chunk)
                total_detalles_count += len(detalles_chunk)
                pct = int((chunk_counter / total_chunks_expected) * 100)
                print(f"    [Bloque {chunk_counter:>2}/{total_chunks_expected}] {comp_id_virtual - 1:,} comprobantes insertados ({pct}%)...")
                comprobantes_chunk = []
                detalles_chunk = []
                pagos_chunk = []
                chunk_counter += 1

        curr_date += timedelta(days=1)

    if comprobantes_chunk:
        _insert_chunk(conn, comprobantes_chunk, detalles_chunk, pagos_chunk)
        total_detalles_count += len(detalles_chunk)

    total_tickets_inserted = comp_id_virtual - 1
    print(f"  ✓ {total_tickets_inserted:,} comprobantes y {total_detalles_count:,} detalles insertados.")
    print(f"    - Anomalías controladas: {anomalias_anulados:,} anulados/devueltos, {anomalias_outliers_tiempo:,} outliers de tiempo.")


def _insert_chunk(conn, comprobantes, detalles, pagos):
    """Inserta un bloque transaccional con alto desempeño utilizando executemany."""
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO `COMPROBANTE_PAGO`
            (`id_comprobante`, `id_tienda`, `id_caja`, `id_empleado`, `id_cliente`, `id_asignacion`,
             `tipo_comprobante`, `serie`, `numero_correlativo`, `fecha_hora_inicio_atencion`,
             `fecha_hora_emision`, `tiempo_atencion_segundos`, `subtotal_gravado`, `igv`,
             `total_descuento`, `monto_total`, `estado`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            comprobantes,
        )

        cur.executemany(
            """
            INSERT INTO `DETALLE_COMPROBANTE`
            (`id_comprobante`, `id_producto`, `cantidad`, `precio_unitario_venta`,
             `costo_unitario_historico`, `descuento_unitario`, `subtotal_linea`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            detalles,
        )

        cur.executemany(
            """
            INSERT INTO `PAGO_COMPROBANTE`
            (`id_comprobante`, `id_metodo_pago`, `monto_pagado`, `numero_operacion_pos`, `fecha_hora_pago`)
            VALUES (%s, %s, %s, %s, %s)
            """,
            pagos,
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
        base_mult = 1.45 if is_weekend else 1.0

        for sens_id, _ in sensors:
            for h in range(10, 22):
                for m in [0, 30]:
                    dt = datetime(curr_date.year, curr_date.month, curr_date.day, h, m, 0)

                    if 18 <= h <= 20:
                        entradas = int(random.randint(220, 380) * base_mult)
                        salidas = int(random.randint(90, 180) * base_mult)
                        aforo = int(random.randint(1800, 3200) * base_mult)
                    elif 13 <= h <= 15:
                        entradas = int(random.randint(110, 190) * base_mult)
                        salidas = int(random.randint(95, 160) * base_mult)
                        aforo = int(random.randint(950, 1800) * base_mult)
                    else:
                        entradas = int(random.randint(40, 95) * base_mult)
                        salidas = int(random.randint(35, 90) * base_mult)
                        aforo = int(random.randint(400, 950) * base_mult)

                    iot_batch.append((sens_id, dt, entradas, salidas, aforo))

        curr_date += timedelta(days=1)

    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("TRUNCATE TABLE `LOG_AFLUENCIA_IOT`;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

        for i in range(0, len(iot_batch), 2000):
            chunk = iot_batch[i:i + 2000]
            cur.executemany(
                """
                INSERT INTO `LOG_AFLUENCIA_IOT`
                (`id_dispositivo`, `fecha_hora_lectura`, `conteo_entradas`, `conteo_salidas`, `aforo_instantaneo_calculado`)
                VALUES (%s, %s, %s, %s, %s)
                """,
                chunk,
            )

    conn.commit()
    print(f"  ✓ {len(iot_batch):,} lecturas de telemetría IoT insertadas exitosamente.")


def main():
    print("=" * 70)
    print("🚀 GENERADOR MASIVO DE DATOS OLTP - RIPLEY BUSINESS INTELLIGENCE")
    print(f"🎯 Meta Comprobantes: ~{TARGET_TICKETS:,} tickets")
    print(f"📦 Catálogo de Productos: ~{TARGET_PRODUCTS:,} SKUs")
    print(f"👥 Padrón de Clientes: ~{NUM_CLIENTES:,} registros")
    print(f"📅 Rango de Fechas: {START_DATE.strftime('%Y-%m-%d')} a {END_DATE.strftime('%Y-%m-%d')} (62 días)")
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
            cur.execute("SELECT COUNT(*) FROM `LINEA_COMERCIAL`;")
            total_lineas = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `CATEGORIA`;")
            total_categorias = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `SUBCATEGORIA`;")
            total_subcategorias = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `MARCA`;")
            total_marcas = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `PROVEEDOR`;")
            total_proveedores = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `PRODUCTO`;")
            total_productos = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `INVENTARIO_TIENDA`;")
            total_inventario = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `CLIENTE`;")
            total_clientes = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `COMPROBANTE_PAGO`;")
            total_tickets = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `DETALLE_COMPROBANTE`;")
            total_detalles = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM `LOG_AFLUENCIA_IOT`;")
            total_iot = cur.fetchone()[0]

        print("\n" + "=" * 70)
        print("🎉 GENERACIÓN Y CARGA MASIVA COMPLETADA CON ÉXITO")
        print(f"  🏢 Líneas Comerciales:              {total_lineas}")
        print(f"  📂 Categorías de Producto:          {total_categorias}")
        print(f"  🏷️  Subcategorías:                   {total_subcategorias}")
        print(f"  🏷️  Marcas (Propias y Externas):     {total_marcas}")
        print(f"  🏭 Proveedores Homologados:         {total_proveedores}")
        print(f"  📦 Catálogo Total PRODUCTO:         {total_productos:,}")
        print(f"  🏬 Registros INVENTARIO_TIENDA:     {total_inventario:,}")
        print(f"  👥 Total CLIENTE:                   {total_clientes:,}")
        print(f"  🧾 Total COMPROBANTE_PAGO:          {total_tickets:,}")
        print(f"  🛒 Total DETALLE_COMPROBANTE:       {total_detalles:,}")
        print(f"  📡 Total LOG_AFLUENCIA_IOT:         {total_iot:,}")
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

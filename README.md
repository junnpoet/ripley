# Proyecto de Inteligencia de Negocios - Ripley

Modelo analítico y operacional para el análisis y optimización de la gestión de ventas y afluencia en horas pico de la empresa comercial **Ripley**.

El repositorio integra tanto la **base de datos operacional (OLTP)** en 3NF como el **Data Warehouse analítico (DW)** bajo el modelo de Constelación de Hechos (Fact Constellation) de Ralph Kimball, ambos orquestados en un contenedor Docker con MySQL 8.0.

---

## 1. Estructura del Repositorio

```
.
├── Makefile                     # Automatización unificada de Docker, OLTP y Data Warehouse
├── README.md                    # Guía general de arquitectura y despliegue del proyecto
├── docker-compose.yml           # Orquestación del motor MySQL 8.0 (ripley-mysql-oltp)
├── .env.example                 # Variables de entorno de referencia para credenciales
├── requirements.txt             # Dependencias Python (PyMySQL, SQLAlchemy, Pandas, OpenPyXL)
├── docs/                        # Documentación de arquitectura y modelado
│   ├── PROYECT.md               # Alcance del negocio, problemática y KPIs
│   ├── MODELO_TRANSACCIONAL_OLTP.md # Modelo relacional 3NF de fuentes operativas
│   ├── ANALISIS_DIMENSIONAL.md  # Modelo dimensional Kimball (Constelación de Hechos)
│   ├── erd_oltp.mmd             # Diagrama ERD relacional OLTP (Mermaid Crow's Foot)
│   ├── erd_oltp.png             # Imagen renderizada en alta resolución del ERD OLTP
│   ├── erd_dw.mmd               # Diagrama ERD dimensional DW (Mermaid Crow's Foot)
│   └── erd_dw.png               # Imagen renderizada del modelo dimensional DW
├── database/
│   ├── oltp/
│   │   └── 01_schema.sql        # DDL de creación de las 24 tablas operativas en 3NF
│   └── dw/
│       ├── 01_schema.sql        # DDL de 8 dimensiones, 2 hechos y comodines Kimball (-1)
│       └── 02_seed_tiempo.sql   # Seed SQL estático de DIM_FECHA (2025-2027) y DIM_HORA (1440 min)
├── scripts/
│   ├── oltp/
│   │   ├── reset_db.py          # Limpieza y recreación de tablas OLTP en 3NF
│   │   ├── generate_seed_data.py# Generador masivo de transacciones e IoT (~11,000 hechos)
│   │   └── export_to_excel.py   # Exportación de 24 tablas OLTP a Excel multi-hoja
│   └── dw/
│       ├── reset_dw.py          # Limpieza y recreación de tablas DW con comodines (-1)
│       ├── populate_tiempo.py   # Generador determinista de DIM_FECHA y DIM_HORA
│       └── export_dw_to_excel.py# Exportación de las 10 tablas DW a Excel formateado
└── exports/                     # Archivos Excel generados (.gitignore)
    ├── ripley_oltp_data.xlsx    # 24 tablas operacionales con transacciones
    └── ripley_dw_data.xlsx      # 10 tablas analíticas (dimensiones y hechos)
```

---

## 2. Automatización con Makefile

El proyecto cuenta con un `Makefile` en la raíz con comandos claramente diferenciados entre infraestructura, sistema transaccional (OLTP) y sistema analítico (DW):

```bash
make help
```

### Comandos de Infraestructura Docker
| Comando | Acción |
| :--- | :--- |
| `make db-up` | Levanta el contenedor MySQL en segundo plano (`sudo docker compose up -d`). |
| `make db-down` | Detiene y remueve el contenedor MySQL. |
| `make db-ps` | Consulta el estado y salud del contenedor. |
| `make db-logs` | Visualiza los logs en tiempo real de MySQL. |
| `make db-shell` | Consola interactiva MySQL conectada a `ripley_oltp` (`ripley_user`). |
| `make db-shell-dw` | Consola interactiva MySQL conectada a `ripley_dw` (`ripley_user`). |
| `make db-root` | Consola interactiva MySQL como superusuario `root`. |

### Comandos OLTP (Base Transaccional `ripley_oltp`)
| Comando | Acción |
| :--- | :--- |
| `make oltp-reset` | **Reinicia la BD OLTP** recreando las 24 tablas en 3NF desde cero. |
| `make oltp-seed` | **Puebla la BD OLTP** generando catálogos y ~11,000 hechos con horas pico y anomalías. |
| `make oltp-export` | **Exporta las 24 tablas OLTP** a `exports/ripley_oltp_data.xlsx`. |

### Comandos DW (Data Warehouse `ripley_dw`)
| Comando | Acción |
| :--- | :--- |
| `make dw-reset` | **Reinicia el DW** recreando 8 dimensiones, 2 hechos y registros comodín `-1`. |
| `make dw-seed-tiempo` | **Puebla las dimensiones temporales** estáticas (`DIM_FECHA` y `DIM_HORA`). |
| `make dw-export` | **Exporta las 10 tablas DW** a `exports/ripley_dw_data.xlsx`. |

*(Nota: Los comandos `make db-reset`, `make seed-data` y `make export-excel` se mantienen como alias funcionales de OLTP por retrocompatibilidad).*

---

## 3. Modelo del Data Warehouse (`ripley_dw`)

El Data Warehouse implementa una **Constelación de Hechos (Fact Constellation)** con dimensiones conformes:

### Dimensiones Conformes (8)
1. **`DIM_FECHA`**: Calendario 2025-2027 (1,096 días), feriados oficiales de Perú (fijos y Semana Santa móvil) y temporadas comerciales retail (Día de la Madre, Fiestas Patrias, Cyber Wow, Black Friday, Navidad). Clave inteligente `YYYYMMDD`.
2. **`DIM_HORA`**: 1,440 minutos del día (00:00 a 23:59), con clasificación de `tipo_horario` (Hora Pico, Hora Valle, Hora Normal) y `turno` laboral. Clave inteligente `HHMM`.
3. **`DIM_TIENDA`**: Sucursales físicas con atributos de formato, aforo máximo, superficie m² y cajas instaladas. Clave sustituta (SK).
4. **`DIM_PRODUCTO`**: Catálogo comercial con jerarquía (Departamento, Categoría, Subcategoría, Marca, Marca Propia). Clave sustituta (SK).
5. **`DIM_CAJA`**: Puntos de venta POS por piso, zona y tipo de caja (Tradicional, Rápida, Self-Checkout). Clave sustituta (SK).
6. **`DIM_PERSONAL`**: Colaboradores/cajeros por cargo, turno y tipo de contrato. Clave sustituta (SK).
7. **`DIM_MEDIO_PAGO`**: Tipos de medio de pago, canal y flag de tarjeta propia Ripley. Clave sustituta (SK).
8. **`DIM_CLIENTE`**: Clientes con segmento de fidelidad (Silver, Gold, Black) y perfil sociodemográfico. Clave sustituta (SK).

### Registros Comodín (-1)
Siguiendo las mejores prácticas de Ralph Kimball, todas las dimensiones inicializan un registro comodín con identificador `-1` (`Desconocido` / `No especificado`), garantizando integridad referencial ante datos no identificados o ventas anónimas.

### Tablas de Hechos (2)
1. **`FACT_VENTAS`**: Hecho a nivel de línea de ticket (grano atómico). Conecta las 8 dimensiones y almacena métricas financieras (`cantidad_unidades`, `subtotal_neto`, `monto_descuento`, `monto_total_venta`, `margen_bruto`) y operacionales (`tiempo_espera_cola_seg`, `tiempo_atencion_caja_seg`).
2. **`FACT_AFLUENCIA_TIENDA`**: Hecho de instantánea periódica horaria (Periodic Snapshot). Conecta `DIM_FECHA`, `DIM_HORA` y `DIM_TIENDA` para medir personas entrantes/salientes, aforo promedio y porcentaje de saturación de tienda.

---

## 4. Guía Rápida de Despliegue

```bash
# 1. Levantar el contenedor Docker
make db-up

# 2. Inicializar y poblar la base transaccional OLTP
make oltp-reset
make oltp-seed

# 3. Inicializar y poblar el Data Warehouse dimensional
make dw-reset
make dw-seed-tiempo

# 4. Generar reportes Excel de ambos entornos
make oltp-export
make dw-export
```

### Credenciales de Conexión a las Bases de Datos
* **Host:** `localhost` (puerto `3306`)
* **Usuario:** `ripley_user` / **Contraseña:** `ripley_pass`
* **Base OLTP:** `ripley_oltp`
* **Base DW:** `ripley_dw`
* **Superusuario:** `root` / **Contraseña:** `rootpassword`

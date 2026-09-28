# Proyecto de Inteligencia de Negocios - Ripley

Modelo analítico y operacional para el análisis y optimización de la gestión de ventas y afluencia en horas pico de la empresa comercial **Ripley**.

---

## 1. Estructura del Repositorio

```
.
├── Makefile                  # Automatización de tareas (Docker, migraciones, exportaciones)
├── README.md                 # Guía general de arquitectura y despliegue del proyecto
├── docker-compose.yml        # Orquestación del contenedor MySQL 8.0 para la base OLTP
├── .env.example              # Variables de entorno de referencia para credenciales
├── requirements.txt          # Dependencias Python para scripts de datos y utilitarios
├── docs/                     # Documentación de diseño y modelado
│   ├── PROYECT.md            # Alcance, problemática y KPIs del proyecto
│   ├── MODELO_TRANSACCIONAL_OLTP.md # Modelo relacional 3NF de las fuentes operativas
│   ├── ANALISIS_DIMENSIONAL.md      # Modelo dimensional de Kimball (Data Mart)
│   ├── erd_oltp.mmd          # Diagrama ERD en Mermaid (notación Crow's Foot y tipos de datos)
│   └── erd_oltp.png          # Imagen renderizada en alta resolución del ERD relacional 3NF
├── database/
│   └── oltp/
│       └── 01_schema.sql     # DDL de creación de las 24 tablas operativas en 3NF
├── scripts/
│   ├── generate_seed_data.py # Generador autosuficiente de transacciones e IoT (~11,000 hechos)
│   └── export_to_excel.py    # Script que extrae todas las tablas a un Excel multi-hoja
└── exports/                  # Directorio de salida para libros Excel generados (.gitignore)
```

---

## 2. Automatización con Makefile

El proyecto cuenta con un `Makefile` en la raíz para agilizar el ciclo de desarrollo sin memorizar comandos largos:

| Comando | Acción |
| :--- | :--- |
| `make help` | Muestra la lista interactiva de comandos disponibles. |
| `make db-up` | Levanta el contenedor MySQL con Docker en segundo plano (`sudo docker compose up -d`). |
| `make db-down` | Detiene el contenedor MySQL. |
| `make db-ps` | Consulta el estado y la salud del contenedor. |
| `make db-logs` | Visualiza los logs en tiempo real del motor MySQL. |
| `make db-shell` | Conexión interactiva a la consola MySQL con el usuario `ripley_user`. |
| `make db-root` | Conexión interactiva como superusuario `root`. |
| `make db-reset` | **Reinicia y vacía toda la base de datos recreando las 24 tablas en 3NF desde cero.** |
| `make seed-data` | **Puebla la BD y genera transacciones masivas (~11,000 hechos con horas pico y anomalías).** |
| `make export-excel` | **Exporta automáticamente todas las 24 tablas a un libro Excel multi-pestaña.** |
| `make clean` | Elimina el entorno virtual de Python y archivos temporales. |

---

## 3. Base de Datos Transaccional (OLTP)

La base de datos opera en **MySQL 8.0** y representa el sistema fuente operacional (POS, ERP comercial y sensores IoT de afluencia).

### Despliegue y Poblado

Desde la raíz del repositorio:

1. **Levantar el motor de base de datos:**
   ```bash
   make db-up
   ```
   *(El contenedor crea el esquema limpio y vacío a partir de `database/oltp/01_schema.sql`).*

2. **Poblar los datos y generar transacciones:**
   ```bash
   make seed-data
   ```

### Credenciales para Clientes Externos (DBeaver, MySQL Workbench, Power BI)
* **Host:** `localhost` o `127.0.0.1`
* **Puerto:** `3306`
* **Base de datos:** `ripley_oltp`
* **Usuario:** `ripley_user`
* **Contraseña:** `ripley_pass`

---

## 4. Exportación de Entidades a Excel

Para generar un libro Excel (`exports/ripley_oltp_data.xlsx`) donde **cada tabla de la base de datos es una hoja independiente** con formato y auto-ancho de columna:

```bash
make export-excel
```
*Este comando crea automáticamente un entorno virtual en `.venv`, instala las dependencias de `requirements.txt` y ejecuta la extracción desde MySQL.*

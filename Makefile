.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# DETECCIÓN DE SISTEMA OPERATIVO Y CONFIGURACIÓN MULTIPLATAFORMA
# -----------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
    # Entorno Windows Nativo (CMD / PowerShell)
    PYTHON_SYS := python
    BIN_DIR    := .venv\Scripts
    PYTHON     := $(BIN_DIR)\python.exe
    PIP        := $(BIN_DIR)\pip.exe
    CLEAN_CMD  := $(PYTHON_SYS) -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in ['.venv', '__pycache__'] + glob.glob('scripts/**/__pycache__', recursive=True)]"
else
    # Entornos Unix (Linux / macOS / WSL)
    PYTHON_SYS := python3
    BIN_DIR    := .venv/bin
    PYTHON     := $(BIN_DIR)/python3
    PIP        := $(BIN_DIR)/pip
    CLEAN_CMD  := rm -rf .venv __pycache__ scripts/__pycache__ scripts/oltp/__pycache__ scripts/dw/__pycache__
endif

DOCKER ?= docker

.PHONY: help venv clean \
        db-up db-down db-ps db-logs db-shell db-shell-dw db-root \
        oltp-reset oltp-seed oltp-export \
        dw-reset dw-seed-tiempo dw-export \
        db-reset seed-data export-excel

help:
	@echo "=================================================================="
	@echo "📋 COMANDOS DISPONIBLES (PROYECTO RIPLEY IN - OLTP & DATA WAREHOUSE)"
	@echo "=================================================================="
	@echo "  [INFRAESTRUCTURA DOCKER]"
	@echo "  make db-up          - Levanta MySQL con Docker en segundo plano"
	@echo "  make db-down        - Detiene el contenedor MySQL"
	@echo "  make db-ps          - Consulta el estado y salud del contenedor"
	@echo "  make db-logs        - Muestra los logs en tiempo real de MySQL"
	@echo "  make db-shell       - Consola MySQL interactiva en ripley_oltp"
	@echo "  make db-shell-dw    - Consola MySQL interactiva en ripley_dw"
	@echo "  make db-root        - Consola MySQL interactiva como root"
	@echo ""
	@echo "  [TRANSACCIONAL - OLTP (ripley_oltp)]"
	@echo "  make oltp-reset     - Reinicia la BD OLTP (recrea 24 tablas en 3NF)"
	@echo "  make oltp-seed      - Puebla maestros y ~11,000 transacciones OLTP"
	@echo "  make oltp-export    - Exporta las 24 tablas OLTP a Excel (.xlsx)"
	@echo ""
	@echo "  [ANALÍTICO - DATA WAREHOUSE (ripley_dw)]"
	@echo "  make dw-reset       - Reinicia el DW (esquema Kimball con comodines -1)"
	@echo "  make dw-seed-tiempo - Puebla DIM_FECHA (2025-2027) y DIM_HORA (1440 min)"
	@echo "  make dw-export      - Exporta las 10 tablas del DW a Excel (.xlsx)"
	@echo ""
	@echo "  [UTILITARIOS]"
	@echo "  make venv           - Prepara entorno virtual Python y dependencias"
	@echo "  make clean          - Elimina cache y entorno virtual"
	@echo "=================================================================="

venv: .venv/touchfile

.venv/touchfile: requirements.txt
	@echo "📦 Configurando entorno virtual Python..."
	@$(PYTHON_SYS) -c "import os, venv; os.path.isdir('.venv') or venv.create('.venv', with_pip=True)"
	@$(PIP) install --quiet --upgrade pip
	@$(PIP) install --quiet -r requirements.txt
	@$(PYTHON_SYS) -c "import pathlib; pathlib.Path('.venv/touchfile').touch()"
	@echo "✅ Entorno virtual listo en .venv"

# -----------------------------------------------------------------------------
# INFRAESTRUCTURA DOCKER
# -----------------------------------------------------------------------------
db-up:
	$(DOCKER) compose up -d

db-down:
	$(DOCKER) compose down

db-ps:
	$(DOCKER) compose ps

db-logs:
	$(DOCKER) compose logs -f mysql-oltp

db-shell:
	$(DOCKER) compose exec -it mysql-oltp mysql -u ripley_user -pripley_pass ripley_oltp

db-shell-dw:
	$(DOCKER) compose exec -it mysql-oltp mysql -u ripley_user -pripley_pass ripley_dw

db-root:
	$(DOCKER) compose exec -it mysql-oltp mysql -u root -prootpassword

# -----------------------------------------------------------------------------
# BASE DE DATOS TRANSACCIONAL (OLTP)
# -----------------------------------------------------------------------------
oltp-reset: venv
	@$(PYTHON) scripts/oltp/reset_db.py

oltp-seed: venv
	@$(PYTHON) scripts/oltp/generate_seed_data.py

oltp-export: venv
	@$(PYTHON) scripts/oltp/export_to_excel.py

# Alias de compatibilidad hacia atrás
db-reset: oltp-reset
seed-data: oltp-seed
export-excel: oltp-export

# -----------------------------------------------------------------------------
# DATA WAREHOUSE DIMENSIONAL (DW)
# -----------------------------------------------------------------------------
dw-reset: venv
	@$(PYTHON) scripts/dw/reset_dw.py

dw-seed-tiempo: venv
	@$(PYTHON) scripts/dw/populate_tiempo.py

dw-export: venv
	@$(PYTHON) scripts/dw/export_dw_to_excel.py

# -----------------------------------------------------------------------------
# LIMPIEZA
# -----------------------------------------------------------------------------
clean:
	@$(CLEAN_CMD)
	@echo "🧹 Limpieza completada."

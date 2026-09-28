.DEFAULT_GOAL := help
PYTHON := .venv/bin/python3
PIP := .venv/bin/pip

.PHONY: help venv db-up db-down db-ps db-logs db-shell db-root db-reset seed-data export-excel clean

help:
	@echo "=================================================================="
	@echo "📋 COMANDOS DISPONIBLES (PROYECTO RIPLEY IN)"
	@echo "=================================================================="
	@echo "  make db-up         - Levanta MySQL OLTP con Docker en segundo plano"
	@echo "  make db-down       - Detiene el contenedor MySQL"
	@echo "  make db-ps         - Consulta el estado y salud del contenedor"
	@echo "  make db-logs       - Muestra los logs en tiempo real de MySQL"
	@echo "  make db-shell      - Entra a la consola interactiva MySQL (ripley_user)"
	@echo "  make db-root       - Entra a la consola interactiva MySQL como root"
	@echo "  make db-reset      - Reinicia y vacía toda la BD (recrea tablas desde 0)"
	@echo "  make seed-data     - Puebla maestros y genera transacciones (~11,000 hechos)"
	@echo "  make export-excel  - Exporta todas las entidades a un Excel (.xlsx)"
	@echo "  make venv          - Crea el entorno virtual Python con dependencias"
	@echo "  make clean         - Elimina el entorno virtual y temporales"
	@echo "=================================================================="

venv: .venv/touchfile

.venv/touchfile: requirements.txt
	@echo "📦 Configurando entorno virtual Python..."
	@test -d .venv || python3 -m venv .venv
	@$(PIP) install --quiet --upgrade pip
	@$(PIP) install --quiet -r requirements.txt
	@touch .venv/touchfile
	@echo "✅ Entorno virtual listo en .venv"

db-reset: venv
	@$(PYTHON) scripts/reset_db.py

seed-data: venv
	@$(PYTHON) scripts/generate_seed_data.py

export-excel: venv
	@$(PYTHON) scripts/export_to_excel.py

db-up:
	sudo docker compose up -d

db-down:
	sudo docker compose down

db-ps:
	sudo docker compose ps

db-logs:
	sudo docker compose logs -f mysql-oltp

db-shell:
	sudo docker compose exec -it mysql-oltp mysql -u ripley_user -pripley_pass ripley_oltp

db-root:
	sudo docker compose exec -it mysql-oltp mysql -u root -prootpassword ripley_oltp

clean:
	rm -rf .venv __pycache__ scripts/__pycache__
	@echo "🧹 Limpieza completada."

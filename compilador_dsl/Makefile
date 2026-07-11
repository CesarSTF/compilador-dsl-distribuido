.PHONY: up down restart logs build test

# Levanta los contenedores en segundo plano (nodos 192.168.1.10 y 11)
up:
	docker compose up -d

# Tumba los contenedores y elimina la red asociada
down:
	docker compose down

# Reconstruye las imágenes y levanta los contenedores
build:
	docker compose up -d --build

# Reinicia los contenedores
restart:
	docker compose restart

# Muestra los logs en tiempo real
logs:
	docker compose logs -f

# Ejecuta el script de prueba de carga
test:
	python test_carga.py

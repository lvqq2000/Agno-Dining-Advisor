.PHONY: setup run up down build rebuild logs

# Build the containers
setup:
	docker compose build

# Start the project
run:
	docker compose up

# ---- Optional helper commands ----

# Build the containers (same as setup, kept for flexibility)
build:
	docker compose build

# Rebuild and start containers
rebuild:
	docker compose up --build

# Start containers (same as run, kept for flexibility)
up:
	docker compose up

# Stop containers
down:
	docker compose down

# View logs
logs:
	docker compose logs -f
.PHONY: setup migrate run up down build rebuild logs

# Set up the environment
setup: build run migrate

# Build the containers
build:
	docker compose build

migrate:
	docker compose exec app alembic upgrade head

# Start the project
run:
	docker compose up

# ---- Optional helper commands ----

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
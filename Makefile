.PHONY: setup migrate run up down build rebuild logs

# Set up the environment
setup: build run migrate seed

# Build the containers
build:
	docker compose build

# Run project seed (populate DB). Uses a one-off container so it's safe to run any time.
seed:
	docker compose run --rm app python -m app.db.seeds.seed

# Rebuild the app image and run seed (useful when requirements changed)
seed-rebuild:
	docker compose build --no-cache app
	docker compose run --rm app python -m app.db.seeds.seed

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
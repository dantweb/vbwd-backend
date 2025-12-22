.PHONY: up down build test test-unit test-coverage logs shell clean

# Start all services
up:
	docker-compose up -d

# Start with rebuild
up-build:
	docker-compose up -d --build

# Stop services
down:
	docker-compose down

# Build containers
build:
	docker-compose build

# Run all tests
test:
	docker-compose run --rm test pytest -v

# Run unit tests only
test-unit:
	docker-compose run --rm test pytest tests/unit/ -v

# Run tests with coverage
test-coverage:
	docker-compose run --rm test pytest --cov=src --cov-report=term-missing

# View logs
logs:
	docker-compose logs -f

# Shell access to API container
shell:
	docker-compose exec api bash

# Clean up
clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

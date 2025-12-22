# VBWD Backend

Python/Flask API for the VBWD SaaS platform.

## Tech Stack

- **Framework**: Flask 3.0
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **Testing**: pytest

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dantweb/vbwd-backend.git
cd vbwd-backend

# Copy environment variables
cp .env.example .env

# Start services
make up

# Run tests
make test
```

## Development Commands

```bash
make up           # Start all services
make up-build     # Start with rebuild
make down         # Stop services
make test         # Run all tests
make test-unit    # Run unit tests only
make test-coverage # Run tests with coverage
make logs         # View logs
make shell        # Shell access to API container
make clean        # Clean up
```

## Project Structure

```
├── src/
│   ├── events/        # Domain events
│   ├── handlers/      # Event handlers
│   ├── interfaces/    # Abstract interfaces
│   ├── models/        # SQLAlchemy models
│   ├── plugins/       # Plugin system
│   ├── repositories/  # Data access layer
│   ├── routes/        # API endpoints
│   ├── schemas/       # Marshmallow schemas
│   ├── sdk/           # Payment SDK adapters
│   ├── services/      # Business logic
│   ├── webhooks/      # Webhook handling
│   └── utils/         # Utilities
├── tests/
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── alembic/           # Database migrations
└── container/         # Docker configuration
```

## Architecture

- **TDD**: Test-Driven Development
- **SOLID**: Single Responsibility, Open/Closed, Liskov, Interface Segregation, DI
- **Clean Architecture**: Separation of concerns
- **Event-Driven**: Domain events with handlers

## Tests

```bash
# Run all tests
docker-compose run --rm test pytest -v

# Run specific test file
docker-compose run --rm test pytest tests/unit/handlers/test_payment_handlers.py -v

# Run with coverage
docker-compose run --rm test pytest --cov=src --cov-report=term-missing
```

## License

CC0 1.0 Universal (Public Domain)

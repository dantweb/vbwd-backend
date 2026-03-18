"""Alembic environment configuration.

Intentionally plugin-agnostic: plugin models are discovered dynamically
by scanning each plugin's src/models/ directory and importing every
module found there.  This registers all SQLAlchemy model classes into
db.Model.metadata without naming any specific plugin in this file.
"""
from logging.config import fileConfig
import sys
import os
import importlib
import pkgutil

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vbwd.config import get_database_url
from vbwd.extensions import db

# Import core models so their tables are visible to autogenerate
import vbwd.models  # noqa: F401  — side-effect: registers all core model classes

# Dynamically import every model module from every plugin's src/models/ directory.
# No plugin names are hard-coded here; new plugins are picked up automatically.
_plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
for _plugin in sorted(os.listdir(_plugins_dir)):
    _models_dir = os.path.join(_plugins_dir, _plugin, "src", "models")
    if not os.path.isdir(_models_dir):
        continue
    for _, _module_name, _is_pkg in pkgutil.iter_modules([_models_dir]):
        if not _is_pkg:
            importlib.import_module(f"plugins.{_plugin}.src.models.{_module_name}")

# Alembic config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the runtime database URL
config.set_main_option("sqlalchemy.url", get_database_url())

# All tables — core and plugin — are now registered in this metadata
target_metadata = db.Model.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

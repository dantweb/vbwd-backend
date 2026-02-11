"""Plugin management CLI commands."""
import click
from flask import current_app
from flask.cli import with_appcontext


@click.group("plugins")
def plugins_cli():
    """Plugin management commands."""
    pass


@plugins_cli.command("list")
@with_appcontext
def list_plugins():
    """List all registered plugins."""
    manager = getattr(current_app, "plugin_manager", None)
    if not manager:
        click.echo("Plugin system not initialized.")
        return

    plugins = manager.get_all_plugins()
    if not plugins:
        click.echo("No plugins registered.")
        return

    for plugin in plugins:
        meta = plugin.metadata
        click.echo(f"{meta.name} ({meta.version}) — {plugin.status.value.upper()}")


@plugins_cli.command("enable")
@click.argument("name")
@with_appcontext
def enable_plugin(name):
    """Enable a plugin."""
    manager = getattr(current_app, "plugin_manager", None)
    if not manager:
        click.echo("Plugin system not initialized.")
        return

    try:
        plugin = manager.get_plugin(name)
        if not plugin:
            click.echo(f"Plugin '{name}' not found.")
            return
        if plugin.status.value == "enabled":
            click.echo(f"Plugin '{name}' is already enabled.")
            return
        # Re-initialize if needed
        from src.plugins.base import PluginStatus

        if plugin.status == PluginStatus.DISABLED:
            plugin._status = PluginStatus.INITIALIZED
        manager.enable_plugin(name)
        click.echo(f"Plugin '{name}' enabled.")
    except ValueError as e:
        click.echo(f"Error: {e}")


@plugins_cli.command("disable")
@click.argument("name")
@with_appcontext
def disable_plugin(name):
    """Disable a plugin."""
    manager = getattr(current_app, "plugin_manager", None)
    if not manager:
        click.echo("Plugin system not initialized.")
        return

    try:
        manager.disable_plugin(name)
        click.echo(f"Plugin '{name}' disabled.")
    except ValueError as e:
        click.echo(f"Error: {e}")

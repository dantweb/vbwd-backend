"""CLI command to reset database and populate with clean demo data."""
import click
from flask.cli import with_appcontext


@click.command("reset-demo")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@with_appcontext
def reset_demo_command(yes):
    """
    Reset database to clean demo state.

    Removes all transactional data (invoices, subscriptions, purchases, etc.)
    and replaces plans/addons/token bundles with a curated demo set.
    User accounts are preserved.

    Usage:
        flask reset-demo
        flask reset-demo --yes   # skip confirmation
    """
    if not yes:
        click.echo("This will DELETE all invoices, subscriptions, purchases,")
        click.echo("and replace plans/addons/token bundles with demo data.")
        click.echo("User accounts will be preserved.")
        if not click.confirm("Continue?"):
            click.echo("Aborted.")
            return

    from src.extensions import db
    from src.cli._demo_seeder import DemoSeeder

    seeder = DemoSeeder(db.session)
    stats = seeder.run()

    click.echo("Database reset complete:")
    for key, val in stats.items():
        click.echo(f"  {key}: {val}")

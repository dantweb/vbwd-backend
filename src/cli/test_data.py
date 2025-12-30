"""CLI commands for test data management."""
import click
from flask.cli import with_appcontext


@click.command('seed-test-data')
@with_appcontext
def seed_test_data_command():
    """
    Seed test data into the database.

    Requires TEST_DATA_SEED=true environment variable.
    Creates test user, admin, tariff plan, and subscription.

    Usage:
        flask seed-test-data
        TEST_DATA_SEED=true flask seed-test-data
    """
    from src.extensions import db
    from src.testing.test_data_seeder import TestDataSeeder

    seeder = TestDataSeeder(db.session)
    if seeder.seed():
        click.echo('Test data seeded successfully.')
        click.echo(f'  - Test user: {seeder._create_test_user()}')
        click.echo(f'  - Test admin: {seeder._create_test_admin()}')
    else:
        click.echo('Test data seeding skipped (TEST_DATA_SEED != true).')
        click.echo('Set TEST_DATA_SEED=true to enable seeding.')


@click.command('cleanup-test-data')
@with_appcontext
def cleanup_test_data_command():
    """
    Remove test data from the database.

    Requires TEST_DATA_CLEANUP=true environment variable.
    Removes test users, subscriptions, and tariff plans.

    Usage:
        flask cleanup-test-data
        TEST_DATA_CLEANUP=true flask cleanup-test-data
    """
    from src.extensions import db
    from src.testing.test_data_seeder import TestDataSeeder

    seeder = TestDataSeeder(db.session)
    if seeder.cleanup():
        click.echo('Test data cleaned up successfully.')
    else:
        click.echo('Test data cleanup skipped (TEST_DATA_CLEANUP != true).')
        click.echo('Set TEST_DATA_CLEANUP=true to enable cleanup.')

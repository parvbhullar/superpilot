from pathlib import Path

import click
import yaml

from superpilot.app.cli_app.main import run_superpilot
from superpilot.app.client_lib.shared_click_commands import (
    DEFAULT_SETTINGS_FILE,
    make_settings,
)
from superpilot.app.client_lib.utils import coroutine, handle_exceptions


@click.group()
def superpilot():
    """Temporary command group for v2 commands."""
    pass


superpilot.add_command(make_settings)


@superpilot.command()
@click.option(
    "--settings-file",
    type=click.Path(),
    default=DEFAULT_SETTINGS_FILE,
)
@click.option(
    "--pdb",
    is_flag=True,
    help="Drop into a debugger if an error is raised.",
)
@coroutine
async def run(settings_file: str, pdb: bool) -> None:
    """Run the Superpilot ."""
    click.echo("Running Superpilot ...")
    settings_file = Path(settings_file)
    settings = {}
    if settings_file.exists():
        settings = yaml.safe_load(settings_file.read_text())
    main = handle_exceptions(run_superpilot, with_debugger=pdb)
    await main(settings)


if __name__ == "__main__":
    superpilot()

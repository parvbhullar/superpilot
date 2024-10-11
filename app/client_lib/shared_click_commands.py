import pathlib

import click

DEFAULT_SETTINGS_FILE = str(
    pathlib.Path("~/superpilot/default_pilot_settings.yml").expanduser()
)


@click.command()
@click.option(
    "--settings-file",
    type=click.Path(),
    default=DEFAULT_SETTINGS_FILE,
)
def make_settings(settings_file: str) -> None:
    from superpilot.app.client_lib.settings import make_user_configuration

    make_user_configuration(pathlib.Path(settings_file))


@click.command()
@click.option("-d", "--detailed", is_flag=True, help="Show detailed status.")
def status(detailed: bool):
    import importlib
    import pkgutil

    import superpilot.core
    from superpilot.core.status import print_status

    status_list = []
    for loader, package_name, is_pkg in pkgutil.iter_modules(superpilot.core.__path__):
        if is_pkg:
            subpackage = importlib.import_module(
                f"{superpilot.core.__name__}.{package_name}"
            )
            if hasattr(subpackage, "status"):
                status_list.append(subpackage.status)

    print_status(status_list, detailed)

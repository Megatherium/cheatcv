"""Main CLI entry point for CheatCV."""

import click
from . import __version__
from .commands import info as info_module
from .commands import transform as transform_module
from .commands import detect as detect_module


@click.group()
@click.version_option(version=__version__, prog_name='cheatcv')
@click.pass_context
def cli(ctx):
    """
    CheatCV - A CLI tool for quick computer vision operations.

    Use --help with any command to see detailed usage information.
    """
    pass


# Info commands group
@cli.group()
def info():
    """Image information commands."""
    pass


info.add_command(info_module.info, name='show')
info.add_command(info_module.list_images, name='list')


# Transform commands group
@cli.group()
def transform():
    """Image transformation commands."""
    pass


transform.add_command(transform_module.resize)
transform.add_command(transform_module.convert)
transform.add_command(transform_module.edges)


# Detect commands group
@cli.group()
def detect():
    """Object detection commands."""
    pass


detect.add_command(detect_module.faces)


# Main entry point
def main():
    """Main entry point for the CLI."""
    cli(prog_name='cheatcv')


if __name__ == '__main__':
    main()

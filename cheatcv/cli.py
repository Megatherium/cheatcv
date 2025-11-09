"""CheatCV CLI - Main entry point for all commands."""

import click

from cheatcv.commands import (
    run,
    hotkey,
    keepalive,
    test,
    benchmark,
    profile,
)


@click.group()
@click.version_option(version="0.1.0", prog_name="cheatcv")
def main():
    """
    CheatCV - Android game automation via ADB with CV pattern detection.

    Use 'cheatcv <command> --help' for more information on a specific command.
    """
    pass


# Register commands
main.add_command(run.run)
main.add_command(hotkey.hotkey)
main.add_command(keepalive.keepalive)
main.add_command(test.test)
main.add_command(benchmark.benchmark)
main.add_command(profile.profile)


if __name__ == "__main__":
    main()

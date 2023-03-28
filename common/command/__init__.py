import typer

from common.command.mysql import db_typer
from common.command.tools import tool_typer

banner = """
-------  -----  ------- ------- ------- ------- ------- -------
|______ |_____| |______    |    |_____] |     | |______    |
|       |     | ______|    |    |       |_____| ______|    |
"""

cli = typer.Typer()

cli.add_typer(db_typer, name="db")
cli.add_typer(tool_typer, name="tools")

from common.command.shell import *  # noqa

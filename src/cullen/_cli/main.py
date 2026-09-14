import sys

from typer import Typer, echo

from cullen import CullenError
from cullen._cli.commands.cull import app as cull_app
from cullen._cli.commands.flop import app as flop_app
from cullen._cli.commands.relocate import app as relocate_app

app = Typer(no_args_is_help=True)

subapps = [
    cull_app,
    relocate_app,
    flop_app,
]

for subapp in subapps:
    app.add_typer(subapp)


def main() -> None:
    try:
        app()
    except CullenError as error:
        echo(str(error), err=True)

        sys.exit(1)


if __name__ == '__main__':
    # app("relocate /Volumes/sharge/jsons".split())
    app("cull /Users/justin/photos/stages/stage1.filter/26.05.03.sivakova_bd".split())
    # app("cull /Volumes/sharge/photos/stages/stage1.filter/26.03.22.fen_init_lab".split())
    # app("cull --help".split())

from typing import Any

from click import Context
from typer import Typer, Exit, echo
from typer.core import TyperGroup

from cullen.commands.cull import app as cull_app
from cullen.errors import CullenError
from cullen.commands.relocate import app as relocate_app
from cullen.commands.flop import app as flop_app


class ErrorHandlingGroup(TyperGroup):
    def invoke(self, ctx: Context) -> Any:
        try:
            return super().invoke(ctx)
        except CullenError as error:
            echo(str(error), err=True)

            raise Exit(code=1) from error


app = Typer(cls=ErrorHandlingGroup, no_args_is_help=True)

subapps = [
    cull_app,
    relocate_app,
    flop_app,
]

for subapp in subapps:
    app.add_typer(subapp)


if __name__ == '__main__':
    # app("relocate /Volumes/sharge/jsons".split())
    app("cull /Users/justin/photos/stages/stage1.filter/26.05.03.sivakova_bd".split())
    # app("cull /Volumes/sharge/photos/stages/stage1.filter/26.03.22.fen_init_lab".split())
    # app("cull --help".split())

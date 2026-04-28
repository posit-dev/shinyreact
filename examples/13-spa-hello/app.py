from pathlib import Path

from shiny import reactive
from shinyjson import SpaApp, render_json

_src_dir = Path(__file__).parent


def server(input, output, session):  # noqa: ARG001
    @reactive.calc
    def greeting():
        name = input.name()
        if not name:
            return "World"
        return name

    @render_json
    def txtout_title():
        return f"Hello, {greeting()}!"

    @render_json
    def txtout_count():
        return input.click_count()


app = SpaApp(_src_dir / "www", server)

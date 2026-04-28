from pathlib import Path

import shinyjson
from shiny import reactive

_src_dir = Path(__file__).parent


def server(input, output, session):  # noqa: ARG001
    @reactive.calc
    def greeting():
        name = input.name()
        if not name:
            return "World"
        return name

    @shinyjson.render_json
    def txtout_title():
        return f"Hello, {greeting()}!"

    @shinyjson.render_json
    def txtout_count():
        return input.click_count()


app = shinyjson.SpaApp(_src_dir / "www", server)

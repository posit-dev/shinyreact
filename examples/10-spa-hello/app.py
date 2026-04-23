from pathlib import Path

import shinyjson
from shiny import reactive
from spa_app import SpaApp

_src_dir = Path(__file__).parent


def server(input, output, session):
    @reactive.calc
    def greeting():
        name = input.name()
        if not name:
            return "World"
        return name

    @shinyjson.render
    def greeting_data():
        return {"greeting": f"Hello, {greeting()}!", "count": input.click_count()}


app = SpaApp(_src_dir / "www", server)

import datetime
from pathlib import Path

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session

_inputs_dep = HTMLDependency(
    name="inputs-example",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "inputs.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("main", extra_deps=[_inputs_dep])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def main():
        return shinyjson.Spec(
            root="app",
            elements={
                "app": shinyjson.Element(type="App", props={}),
            },
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()

    @shinyjson.render
    def numberout():
        return str(input.numberin())

    @shinyjson.render
    def checkboxout():
        return str(input.checkboxin())

    @shinyjson.render
    def radioout():
        return str(input.radioin())

    @shinyjson.render
    def selectout():
        return str(input.selectin())

    @shinyjson.render
    def sliderout():
        return str(input.sliderin())

    @shinyjson.render
    def dateout():
        return str(input.datein())

    @shinyjson.render
    @reactive.event(input.buttonin, ignore_init=True)
    def buttonout():
        return str(input.buttonin())

    @shinyjson.render
    def fileout():
        files = input.filein()
        if files is None:
            return None
        # Summarize file info from the client
        summaries = []
        for f in files:
            size_kb = round(f["size"] / 1024, 1)
            summaries.append(f"📄 {f['name']} ({size_kb} KB, {f['type'] or 'unknown type'})")
        return "\n".join(summaries)

    @shinyjson.render
    def batchout():
        data = input.batchdata()
        if data is None:
            return "No data submitted yet."

        data["receivedAt"] = datetime.datetime.now().isoformat()

        return data


app = App(app_ui, server)

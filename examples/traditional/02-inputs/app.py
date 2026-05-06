import datetime
from pathlib import Path

import shinyreact
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

_src_dir = Path(__file__).parent
_inputs_dep = HTMLDependency(
    name="inputs-example",
    version=str(int((_src_dir / "inputs.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "inputs.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyreact.ui_output("main", extra_deps=[_inputs_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def page_layout(title: str, *children: shinyreact.Node) -> shinyreact.Node:
    return shinyreact.Node(
        type="PageLayout", props={"title": title}, children=list(children)
    )


def text_input_card(
    input_id: str, output_id: str, default_value: str = "Hello, world!"
) -> shinyreact.Node:
    return shinyreact.Node(
        type="TextInputCard",
        props={
            "input_id": input_id,
            "output_id": output_id,
            "default_value": default_value,
        },
    )


def number_input_card(
    input_id: str, output_id: str, default_value: float = 42
) -> shinyreact.Node:
    return shinyreact.Node(
        type="NumberInputCard",
        props={
            "input_id": input_id,
            "output_id": output_id,
            "default_value": default_value,
        },
    )


def checkbox_input_card(
    input_id: str, output_id: str, default_value: bool = False
) -> shinyreact.Node:
    return shinyreact.Node(
        type="CheckboxInputCard",
        props={
            "input_id": input_id,
            "output_id": output_id,
            "default_value": default_value,
        },
    )


def radio_input_card(
    input_id: str, output_id: str, default_value: str = "option1"
) -> shinyreact.Node:
    return shinyreact.Node(
        type="RadioInputCard",
        props={
            "input_id": input_id,
            "output_id": output_id,
            "default_value": default_value,
        },
    )


def select_input_card(
    input_id: str, output_id: str, default_value: str = "apple"
) -> shinyreact.Node:
    return shinyreact.Node(
        type="SelectInputCard",
        props={
            "input_id": input_id,
            "output_id": output_id,
            "default_value": default_value,
        },
    )


def slider_input_card(
    input_id: str, output_id: str, default_value: float = 50
) -> shinyreact.Node:
    return shinyreact.Node(
        type="SliderInputCard",
        props={
            "input_id": input_id,
            "output_id": output_id,
            "default_value": default_value,
        },
    )


def date_input_card(input_id: str, output_id: str) -> shinyreact.Node:
    return shinyreact.Node(
        type="DateInputCard",
        props={"input_id": input_id, "output_id": output_id},
    )


def button_input_card(input_id: str, output_id: str) -> shinyreact.Node:
    return shinyreact.Node(
        type="ButtonInputCard",
        props={"input_id": input_id, "output_id": output_id},
    )


def file_input_card(input_id: str, output_id: str) -> shinyreact.Node:
    return shinyreact.Node(
        type="FileInputCard",
        props={"input_id": input_id, "output_id": output_id},
    )


def batch_form_card(input_id: str, output_id: str) -> shinyreact.Node:
    return shinyreact.Node(
        type="BatchFormCard",
        props={"input_id": input_id, "output_id": output_id},
    )


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        return page_layout(
            "Shiny React Input Examples",
            text_input_card("txtin", "txtout"),
            number_input_card("numberin", "numberout"),
            checkbox_input_card("checkboxin", "checkboxout"),
            radio_input_card("radioin", "radioout"),
            select_input_card("selectin", "selectout"),
            slider_input_card("sliderin", "sliderout"),
            date_input_card("datein", "dateout"),
            button_input_card("buttonin", "buttonout"),
            file_input_card("filein", "fileout"),
            batch_form_card("batchdata", "batchout"),
        )

    @shinyreact.reactive_output
    def txtout():
        return input.txtin().upper()

    @shinyreact.reactive_output
    def numberout():
        return str(input.numberin())

    @shinyreact.reactive_output
    def checkboxout():
        return str(input.checkboxin())

    @shinyreact.reactive_output
    def radioout():
        return str(input.radioin())

    @shinyreact.reactive_output
    def selectout():
        return str(input.selectin())

    @shinyreact.reactive_output
    def sliderout():
        return str(input.sliderin())

    @shinyreact.reactive_output
    def dateout():
        return str(input.datein())

    @shinyreact.reactive_output
    @reactive.event(input.buttonin, ignore_init=True)
    def buttonout():
        return str(input.buttonin())

    @shinyreact.reactive_output
    def fileout():
        files = input.filein()
        if files is None:
            return None
        # Summarize file info from the client
        summaries = []
        for f in files:
            size_kb = round(f["size"] / 1024, 1)
            summaries.append(
                f"📄 {f['name']} ({size_kb} KB, {f['type'] or 'unknown type'})"
            )
        return "\n".join(summaries)

    @shinyreact.reactive_output
    def batchout():
        data = input.batchdata()
        if data is None:
            return "No data submitted yet."

        data["receivedAt"] = datetime.datetime.now().isoformat()

        return data


app = App(app_ui, server)

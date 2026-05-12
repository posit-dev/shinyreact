import shinymui
import shinyreact
from shiny import App, Inputs, Outputs, Session

app_ui = shinyreact.ui_output("main", extra_deps=[shinymui.dep()])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def main():
        name = input.name() or ""
        age = input.age() or 0
        clicks = input.btn1() or 0
        return shinyreact.Node(
            type="div",
            props={
                "style": {
                    "padding": "16px",
                    "fontFamily": "sans-serif",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "16px",
                    "maxWidth": "600px",
                }
            },
            children=[
                shinyreact.Node(type="h1", props={"children": "shinymui prototype"}),
                shinymui.button("Save with icon", input_id="btn1", start_icon="Save"),
                shinyreact.Node(type="div", props={"children": f"Button btn1 clicks: {clicks}"}),
                shinymui.slider(input_id="age", label="Age", default_value=25, min=0, max=100),
                shinyreact.Node(type="div", props={"children": f"Age value: {age}"}),
                shinymui.text_field(input_id="name", label="Your name", default_value="World"),
                shinyreact.Node(type="div", props={"children": f"Hello, {name}!"}),
            ],
        )


app = App(app_ui, server)

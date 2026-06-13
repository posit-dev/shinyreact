import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinymui as mui
import shinyreact
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo", extra_deps=[mui._dep()]),
        shinyreact.output_react("echo"),
        style=(
            "max-width:560px; margin:2rem auto; padding:0 1rem; "
            "display:flex; flex-direction:column; gap:1rem;"
        ),
    )
)


def server(input, output, session):
    @shinyreact.render_react
    def demo():
        return mui.card(
            mui.text_field("name", label="Name", placeholder="Your name…"),
            mui.slider("age", min=18, max=99, value=30),
            mui.switch("subscribe", label="Subscribe"),
            mui.checkbox("agree", label="I agree"),
            mui.select("role", ["Engineer", "Designer", "PM"], label="Role"),
            mui.button("save", "Save"),
            mui.dialog(
                "details",
                mui.alert("Dialog body content."),
                trigger_label="Details",
                title="Details",
            ),
            title="shinymui demo",
        )

    @shinyreact.render_react
    def echo():
        return mui.alert(
            f"Hi {input.name() or 'there'} — age {input.age()}, "
            f"role {input.role() or '—'}, saved {input.save()} times.",
            severity="success" if input.agree() else "info",
        )


app = App(app_ui, server)

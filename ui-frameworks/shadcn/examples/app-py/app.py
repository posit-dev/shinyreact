import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinyreact
import shinyshadcn as sc
from shiny import App, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo_card", extra_deps=[sc._dep()]),
        style="max-width:520px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    @shinyreact.render_react
    def demo_card():
        name = input.my_input() if "my_input" in input else ""
        clicks = input.my_btn() if "my_btn" in input else 0
        color = input.color_select() if "color_select" in input else "blue"
        brightness = input.brightness() if "brightness" in input else 50
        agreed = input.agree() if "agree" in input else False

        greeting = f"Hello, {name}!" if name else "Type your name above."
        status_variant = "destructive" if not agreed else "default"
        status_msg = (
            "You must agree to the terms."
            if not agreed
            else f"Welcome! Brightness: {brightness}%, Color: {color}"
        )

        return sc.card(
            sc.text_input("my_input", placeholder="Your name…", label="Name"),
            sc.select(
                "color_select",
                choices=["blue", "green", "red", "purple"],
                selected="blue",
                label="Favorite color",
            ),
            sc.slider(
                "brightness", min=0, max=100, step=5, value=50, label="Brightness"
            ),
            sc.separator(),
            sc.switch("dark_mode", label="Dark mode"),
            sc.checkbox("agree", label="I agree to the terms"),
            sc.separator(),
            sc.button("my_btn", "Submit"),
            sc.separator(),
            sc.alert(status_msg, variant=status_variant),
            ui.div(
                sc.badge(greeting),
                sc.badge(f"clicked {clicks}×", variant="secondary"),
                class_="flex gap-2 flex-wrap",
            ),
            title="shadcn demo",
        )


app = App(app_ui, server)

"""Toast demo — server pushes notifications to the client (message-handler pattern)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pkg-py" / "src"))

import shinyreact
import shinyshadcn as sc
from shiny import App, reactive, ui

app_ui = shinyreact.page_react(
    ui.div(
        shinyreact.output_react("demo", extra_deps=[sc._dep()]),
        style="max-width:480px; margin:2rem auto; padding:0 1rem;",
    )
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.notify_btn, ignore_init=True)
    async def _():
        await sc.toast(
            session,
            "Changes saved!",
            description="Your profile was updated successfully.",
            type="success",
        )

    @shinyreact.render_react
    def demo():
        clicks = input.notify_btn() if "notify_btn" in input else 0
        return sc.card(
            sc.toaster(),  # host — renders nothing until a toast is pushed
            sc.button("notify_btn", "Save changes"),
            sc.badge(f"saved {clicks}×", variant="secondary"),
            title="Toast (server push)",
        )


app = App(app_ui, server)

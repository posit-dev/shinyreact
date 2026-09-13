"""Two ways a *hosted* Shiny input widget quietly fails to appear or update.

Both are Shiny's own reactive-graph behavior, not shinyreact's, but the
`@render.ui` holder recipe walks you straight into them:

1. An `update_slider()` sent before the holder has rendered targets an id the
   client does not know yet, and is dropped — silently.
2. A holder that is not visible on first paint is *suspended*, so its render
   function never runs and the widget never appears at all.
"""

from shiny import reactive
from shiny.express import input, render, session, ui  # noqa: F401  # marks Express
from shinyreact import set_react_page

set_react_page()


# --- 1. An update that arrives before the widget exists is dropped ----------
#
# The holder stays empty until the test clicks "Render it", so `_at_startup`
# below is guaranteed to have run first.
@render.ui
def late_widget():
    if not input.show():
        return None
    return ui.input_slider("late_bins", "Late", min=1, max=50, value=9)


@reactive.effect
def _at_startup():
    # First flush, long before `late_bins` exists on the client. Goes nowhere.
    ui.update_slider("late_bins", value=30)


@reactive.effect
@reactive.event(input.bump, ignore_init=True)
def _after_it_exists():
    # The control: the very same call, once the widget is really there.
    ui.update_slider("late_bins", value=30)


# --- 2. A holder that starts hidden never computes --------------------------
#
# Both of these are mounted inside a `display: none` panel. Only the second
# one opts out of suspension, so only the second one ever renders.
@render.ui
def suspended_widget():
    return ui.input_slider("suspended_bins", "Suspended", min=1, max=50, value=9)


@render.ui
def unsuspended_widget():
    return ui.input_slider("unsuspended_bins", "Unsuspended", min=1, max=50, value=9)


session.output(suspend_when_hidden=False)(unsuspended_widget)

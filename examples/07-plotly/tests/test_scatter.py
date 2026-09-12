"""Pins both outputs: the JSON echo and the plotly widget.

Shiny's `local_server` fixture reads a `reactive_output` and a
`@render_plotly` widget the same way, so this example's central claim — a
traditional widget renderer needs no `*Output()` placeholder to produce its
value — is checkable without a browser. Run it from the app directory::

    pytest
"""

from __future__ import annotations

import pytest
from shiny.testserver import TestServerSession

# The app is a directory up from this `tests/` folder, so the `local_server`
# fixture (an already-started `test_server()` session) gets pointed at it.
pytestmark = pytest.mark.parametrize("local_server", ["../app.py"], indirect=True)


def test_greeting_counts_the_points(local_server: TestServerSession) -> None:
    local_server.set_inputs(num_points=50)
    assert local_server.get_output("greeting") == "Showing 50 random points"

    local_server.set_inputs(num_points=1)
    assert local_server.get_output("greeting") == "Showing 1 random points"


def test_scatter_renders_a_widget_with_no_placeholder(
    local_server: TestServerSession,
) -> None:
    local_server.set_inputs(num_points=50)
    widget = local_server.get_output("scatter").value

    # What shinywidgets puts on the wire: a widget reference, not a figure.
    # The client's `ShinyOutput` is what turns it into a plot.
    assert widget["widget_pkg"] == "plotly"
    assert widget["model_id"]


def test_neither_output_renders_before_the_first_message(
    local_server: TestServerSession,
) -> None:
    assert local_server.get_output("greeting").status == "silent"
    assert local_server.get_output("scatter").status == "silent"

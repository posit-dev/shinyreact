"""Pins both outputs: the JSON echo and the plotly widget.

`shiny.testserver.test_server()` reads a `reactive_output` and a
`@render_plotly` widget the same way, so this example's central claim — a
traditional widget renderer needs no `*Output()` placeholder to produce its
value — is checkable without a browser. Run it from the app directory::

    pytest
"""

from __future__ import annotations

from pathlib import Path

from shiny.testserver import test_server

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_greeting_counts_the_points() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(num_points=50)
        assert ts.get_output("greeting") == "Showing 50 random points"

        ts.set_inputs(num_points=1)
        assert ts.get_output("greeting") == "Showing 1 random points"


def test_scatter_renders_a_widget_with_no_placeholder() -> None:
    with test_server(APP) as ts:
        ts.set_inputs(num_points=50)
        widget = ts.get_output("scatter").value

        # What shinywidgets puts on the wire: a widget reference, not a figure.
        # The client's `ShinyOutput` is what turns it into a plot.
        assert widget["widget_pkg"] == "plotly"
        assert widget["model_id"]


def test_neither_output_renders_before_the_first_message() -> None:
    with test_server(APP) as ts:
        assert ts.get_output("greeting").status == "silent"
        assert ts.get_output("scatter").status == "silent"

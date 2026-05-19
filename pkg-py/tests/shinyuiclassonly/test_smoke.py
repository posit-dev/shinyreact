"""End-to-end smoke: build a UI tree and tagify it without errors."""

from __future__ import annotations

import shinyuiclassonly as sui
from shiny import ui as _sui


def test_full_tree_tagifies():
    tree = _sui.page_fluid(
        sui.card(
            sui.accordion(
                sui.accordion_panel(
                    "Settings",
                    sui.input_slider("n", "N", 1, 10, 5),
                    sui.input_select("c", "Col", {"a": "A"}),
                    sui.input_action_button("go", "Run"),
                ),
                sui.accordion_panel(
                    "Diagnostics",
                    sui.output_code("summary"),
                    sui.output_plot("plot", click=True, brush=True),
                ),
                id="acc",
                open="Settings",
            ),
            id="m",
            full_screen=False,
        ),
        title="smoke",
    )
    html = str(tree.tagify())
    # Verify a handful of pieces ended up in the rendered HTML.
    assert 'id="n"' in html
    assert 'id="c"' in html
    assert 'id="go"' in html
    assert 'id="summary"' in html
    assert 'id="plot"' in html
    assert "Settings" in html
    assert "Diagnostics" in html

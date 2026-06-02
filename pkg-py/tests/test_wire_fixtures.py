import json
from pathlib import Path

import shinyreact
from htmltools import HTML, TagList, tags
from shinyreact._spec import _ATTR_MAP

FIXTURES = Path(__file__).parent / "fixtures" / "wire_format"


def _wire(value: object) -> object:
    if isinstance(value, shinyreact.Node):
        return value.to_dict()
    from shinyreact._spec import serialize_ui

    payload, _deps = serialize_ui(value)
    return payload


def _cases() -> dict[str, object]:
    return {
        "react_node": shinyreact.Node(type="Card", props={"title": "Hi"}),
        "tag_child": shinyreact.Node(
            type="Card", children=[tags.span("hi", class_="x")]
        ),
        "text_child": shinyreact.Node(type="Card", children=["plain text", 42]),
        "html_child": shinyreact.Node(type="Card", children=[HTML("<b>x</b>")]),
        "mixed_tree": shinyreact.Node(
            type="Card",
            props={"title": "Hi"},
            children=[
                shinyreact.Node(type="Divider"),
                tags.span("hi", class_="x"),
                "text",
            ],
        ),
        "taglist_root": TagList(
            shinyreact.Node(type="Card"), tags.div("d", id="root2")
        ),
    }


def test_fixtures_match_committed() -> None:
    for name, value in _cases().items():
        expected = json.loads((FIXTURES / f"{name}.json").read_text())
        assert _wire(value) == expected, name


def test_attr_map_matches_committed() -> None:
    # The HTML-attribute -> React-prop name map must stay identical to R's
    # `.ATTR_MAP` (pkg-r/R/wire.R). Both sides assert against this committed
    # fixture so the two languages can't drift.
    expected = json.loads((FIXTURES / "attr_map.json").read_text())
    assert _ATTR_MAP == expected

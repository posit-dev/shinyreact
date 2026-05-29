import json
from pathlib import Path

import shinyreact

FIXTURES = Path(__file__).parent / "fixtures" / "wire_format"

CASES = {
    "single_element": shinyreact.Node(type="Card", props={"title": "Hello"}),
    "nested_tree": shinyreact.Node(
        type="Card",
        props={"title": "Hi"},
        children=[
            shinyreact.Node(type="Divider"),
            shinyreact.Node(type="Text", props={"value": "x"}),
        ],
    ),
    "empty_children": shinyreact.Node(type="Divider"),
    "multi_props": shinyreact.Node(
        type="TextInput",
        props={"input_id": "name", "label": "Name", "placeholder": "..."},
    ),
}


def _wire(value) -> dict:
    if isinstance(value, shinyreact.Node):
        return value.to_spec().to_dict()
    return value


def test_fixtures_match_committed() -> None:
    for name, value in CASES.items():
        expected = json.loads((FIXTURES / f"{name}.json").read_text())
        assert _wire(value) == expected, name

    # Raw passthrough value (not a Node/Spec).
    raw = {"key": "value", "count": 42}
    expected_raw = json.loads((FIXTURES / "raw_value.json").read_text())
    assert raw == expected_raw

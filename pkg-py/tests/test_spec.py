import pytest
from shinyjson._spec import Element, Node, Spec


def test_element_to_dict_no_children():
    elem = Element(type="Card", props={"title": "Hello"}, children=[])
    assert elem.to_dict() == {
        "type": "Card",
        "props": {"title": "Hello"},
        "children": [],
    }


def test_element_to_dict_with_children():
    elem = Element(type="Page", props={}, children=["card-1", "card-2"])
    assert elem.to_dict() == {
        "type": "Page",
        "props": {},
        "children": ["card-1", "card-2"],
    }


def test_element_default_children():
    elem = Element(type="Metric", props={"value": 42})
    assert elem.to_dict()["children"] == []


def test_spec_to_dict_single_element():
    spec = Spec(
        root="card",
        elements={"card": Element(type="Card", props={"title": "Hi"})},
    )
    assert spec.to_dict() == {
        "root": "card",
        "elements": {
            "card": {"type": "Card", "props": {"title": "Hi"}, "children": []}
        },
    }


def test_spec_to_dict_nested():
    spec = Spec(
        root="page",
        elements={
            "page": Element(type="Page", props={}, children=["card"]),
            "card": Element(type="Card", props={"title": "Hi"}),
        },
    )
    result = spec.to_dict()
    assert result["root"] == "page"
    assert result["elements"]["page"]["children"] == ["card"]
    assert result["elements"]["card"]["type"] == "Card"


def test_spec_invalid_root_raises():
    with pytest.raises(ValueError, match="root 'missing' not found in elements"):
        Spec(
            root="missing",
            elements={"card": Element(type="Card", props={"title": "Hi"})},
        )


# ---------------------------------------------------------------------------
# Node tests
# ---------------------------------------------------------------------------


def test_node_to_spec_single():
    node = Node(type="Card", props={"title": "Hi"})
    spec = node.to_spec()
    assert spec.root == "auto_001"
    assert spec.elements["auto_001"].type == "Card"
    assert spec.elements["auto_001"].props == {"title": "Hi"}
    assert spec.elements["auto_001"].children == []


def test_node_to_spec_nested():
    node = Node(
        type="Card",
        props={"title": "Hi"},
        children=[
            Node(type="TextInput", props={"input_id": "txtin"}),
            Node(type="Divider"),
            Node(type="OutputDisplay", props={"output_id": "txtout"}),
        ],
    )
    spec = node.to_spec()

    # Root is the Card (last to be assigned since children are walked first)
    root_elem = spec.elements[spec.root]
    assert root_elem.type == "Card"
    assert len(root_elem.children) == 3

    # Children are assigned keys in depth-first order
    child_types = [spec.elements[k].type for k in root_elem.children]
    assert child_types == ["TextInput", "Divider", "OutputDisplay"]


def test_node_to_spec_deeply_nested():
    node = Node(
        type="Page",
        props={},
        children=[
            Node(
                type="Card",
                props={"title": "Hi"},
                children=[
                    Node(type="Badge", props={"text": "#1"}),
                ],
            ),
        ],
    )
    spec = node.to_spec()
    assert len(spec.elements) == 3

    # Badge is deepest → auto_001, Card → auto_002, Page → auto_003
    root_elem = spec.elements[spec.root]
    assert root_elem.type == "Page"

    card_key = root_elem.children[0]
    card_elem = spec.elements[card_key]
    assert card_elem.type == "Card"

    badge_key = card_elem.children[0]
    badge_elem = spec.elements[badge_key]
    assert badge_elem.type == "Badge"
    assert badge_elem.props == {"text": "#1"}


def test_node_to_spec_produces_valid_spec_dict():
    """Node.to_spec().to_dict() produces valid @json-render/react format."""
    node = Node(
        type="Card",
        props={"title": "Hi"},
        children=[Node(type="Divider")],
    )
    result = node.to_spec().to_dict()
    assert "root" in result
    assert "elements" in result
    assert result["root"] in result["elements"]
    for elem in result["elements"].values():
        assert "type" in elem
        assert "props" in elem
        assert "children" in elem

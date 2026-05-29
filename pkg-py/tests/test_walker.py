from shinyreact import Node


def test_node_simple_react_node():
    node = Node(type="Card", props={"title": "Hi"})
    assert node.to_dict() == {
        "type": "react",
        "name": "Card",
        "props": {"title": "Hi"},
        "children": [],
    }


def test_node_string_child_becomes_text():
    node = Node(type="Card", props={}, children=["hello"])
    assert node.to_dict() == {
        "type": "react",
        "name": "Card",
        "props": {},
        "children": [{"type": "text", "value": "hello"}],
    }


def test_node_nested_react_children():
    node = Node(
        type="Page",
        props={},
        children=[Node(type="Card", props={"title": "Hi"})],
    )
    assert node.to_dict() == {
        "type": "react",
        "name": "Page",
        "props": {},
        "children": [
            {"type": "react", "name": "Card", "props": {"title": "Hi"}, "children": []}
        ],
    }


def test_node_numeric_child_becomes_text():
    assert Node(type="Card", props={}, children=[42]).to_dict()["children"] == [
        {"type": "text", "value": "42"}
    ]
    assert Node(type="Card", props={}, children=[3.14]).to_dict()["children"] == [
        {"type": "text", "value": "3.14"}
    ]

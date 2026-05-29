from htmltools import HTML, HTMLDependency, TagList, tags

from shinyreact import Node
from shinyreact._spec import serialize_ui


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


def test_tag_becomes_tag_node_with_translated_attrs():
    node = Node(type="Card", props={}, children=[
        tags.div("hi", tags.span("x", class_="hl"), class_="card", id="c1"),
    ])
    assert node.to_dict()["children"] == [
        {
            "type": "tag",
            "name": "div",
            "props": {"className": "card", "id": "c1"},
            "children": [
                {"type": "text", "value": "hi"},
                {
                    "type": "tag",
                    "name": "span",
                    "props": {"className": "hl"},
                    "children": [{"type": "text", "value": "x"}],
                },
            ],
        }
    ]


def test_input_tag_name_and_attributes_do_not_collide():
    node = Node(type="Form", props={}, children=[
        tags.input(type="text", name="email", tabindex="2", aria_label="Email"),
    ])
    child = node.to_dict()["children"][0]
    assert child["type"] == "tag"
    assert child["name"] == "input"
    assert child["props"] == {
        "type": "text",
        "name": "email",
        "tabIndex": "2",
        "aria-label": "Email",
    }

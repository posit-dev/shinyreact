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


def test_html_becomes_html_node():
    node = Node(type="Card", props={}, children=[HTML("<b>bold</b>")])
    assert node.to_dict()["children"] == [{"type": "html", "html": "<b>bold</b>"}]


def test_taglist_flattens_into_parent_children():
    node = Node(type="Card", props={}, children=[TagList("a", "b")])
    assert node.to_dict()["children"] == [
        {"type": "text", "value": "a"},
        {"type": "text", "value": "b"},
    ]


def test_none_child_is_skipped():
    node = Node(type="Card", props={}, children=["a", None, "b"])
    assert node.to_dict()["children"] == [
        {"type": "text", "value": "a"},
        {"type": "text", "value": "b"},
    ]


def test_dependencies_are_harvested_not_emitted():
    dep = HTMLDependency(name="d", version="1.0", source={"subdir": "/tmp"})
    node = Node(type="Card", props={}, children=[dep, "text"])
    payload, deps = serialize_ui(node)
    assert payload["children"] == [{"type": "text", "value": "text"}]
    assert deps == [dep]


def test_serialize_ui_single_node_unwrapped():
    payload, deps = serialize_ui(Node(type="Card"))
    assert payload["type"] == "react"
    assert deps == []


def test_serialize_ui_taglist_returns_list():
    payload, _ = serialize_ui(TagList(Node(type="A"), Node(type="B")))
    assert isinstance(payload, list)
    assert [n["name"] for n in payload] == ["A", "B"]


def test_generic_tagifiable_is_tagified_and_recursed():
    class Widget:
        def tagify(self):
            return tags.div("from widget", class_="w")

    node = Node(type="Card", props={}, children=[Widget()])
    assert node.to_dict()["children"] == [
        {
            "type": "tag",
            "name": "div",
            "props": {"className": "w"},
            "children": [{"type": "text", "value": "from widget"}],
        }
    ]


def test_nested_node_in_tag_in_node_folds_into_one_tree():
    node = Node(type="Card", props={}, children=[
        tags.div(Node(type="Chart", props={"data": [1, 2]})),
    ])
    assert node.to_dict()["children"] == [
        {
            "type": "tag",
            "name": "div",
            "props": {},
            "children": [
                {
                    "type": "react",
                    "name": "Chart",
                    "props": {"data": [1, 2]},
                    "children": [],
                }
            ],
        }
    ]

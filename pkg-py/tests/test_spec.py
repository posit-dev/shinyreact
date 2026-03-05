from shinyjson._spec import Element, Spec


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

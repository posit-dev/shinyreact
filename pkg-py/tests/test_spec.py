from shinyreact import Node


def test_node_is_exported():
    assert Node(type="Card").to_dict()["type"] == "react"


def test_spec_and_element_no_longer_exported():
    import shinyreact

    assert not hasattr(shinyreact, "Spec")
    assert not hasattr(shinyreact, "Element")

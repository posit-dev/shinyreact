import {{pkg}}


def test_{{stub}}_factory():
    node = {{pkg}}.{{stub}}("Click me", input_id="b1")
    assert node.type == "{{prefix}}:{{Stub}}"
    assert node.props["label"] == "Click me"
    assert node.props["input_id"] == "b1"

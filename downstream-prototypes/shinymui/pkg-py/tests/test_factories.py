import shinymui


def test_button_factory_basic():
    node = shinymui.button("Click me", input_id="my_btn")
    assert node.type == "mui:Button"
    assert node.props["label"] == "Click me"
    assert node.props["input_id"] == "my_btn"
    assert node.props["variant"] == "contained"  # default


def test_button_factory_slot_icons():
    node = shinymui.button("Save", input_id="b", start_icon="Save", end_icon="Send")
    assert node.props["start_icon"] == "Save"
    assert node.props["end_icon"] == "Send"


def test_text_field_factory():
    node = shinymui.text_field(
        input_id="name",
        label="Your name",
        default_value="Anonymous",
        helper_text="Required",
    )
    assert node.type == "mui:TextField"
    assert node.props["input_id"] == "name"
    assert node.props["label"] == "Your name"
    assert node.props["default_value"] == "Anonymous"
    assert node.props["helper_text"] == "Required"

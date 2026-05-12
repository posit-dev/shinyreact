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


def test_slider_factory():
    node = shinymui.slider(
        input_id="age",
        label="Age",
        default_value=25,
        min=0,
        max=100,
        step=1,
    )
    assert node.type == "mui:Slider"
    assert node.props["input_id"] == "age"
    assert node.props["default_value"] == 25
    assert node.props["min"] == 0
    assert node.props["max"] == 100
    assert node.props["step"] == 1


def test_card_factory_with_children():
    child = shinymui.button("X", input_id="x")
    node = shinymui.card("My title", child)
    assert node.type == "mui:Card"
    assert node.props["title"] == "My title"
    assert len(node.children) == 1
    assert node.children[0].type == "mui:Button"

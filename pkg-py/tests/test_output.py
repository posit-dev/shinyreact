from htmltools import HTMLDependency, Tag

from shinyjson._output import ui


def test_ui_returns_tag():
    result = ui("my-output")
    assert isinstance(result, Tag)


def test_ui_has_correct_id():
    result = ui("my-output")
    assert result.attrs.get("id") == "my-output"


def test_ui_has_shinyjson_class():
    result = ui("my-output")
    classes = result.attrs.get("class", "")
    assert "shinyjson-output" in classes


def test_ui_accepts_extra_deps():
    dep = HTMLDependency("test", "1.0.0", source={"subdir": "/tmp"}, script={"src": "t.js"})
    result = ui("my-output", extra_deps=[dep])
    assert isinstance(result, Tag)


def test_ui_no_extra_deps_by_default():
    result = ui("my-output")
    assert isinstance(result, Tag)

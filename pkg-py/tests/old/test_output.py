from htmltools import HTMLDependency, Tag
from shinyjsonold._output import ui_output


def test_ui_output_returns_tag():
    result = ui_output("my-output")
    assert isinstance(result, Tag)


def test_ui_output_has_correct_id():
    result = ui_output("my-output")
    assert result.attrs.get("id") == "my-output"


def test_ui_output_has_shinyjson_class():
    result = ui_output("my-output")
    classes = result.attrs.get("class", "")
    assert "shinyjson-output" in classes


def test_ui_output_accepts_extra_deps():
    dep = HTMLDependency(
        "test", "1.0.0", source={"subdir": "/tmp"}, script={"src": "t.js"}
    )
    result = ui_output("my-output", extra_deps=[dep])
    assert isinstance(result, Tag)


def test_ui_output_no_extra_deps_by_default():
    result = ui_output("my-output")
    assert isinstance(result, Tag)


def test_ui_output_script_has_defer():
    result = ui_output("my-output")
    deps = result.get_dependencies()
    shinyjson_dep = next(d for d in deps if d.name == "shinyjsonold")
    # The script dict should include defer=""
    assert shinyjson_dep.script is not None
    script = shinyjson_dep.script
    if isinstance(script, list):
        script = script[0]
    assert script.get("defer") == ""

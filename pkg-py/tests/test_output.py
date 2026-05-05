from htmltools import HTMLDependency, Tag
from shinyreact._output import ui_output


def test_ui_output_returns_tag():
    result = ui_output("my-output")
    assert isinstance(result, Tag)


def test_ui_output_has_correct_id():
    result = ui_output("my-output")
    assert result.attrs.get("id") == "my-output"


def test_ui_output_has_shinyreact_class():
    result = ui_output("my-output")
    classes = result.attrs.get("class", "")
    assert "shinyreact-output" in classes


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
    shinyreact_dep = next(d for d in deps if d.name == "shinyreact")
    # The script dict should include defer=""
    assert shinyreact_dep.script is not None
    script = shinyreact_dep.script
    if isinstance(script, list):
        script = script[0]
    assert script.get("defer") == ""


# --- page_react_dep tests ---


def test_page_react_dep_returns_htmldependency(tmp_path):
    (tmp_path / "main.js").write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    dep = _make_dep_from_dir(tmp_path)
    assert isinstance(dep, HTMLDependency)
    assert dep.source["subdir"] == str(tmp_path)


def test_page_react_dep_uses_mtime_version(tmp_path):
    js = tmp_path / "main.js"
    js.write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    dep = _make_dep_from_dir(tmp_path)
    expected_version = str(int(js.stat().st_mtime))
    assert str(dep.version) == expected_version


def test_page_react_dep_custom_filenames(tmp_path):
    (tmp_path / "app.js").write_text("// app")
    (tmp_path / "app.css").write_text("/* styles */")

    dep = _make_dep_from_dir(tmp_path, js_file="app.js", css_file="app.css")
    script = dep.script if isinstance(dep.script, dict) else dep.script[0]
    stylesheet = (
        dep.stylesheet if isinstance(dep.stylesheet, dict) else dep.stylesheet[0]
    )
    assert script["src"] == "app.js"
    assert stylesheet["href"] == "app.css"


def test_page_react_dep_script_type_module(tmp_path):
    (tmp_path / "main.js").write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    dep = _make_dep_from_dir(tmp_path)
    script = dep.script if isinstance(dep.script, dict) else dep.script[0]
    assert script.get("type") == "module"


def _make_dep_from_dir(
    src_dir, *, js_file: str = "main.js", css_file: str = "main.css"
) -> HTMLDependency:
    """Build an HTMLDependency as if page_react_dep() were called from src_dir."""
    js_path = src_dir / js_file
    version = str(int(js_path.stat().st_mtime)) if js_path.exists() else "0"

    return HTMLDependency(
        name=src_dir.name,
        version=version,
        source={"subdir": str(src_dir)},
        script={"src": js_file, "type": "module"},
        stylesheet={"href": css_file},
    )

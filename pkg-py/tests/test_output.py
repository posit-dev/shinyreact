from pathlib import Path

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
#
# page_react_dep resolves the caller's frame via inspect.stack(), so to test
# it we execute a tiny script from inside tmp_path and read back its result.


def _run_page_react_dep(
    tmp_path: Path,
    *,
    js_file: str = "main.js",
    css_file: str = "main.css",
) -> HTMLDependency:
    """Call page_react_dep() from a script located in tmp_path."""
    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from shinyreact._page import page_react_dep\n"
        f"dep = page_react_dep(js_file={js_file!r}, css_file={css_file!r})\n"
    )
    namespace: dict = {"__file__": str(app_file)}
    exec(compile(app_file.read_text(), str(app_file), "exec"), namespace)
    return namespace["dep"]


def test_page_react_dep_returns_htmldependency(tmp_path):
    (tmp_path / "main.js").write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    assert isinstance(dep, HTMLDependency)
    assert dep.source["subdir"] == str(tmp_path)
    assert dep.name == tmp_path.name


def test_page_react_dep_uses_mtime_version(tmp_path):
    js = tmp_path / "main.js"
    js.write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    expected_version = str(int(js.stat().st_mtime))
    assert str(dep.version) == expected_version


def test_page_react_dep_missing_js_falls_back_to_zero_version(tmp_path):
    """When the JS entry point doesn\'t exist yet, version is "0"."""
    dep = _run_page_react_dep(tmp_path)
    assert str(dep.version) == "0"


def test_page_react_dep_custom_filenames(tmp_path):
    (tmp_path / "app.js").write_text("// app")
    (tmp_path / "app.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path, js_file="app.js", css_file="app.css")
    script = dep.script if isinstance(dep.script, dict) else dep.script[0]
    stylesheet = (
        dep.stylesheet if isinstance(dep.stylesheet, dict) else dep.stylesheet[0]
    )
    assert script["src"] == "app.js"
    assert stylesheet["href"] == "app.css"


def test_page_react_dep_script_type_module(tmp_path):
    (tmp_path / "main.js").write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    script = dep.script if isinstance(dep.script, dict) else dep.script[0]
    assert script.get("type") == "module"

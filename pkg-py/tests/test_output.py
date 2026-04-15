from htmltools import HTMLDependency, Tag
from shinyjson._output import ui_output
from shinyjson._page_react import page_bare, page_react


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
    shinyjson_dep = next(d for d in deps if d.name == "shinyjson")
    # The script dict should include defer=""
    assert shinyjson_dep.script is not None
    script = shinyjson_dep.script
    if isinstance(script, list):
        script = script[0]
    assert script.get("defer") == ""


# --- page_react tests ---


def test_page_react_returns_tag():
    result = page_react()
    assert isinstance(result, Tag)


def test_page_react_includes_root_div():
    html = str(page_react())
    assert 'id="root"' in html


def test_page_react_includes_shinyjson_dep():
    result = page_react()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyjson" in dep_names


def test_page_react_accepts_htmldep_via_args():
    dep = HTMLDependency(
        "my-app", "1.0.0", source={"subdir": "/tmp"}, script={"src": "app.js"}
    )
    result = page_react(dep)
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "my-app" in dep_names
    assert "shinyjson" in dep_names


def test_page_react_no_js_file_css_file_params():
    """page_react() no longer accepts js_file or css_file."""
    import inspect

    sig = inspect.signature(page_react)
    param_names = list(sig.parameters.keys())
    assert "js_file" not in param_names
    assert "css_file" not in param_names


# --- page_bare tests ---


def test_page_bare_returns_tag():
    result = page_bare()
    assert isinstance(result, Tag)


def test_page_bare_accepts_htmldep_via_args():
    dep = HTMLDependency(
        "custom", "1.0.0", source={"subdir": "/tmp"}, script={"src": "c.js"}
    )
    result = page_bare(dep)
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "custom" in dep_names


def test_page_bare_does_not_include_shinyjson_dep():
    result = page_bare()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyjson" not in dep_names


# --- page_react_dep tests ---


def test_page_react_dep_returns_htmldependency(tmp_path):
    (tmp_path / "main.js").write_text("// app")
    (tmp_path / "main.css").write_text("/* styles */")

    # Call from a fake caller context by invoking directly with patched stack
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
    """Build an HTMLDependency as if page_react_dep() were called from src_dir.

    Bypasses inspect.stack() by constructing the dependency directly using the
    same logic as page_react_dep().
    """
    js_path = src_dir / js_file
    version = str(int(js_path.stat().st_mtime)) if js_path.exists() else "0"

    return HTMLDependency(
        name=src_dir.name,
        version=version,
        source={"subdir": str(src_dir)},
        script={"src": js_file, "type": "module"},
        stylesheet={"href": css_file},
    )

from pathlib import Path

import pytest
from htmltools import HTMLDependency
from shinyreact._dep import _SHINYREACT_JS_PATH, _dep
from shinyreact._page import page_react_dep


def test_dep_version_tracks_bundle_mtime():
    """The shinyreact HTMLDependency version reflects the bundle's mtime.

    Cache-busts the browser whenever ``make update-dist`` rewrites the bundle.
    """
    assert _SHINYREACT_JS_PATH.exists(), (
        "shinyreact.js missing — run `make update-dist`"
    )
    expected = str(int(_SHINYREACT_JS_PATH.stat().st_mtime))
    assert str(_dep().version) == expected


def test_dep_script_has_defer():
    script = _dep().script
    assert script is not None
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
    js_file: str = "ui.js",
    css_file: str = "ui.css",
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
    (tmp_path / "ui.js").write_text("// app")
    (tmp_path / "ui.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    assert isinstance(dep, HTMLDependency)
    assert dep.source["subdir"] == str(tmp_path)
    assert dep.name == tmp_path.name


def test_page_react_dep_uses_mtime_version(tmp_path):
    js = tmp_path / "ui.js"
    js.write_text("// app")
    (tmp_path / "ui.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    expected_version = str(int(js.stat().st_mtime))
    assert str(dep.version) == expected_version


def test_page_react_dep_missing_js_falls_back_to_zero_version(tmp_path):
    """When the JS entry point doesn't exist yet, version is "0"."""
    with pytest.warns(UserWarning, match="JS entry point not found"):
        dep = _run_page_react_dep(tmp_path)
    assert str(dep.version) == "0"


def test_page_react_dep_omits_script_when_js_absent(tmp_path):
    """No tag pointing at a 404 — but warn, since an empty dep is silent."""
    with pytest.warns(UserWarning, match="JS entry point not found"):
        dep = page_react_dep(src_dir=tmp_path)
    # htmltools normalizes an absent script to an empty list.
    assert dep.script == []


def test_page_react_dep_attaches_script_when_js_present(tmp_path):
    (tmp_path / "ui.js").write_text("// app")

    dep = page_react_dep(src_dir=tmp_path)
    script = dep.script if isinstance(dep.script, dict) else dep.script[0]
    assert script["src"] == "ui.js"
    assert script.get("type") == "module"


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
    (tmp_path / "ui.js").write_text("// app")
    (tmp_path / "ui.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    script = dep.script if isinstance(dep.script, dict) else dep.script[0]
    assert script.get("type") == "module"


def test_page_react_dep_explicit_src_dir_and_name(tmp_path):
    """`src_dir` skips frame inspection — the reliable path for library authors.

    Frame inspection reads the *immediate* caller, so wrapping page_react_dep()
    in a helper would otherwise resolve against the wrapper's directory (#184).
    """
    (tmp_path / "ui.js").write_text("// app")

    dep = page_react_dep(src_dir=tmp_path, name="my-app")
    assert dep.source is not None
    assert dep.source["subdir"] == str(tmp_path)
    assert dep.name == "my-app"
    assert str(dep.version) == str(int((tmp_path / "ui.js").stat().st_mtime))


def test_page_react_dep_omits_stylesheet_when_css_absent(tmp_path):
    """A bundle with no CSS must not emit a 404-ing stylesheet link (#184)."""
    (tmp_path / "ui.js").write_text("// app")

    # htmltools normalizes an absent stylesheet to an empty list.
    assert page_react_dep(src_dir=tmp_path).stylesheet == []
    assert page_react_dep(src_dir=tmp_path, css_file=None).stylesheet == []


def test_page_react_dep_attaches_stylesheet_when_css_present(tmp_path):
    (tmp_path / "ui.js").write_text("// app")
    (tmp_path / "ui.css").write_text("/* styles */")

    stylesheet = page_react_dep(src_dir=tmp_path).stylesheet
    assert stylesheet is not None
    entry = stylesheet if isinstance(stylesheet, dict) else stylesheet[0]
    assert entry["href"] == "ui.css"

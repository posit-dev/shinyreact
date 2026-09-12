import warnings
from pathlib import Path
from typing import cast

import pytest
import shinyreact._dep as _dep_mod
from htmltools import HTMLDependency
from htmltools._core import HTMLDependencySource, ScriptItem, StylesheetItem
from shinyreact._dep import _SHINYREACT_JS_PATH, _dep
from shinyreact._page import page_react_dep


# `HTMLDependency` normalizes `script=` / `stylesheet=` to a list and `source=`
# to one of two TypedDicts, but the attributes stay declared as the wider
# argument types. These narrow once here so the assertions below read as
# assertions rather than as type gymnastics.
def dep_source(dep: HTMLDependency) -> HTMLDependencySource:
    source = dep.source
    assert source is not None
    assert "subdir" in source, "a local dep, not an href one"
    return cast(HTMLDependencySource, source)


def first_script(dep: HTMLDependency) -> ScriptItem:
    script = dep.script
    assert script is not None
    return script[0] if isinstance(script, list) else script


def first_stylesheet(dep: HTMLDependency) -> StylesheetItem:
    stylesheet = dep.stylesheet
    assert stylesheet is not None
    return stylesheet[0] if isinstance(stylesheet, list) else stylesheet


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
    assert first_script(_dep()).get("defer") == ""


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
    assert dep_source(dep)["subdir"] == str(tmp_path)
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


def test_page_react_dep_missing_src_dir_raises(tmp_path):
    """A missing src_dir errors here, not as Starlette's mount failure later.

    Mirrors R's test-page-react-dep.R
    "page_react_dep() errors when src_dir does not exist".
    """
    missing = tmp_path / "not-built"
    with pytest.raises(NotADirectoryError, match="React asset directory not found"):
        page_react_dep(src_dir=missing)


def test_page_react_dep_missing_src_dir_message_names_the_path_and_the_fix(tmp_path):
    """The whole point of raising here is a message Starlette's cannot give."""
    missing = tmp_path / "not-built"
    with pytest.raises(NotADirectoryError) as excinfo:
        page_react_dep(src_dir=missing)
    message = str(excinfo.value)
    assert str(missing) in message
    assert "Build the bundle first" in message
    assert "src_dir" in message


def test_page_react_dep_missing_src_dir_beats_the_missing_js_warning(tmp_path):
    """No src_dir means no js_file either; the directory is the useful error.

    Without this ordering the author gets a warning about `ui.js` that sends
    them looking for a file inside a directory that isn't there.
    """
    missing = tmp_path / "not-built"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(NotADirectoryError):
            page_react_dep(src_dir=missing)


def test_page_react_dep_rejects_a_file_as_src_dir(tmp_path):
    """`is_dir()`, not `exists()` — a file path is just as unmountable."""
    not_a_dir = tmp_path / "ui.js"
    not_a_dir.write_text("// app")
    with pytest.raises(NotADirectoryError, match="React asset directory not found"):
        page_react_dep(src_dir=not_a_dir)


def test_page_react_dep_omits_script_when_js_absent(tmp_path):
    """No tag pointing at a 404 — but warn, since an empty dep is silent."""
    with pytest.warns(UserWarning, match="JS entry point not found"):
        dep = page_react_dep(src_dir=tmp_path)
    # htmltools normalizes an absent script to an empty list.
    assert dep.script == []


def test_page_react_dep_attaches_script_when_js_present(tmp_path):
    (tmp_path / "ui.js").write_text("// app")

    dep = page_react_dep(src_dir=tmp_path)
    script = first_script(dep)
    assert script["src"] == "ui.js"
    assert script.get("type") == "module"


def test_page_react_dep_custom_filenames(tmp_path):
    (tmp_path / "app.js").write_text("// app")
    (tmp_path / "app.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path, js_file="app.js", css_file="app.css")
    script = first_script(dep)
    stylesheet = first_stylesheet(dep)
    assert script["src"] == "app.js"
    assert stylesheet["href"] == "app.css"


def test_page_react_dep_script_type_module(tmp_path):
    (tmp_path / "ui.js").write_text("// app")
    (tmp_path / "ui.css").write_text("/* styles */")

    dep = _run_page_react_dep(tmp_path)
    script = first_script(dep)
    assert script.get("type") == "module"


def test_page_react_dep_explicit_src_dir_and_name(tmp_path):
    """`src_dir` skips frame inspection — the reliable path for library authors.

    Frame inspection reads the *immediate* caller, so wrapping page_react_dep()
    in a helper would otherwise resolve against the wrapper's directory (#184).
    """
    (tmp_path / "ui.js").write_text("// app")

    dep = page_react_dep(src_dir=tmp_path, name="my-app")
    assert dep_source(dep)["subdir"] == str(tmp_path)
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

    entry = first_stylesheet(page_react_dep(src_dir=tmp_path))
    assert entry["href"] == "ui.css"


def test_dep_stylesheet_attached_unconditionally() -> None:
    # No existence check on the CSS, unlike page_react_dep()'s. Mirrors R's
    # "shinyreact_dep() attaches the stylesheet unconditionally".
    dep = _dep()
    assert [s["href"] for s in cast("list[StylesheetItem]", dep.stylesheet)] == [
        "shinyreact.css"
    ]


def test_dep_version_falls_back_when_bundle_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Deliberate divergence: R falls back to packageVersion("shinyreact").
    # Mirrors R's "shinyreact_dep() version falls back to the package version".
    monkeypatch.setattr(_dep_mod, "_SHINYREACT_JS_PATH", Path("/nonexistent/x.js"))
    assert str(_dep().version) == "0.1.0"

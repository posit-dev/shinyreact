import json
import re
from pathlib import Path

from htmltools import HTMLDependency, TagList
from shiny.bookmark._restore_state import RestoreContext, RestoreInputSet
from shiny.bookmark._restore_state import restore_context as restore_context_cm
from shinyreact import page_react, ui_output
from shinyreact._bookmark import _read_restore_input_values, _restore_script_tag
from shinyreact._output import _dep, _dep_page
from shinyreact._page import _build_react_page_fn


def _render_dep_to_head(dep: HTMLDependency) -> str:
    """Render an HTMLDependency to the HTML it would inject into <head>."""
    rendered = TagList(dep).tagify().render()
    head_html = "".join(
        d.as_html_tags().get_html_string() for d in rendered["dependencies"]
    )
    return head_html + rendered["html"]


def test_read_restore_input_values_returns_underlying_dict() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello", "num": 42})
    assert _read_restore_input_values(ctx) == {"foo": "hello", "num": 42}


def test_read_restore_input_values_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    _read_restore_input_values(ctx)
    # No keys should be pending — we only inspected.
    assert ctx.input._pending == set()


def test_read_restore_input_values_empty() -> None:
    ctx = RestoreContext()
    # Default RestoreContext has empty RestoreInputSet
    assert _read_restore_input_values(ctx) == {}


def test_restore_script_tag_no_context_returns_none() -> None:
    # No active RestoreContext at all.
    assert _restore_script_tag() is None


def test_restore_script_tag_empty_input_returns_none() -> None:
    ctx = RestoreContext()  # default: empty RestoreInputSet
    with restore_context_cm(ctx):
        assert _restore_script_tag() is None


def test_restore_script_tag_emits_head_content_with_json() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello", "num": 42})
    with restore_context_cm(ctx):
        dep = _restore_script_tag()

    assert dep is not None
    assert isinstance(dep, HTMLDependency)
    head_html = _render_dep_to_head(dep)
    # The script body sets window.shinyreact._restore via JSON.parse.
    assert "window.shinyreact" in head_html
    assert "_restore" in head_html
    # Round-trip the embedded JSON: extract the JSON.parse('...') argument.
    match = re.search(r"JSON\.parse\('(.*)'\)", head_html)
    assert match is not None
    parsed = json.loads(match.group(1))
    assert parsed == {"foo": "hello", "num": 42}


def test_restore_script_tag_escapes_closing_script_tag() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "</script><script>alert(1)</script>"})
    with restore_context_cm(ctx):
        dep = _restore_script_tag()
    assert dep is not None
    head_html = _render_dep_to_head(dep)
    # The literal "</script>" sequence inside the JSON payload must be escaped
    # so the browser does not see it as ending the script. The escaping replaces
    # "</" with "<\/", so no unescaped "</script" appears INSIDE the JSON.parse call.
    # Allow only ONE actual </script> (the one closing our injected tag).
    assert head_html.count("</script>") == 1


def test_restore_script_tag_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        _restore_script_tag()
        # restore_input() inside the same context should still see "hello",
        # because _restore_script_tag did not mark "foo" as pending.
        from shiny.bookmark._restore_state import RestoreInputSet as _RIS  # noqa: F401
        from shiny.module import ResolvedId

        assert ctx.input.get(ResolvedId("foo")) == "hello"


def test_dep_returns_htmldependency_only_no_context() -> None:
    result = _dep()
    assert isinstance(result, HTMLDependency)
    assert result.name == "shinyreact"


def test_dep_returns_htmldependency_only_with_context() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        result = _dep()
    # _dep() never wraps — it is the per-output helper.
    assert isinstance(result, HTMLDependency)


def test_dep_page_no_context_returns_htmldependency() -> None:
    result = _dep_page()
    assert isinstance(result, HTMLDependency)
    assert result.name == "shinyreact"


def test_dep_page_empty_context_returns_htmldependency() -> None:
    ctx = RestoreContext()  # active=False, empty input
    with restore_context_cm(ctx):
        result = _dep_page()
    assert isinstance(result, HTMLDependency)


def test_dep_page_with_active_context_returns_taglist() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        result = _dep_page()
    assert isinstance(result, TagList)
    # First child is the bundle dep; second is the head_content restore script.
    assert any(isinstance(c, HTMLDependency) and c.name == "shinyreact" for c in result)


def _rendered_html(tag) -> str:
    rendered = tag.tagify().render()
    head_html = "".join(
        d.as_html_tags().get_html_string() for d in rendered["dependencies"]
    )
    return head_html + rendered["html"]


def test_page_react_emits_restore_script_when_bookmark_active() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"txt": "hello"})
    with restore_context_cm(ctx):
        html = _rendered_html(page_react(title="t"))
    assert "window.shinyreact._restore" in html
    assert '"txt"' in html
    assert '"hello"' in html


def test_page_react_no_restore_script_without_bookmark() -> None:
    html = _rendered_html(page_react(title="t"))
    assert "window.shinyreact._restore" not in html


def test_set_react_page_emits_restore_script_when_bookmark_active(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    page_fn = _build_react_page_fn(index)

    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"a": 1})
    with restore_context_cm(ctx):
        html = _rendered_html(page_fn())
    assert "window.shinyreact._restore" in html
    assert '"a"' in html


def test_set_react_page_no_restore_script_without_bookmark(tmp_path: Path) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    page_fn = _build_react_page_fn(index)
    html = _rendered_html(page_fn())
    assert "window.shinyreact._restore" not in html


def test_ui_output_does_not_emit_restore_script_when_bookmark_active() -> None:
    """ui_output uses _dep(), not _dep_page() — no restore script."""
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        html = _rendered_html(ui_output("main"))
    assert "window.shinyreact._restore" not in html

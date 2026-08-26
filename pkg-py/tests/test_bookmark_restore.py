import json
import re
from pathlib import Path

import pytest
from htmltools import HTMLDependency, TagList
from shiny.bookmark._restore_state import RestoreContext, RestoreInputSet
from shiny.bookmark._restore_state import restore_context as restore_context_cm
from shinyreact import page_react_html
from shinyreact._bookmark import _config_script_tag, _read_restore_input_values
from shinyreact._dep import _dep, _dep_page
from shinyreact._page import _build_react_page_fn
from shinyreact._protocol import PROTOCOL_VERSION


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


def _extract_config(head_html: str) -> dict[str, object]:
    """Parse the JSON payload of the ``#shinyreact-config`` script tag.

    Mirrors what the JS client does: locate the tag by id and ``JSON.parse``
    its text content. R port: ``extract_config()`` in
    ``pkg-r/tests/testthat/test-bookmark-escaping.R``.
    """
    match = re.search(
        r'<script[^>]*\bid="shinyreact-config"[^>]*>(.*?)</script>',
        head_html,
        re.DOTALL,
    )
    assert match is not None, head_html
    return json.loads(match.group(1))


def _extract_restore_payload(head_html: str) -> object:
    """The ``restore`` member of the ``#shinyreact-config`` payload."""
    config = _extract_config(head_html)
    assert "restore" in config, config
    return config["restore"]


def _config_html(values: dict[str, object]) -> str:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet(dict(values))
    with restore_context_cm(ctx):
        dep = _config_script_tag()
    return _render_dep_to_head(dep)


def test_config_script_tag_no_context_omits_restore() -> None:
    # No active RestoreContext at all: the tag is still emitted (it carries
    # the protocol version), but has no "restore" member.
    head_html = _render_dep_to_head(_config_script_tag())
    config = _extract_config(head_html)
    assert config == {"protocolVersion": PROTOCOL_VERSION}


def test_config_script_tag_empty_input_omits_restore() -> None:
    ctx = RestoreContext()  # default: empty RestoreInputSet
    with restore_context_cm(ctx):
        head_html = _render_dep_to_head(_config_script_tag())
    config = _extract_config(head_html)
    assert config == {"protocolVersion": PROTOCOL_VERSION}


def test_config_script_tag_emits_json_tag_with_restore() -> None:
    head_html = _config_html({"foo": "hello", "num": 42})
    assert 'type="application/json"' in head_html
    assert 'id="shinyreact-config"' in head_html
    config = _extract_config(head_html)
    assert config["protocolVersion"] == PROTOCOL_VERSION
    assert config["restore"] == {"foo": "hello", "num": 42}


def test_config_script_tag_values_with_quotes_are_safe() -> None:
    values = {"foo": "it's me", "bar": 'she said "hi"'}
    assert _extract_restore_payload(_config_html(values)) == values


def test_config_script_tag_values_with_control_chars_are_safe() -> None:
    values = {"text": "line1\nline2\twith\ttabs"}
    assert _extract_restore_payload(_config_html(values)) == values


def test_config_script_tag_line_separators_round_trip() -> None:
    # U+2028 / U+2029 were a hazard when the payload was a JS string literal
    # (issue #183). In the JSON script tag they are inert; this pins the
    # round-trip. Mirrors R's "config_script_tag round-trips U+2028 / U+2029".
    values = {"ls": "A\u2028B", "ps": "C\u2029D"}
    assert _extract_restore_payload(_config_html(values)) == values


def test_config_script_tag_handles_proto_keys_safely() -> None:
    # The client reads the tag with JSON.parse, which treats "__proto__" and
    # "constructor" as ordinary own properties (unlike a bare JS object
    # literal, where "__proto__" is the prototype setter).
    values = {"__proto__": "evil", "constructor": "x", "ok": 1}
    head_html = _config_html(values)
    assert _extract_restore_payload(head_html) == values
    # The wire format is a JSON script tag, not executable JS.
    assert "window.shinyreact._restore" not in head_html


def test_config_script_tag_escapes_closing_script_tag() -> None:
    values = {"foo": "</script><script>alert(1)</script>"}
    head_html = _config_html(values)
    # Every "<" in the payload is emitted as the JSON escape \\u003c, so the only actual
    # </script> is the one closing our injected tag, and no <script> can be
    # smuggled in.
    assert head_html.count("</script>") == 1
    assert "<script>alert(1)" not in head_html
    assert _extract_restore_payload(head_html) == values


def test_config_script_tag_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        _config_script_tag()
        # restore_input() inside the same context should still see "hello",
        # because _config_script_tag did not mark "foo" as pending.
        from shiny.module import ResolvedId

        assert ctx.input.get(ResolvedId("foo")) == "hello"


def test_protocol_version_matches_js_and_r() -> None:
    # PROTOCOL_VERSION is one contract declared in three languages; this
    # parity test pins all three to the same string. Mirrors R's
    # "protocol version matches the JS and Python declarations".
    repo_root = Path(__file__).resolve().parents[2]
    js_src = repo_root / "pkg-js" / "src" / "shiny-react" / "config.ts"
    r_src = repo_root / "pkg-r" / "R" / "protocol.R"
    if not js_src.exists() or not r_src.exists():
        pytest.skip("monorepo sources not available (installed-package run)")
    js_match = re.search(r'PROTOCOL_VERSION = "([^"]+)"', js_src.read_text())
    r_match = re.search(r'\.protocol_version <- "([^"]+)"', r_src.read_text())
    assert js_match is not None
    assert r_match is not None
    assert js_match.group(1) == PROTOCOL_VERSION
    assert r_match.group(1) == PROTOCOL_VERSION


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


def test_dep_page_no_context_includes_config_tag() -> None:
    result = _dep_page()
    assert isinstance(result, TagList)
    assert any(isinstance(c, HTMLDependency) and c.name == "shinyreact" for c in result)
    config = _extract_config(_rendered_html(result))
    assert config == {"protocolVersion": PROTOCOL_VERSION}


def test_dep_page_with_active_context_includes_restore() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        result = _dep_page()
    assert isinstance(result, TagList)
    assert any(isinstance(c, HTMLDependency) and c.name == "shinyreact" for c in result)
    config = _extract_config(_rendered_html(result))
    assert config["restore"] == {"foo": "hello"}


def _rendered_html(tag) -> str:
    rendered = tag.tagify().render()
    head_html = "".join(
        d.as_html_tags().get_html_string() for d in rendered["dependencies"]
    )
    return head_html + rendered["html"]


def test_page_react_html_emits_restore_when_bookmark_active(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")

    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"txt": "hello"})
    with restore_context_cm(ctx):
        html = _rendered_html(page_react_html(index))
    assert _extract_restore_payload(html) == {"txt": "hello"}


def test_page_react_html_config_without_bookmark_has_no_restore(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    html = _rendered_html(page_react_html(index))
    config = _extract_config(html)
    assert config == {"protocolVersion": PROTOCOL_VERSION}


def test_set_react_page_emits_restore_when_bookmark_active(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    page_fn = _build_react_page_fn(index)

    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"a": 1})
    with restore_context_cm(ctx):
        html = _rendered_html(page_fn())
    assert _extract_restore_payload(html) == {"a": 1}


def test_set_react_page_config_without_bookmark_has_no_restore(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    page_fn = _build_react_page_fn(index)
    html = _rendered_html(page_fn())
    config = _extract_config(html)
    assert config == {"protocolVersion": PROTOCOL_VERSION}

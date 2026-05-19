from __future__ import annotations

import pytest
from htmltools import tags
from shinyuiclassonly._base import UiComponent


class _Dummy(UiComponent):
    """Minimal concrete subclass for testing."""

    def tagify(self):
        return tags.div("dummy")


def test_uicomponent_is_abstract():
    with pytest.raises(TypeError):
        UiComponent()  # type: ignore[abstract]


def test_uicomponent_concrete_subclass_constructs():
    c = _Dummy()
    assert c.tagify().name == "div"


def test_uicomponent_html_dependencies_default_empty():
    assert _Dummy.html_dependencies == ()


def test_uicomponent_has_no_session_attribute():
    """shinyuiclassonly drops all session machinery."""
    c = _Dummy()
    assert not hasattr(c, "_session")
    assert not hasattr(c, "_require_session")
    assert not hasattr(c, "_read_input")


def test_uicomponent_does_not_support_context_manager_protocol():
    """Subclasses without AllowsChildren are not context managers."""
    c = _Dummy()
    with pytest.raises(TypeError, match=r"context manager protocol"):
        with c:  # noqa: B017
            pass

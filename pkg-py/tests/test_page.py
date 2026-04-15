from htmltools import Tag
from shinyjson._page_react import page_bare, page_react


def test_page_bare_returns_tag():
    result = page_bare()
    assert isinstance(result, Tag)


def test_page_bare_with_title():
    result = page_bare(title="Test Page")
    rendered = str(result.tagify())
    assert "Test Page" in rendered


def test_page_bare_no_shinyjson_dep():
    result = page_bare()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyjson" not in dep_names


def test_page_react_returns_tag():
    result = page_react()
    assert isinstance(result, Tag)


def test_page_react_has_root_div():
    result = page_react()
    rendered = str(result.tagify())
    assert 'id="root"' in rendered


def test_page_react_includes_shinyjson_dep():
    result = page_react()
    deps = result.get_dependencies()
    dep_names = [d.name for d in deps]
    assert "shinyjson" in dep_names


def test_page_react_includes_js_file():
    result = page_react(js_file="app.js")
    rendered = str(result.tagify())
    assert 'src="app.js"' in rendered


def test_page_react_includes_css_file():
    result = page_react(css_file="app.css")
    rendered = str(result.tagify())
    assert 'href="app.css"' in rendered


def test_page_react_default_files():
    result = page_react()
    rendered = str(result.tagify())
    assert 'src="main.js"' in rendered
    assert 'href="main.css"' in rendered

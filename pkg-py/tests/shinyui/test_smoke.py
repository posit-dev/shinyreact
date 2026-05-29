def test_package_importable():
    import shinyui  # noqa: F401


def test_mock_session_fixture(mock_session):
    from shiny.session import get_current_session

    assert get_current_session() is mock_session

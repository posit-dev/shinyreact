import pytest
from shinyjson._render import render
from shinyjson._spec import Element, Spec


class TestRenderTransform:
    """Test that render.transform() handles both Spec and raw JSON data."""

    @pytest.fixture
    def renderer(self):
        """Create a render instance for testing transform()."""

        @render
        def dummy():
            pass

        return dummy

    @pytest.mark.asyncio
    async def test_transform_spec(self, renderer):
        """Spec values are serialized via to_dict()."""
        spec = Spec(
            root="card",
            elements={"card": Element(type="Card", props={"title": "Hi"})},
        )
        result = await renderer.transform(spec)
        assert result == spec.to_dict()
        assert result["root"] == "card"
        assert "card" in result["elements"]

    @pytest.mark.asyncio
    async def test_transform_dict(self, renderer):
        """Dict values pass through unchanged for useShinyOutput()."""
        data = {"key": "value", "count": 42}
        result = await renderer.transform(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_transform_list(self, renderer):
        """List values pass through unchanged."""
        data = [1, 2, 3]
        result = await renderer.transform(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_transform_string(self, renderer):
        """String values pass through unchanged."""
        result = await renderer.transform("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_transform_number(self, renderer):
        """Numeric values pass through unchanged."""
        result = await renderer.transform(42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_transform_none(self, renderer):
        """None passes through unchanged."""
        result = await renderer.transform(None)
        assert result is None

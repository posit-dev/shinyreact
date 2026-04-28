import pytest
import shinyjson


@pytest.mark.asyncio
async def test_render_json_passes_dict_through() -> None:
    @shinyjson.render_json
    def my_data():
        return {"title": "Hello", "count": 42}

    result = await my_data.transform({"title": "Hello", "count": 42})
    assert result == {"title": "Hello", "count": 42}


@pytest.mark.asyncio
async def test_render_json_passes_primitives_through() -> None:
    @shinyjson.render_json
    def my_data():
        return 42

    assert await my_data.transform(42) == 42
    assert await my_data.transform("hello") == "hello"
    assert await my_data.transform(None) is None
    assert await my_data.transform([1, 2, 3]) == [1, 2, 3]

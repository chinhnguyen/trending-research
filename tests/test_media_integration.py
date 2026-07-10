import os

import pytest

from willbe_trends.config import Settings, get_settings
from willbe_trends.media.diagnostics import mark_image_probe_passed, run_image_generation_test


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY required for live image test")
async def test_openai_image_generation_live():
    get_settings.cache_clear()
    settings = Settings(openai_api_key=os.environ["OPENAI_API_KEY"])
    result = await run_image_generation_test(settings=settings)

    assert result.status == "generated", result.error
    assert result.url
    assert result.url.startswith("data:image/") or result.url.startswith("https://")

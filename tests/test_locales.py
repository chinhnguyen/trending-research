from willbe_trends.briefs.locales import (
    caption_for_locale,
    locale_candidates,
    resolve_preferred_locale,
    shell_why_now,
)
from willbe_trends.models.briefs import BriefCaption


def test_locale_candidates_vietnam_region():
    assert locale_candidates("Vietnam") == ["vi", "en"]
    assert locale_candidates("Ho Chi Minh City") == ["vi", "en"]


def test_locale_candidates_preferred_overrides():
    assert locale_candidates("global", "vi") == ["vi", "en"]
    assert resolve_preferred_locale("global", "vi") == "vi"


def test_caption_for_locale_prefers_vietnamese():
    captions = [
        BriefCaption(locale="en", caption="English caption"),
        BriefCaption(locale="vi", caption="Chú thích tiếng Việt"),
    ]
    picked = caption_for_locale(captions, "vi")
    assert picked is not None
    assert picked.caption == "Chú thích tiếng Việt"


def test_shell_why_now_vietnamese():
    assert "Chọn nền tảng" in shell_why_now("vi")

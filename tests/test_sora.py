from willbe_trends.media.openai_sora import _seconds_for_duration, _size_for_aspect


def test_size_for_aspect_defaults_vertical():
    assert _size_for_aspect("9:16") == "720x1280"


def test_seconds_for_duration_snaps_to_supported_values():
    assert _seconds_for_duration(7) == "8"
    assert _seconds_for_duration(11) == "12"

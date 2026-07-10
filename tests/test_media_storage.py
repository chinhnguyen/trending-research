from willbe_trends.media.storage import media_public_url, persist_generated_image, persist_generated_video


def test_persist_data_url_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr("willbe_trends.media.storage.MEDIA_DIR", tmp_path)
    # 1x1 png
    b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    url = persist_generated_image(f"data:image/png;base64,{b64}")
    assert url is not None
    assert url.startswith("/api/media/")
    filename = url.removeprefix("/api/media/")
    assert (tmp_path / filename).is_file()


def test_media_public_url():
    assert media_public_url("abc.png") == "/api/media/abc.png"


def test_persist_generated_video_writes_mp4(tmp_path, monkeypatch):
    monkeypatch.setattr("willbe_trends.media.storage.MEDIA_DIR", tmp_path)
    url = persist_generated_video(b"fake-mp4-bytes")
    assert url is not None
    assert url.endswith(".mp4")
    filename = url.removeprefix("/api/media/")
    assert (tmp_path / filename).read_bytes() == b"fake-mp4-bytes"

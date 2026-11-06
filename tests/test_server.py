from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from gif2grid_mcp.render import RenderError, render
from gif2grid_mcp.server import gif_to_grid


@pytest.fixture()
def animated_gif(tmp_path: Path) -> Path:
    """A small animated GIF written on the fly, so tests need no fixtures."""
    frames = []
    for i in range(8):
        image = Image.new("RGB", (40, 30), (i * 30, 60, 120))
        frames.append(image)
    target = tmp_path / "motion.gif"
    frames[0].save(
        target,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
    )
    return target


def test_tool_returns_image_and_summary(animated_gif: Path) -> None:
    content = gif_to_grid(str(animated_gif))
    assert len(content) == 2
    assert content[0].type == "image"
    assert content[0].mime_type == "image/png"
    summary = json.loads(content[1].text)
    assert summary["frame_count"] == 9 or summary["frame_count"] == 8
    assert summary["grid"]["width"] > 0


def test_frame_count_is_respected(animated_gif: Path) -> None:
    content = gif_to_grid(str(animated_gif), frames=4)
    summary = json.loads(content[1].text)
    assert summary["frame_count"] == 4
    assert len(summary["frame_timestamps_ms"]) == 4


def test_missing_file_returns_text_error(tmp_path: Path) -> None:
    content = gif_to_grid(str(tmp_path / "nope.gif"))
    assert len(content) == 1
    assert content[0].type == "text"
    assert "no such file" in content[0].text


def test_url_download_is_used(monkeypatch, animated_gif: Path, tmp_path: Path) -> None:
    payload = animated_gif.read_bytes()

    class FakeResponse(io.BytesIO):
        headers = {"Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda url, timeout=30: FakeResponse(payload)
    )
    content = gif_to_grid("https://example.invalid/motion.gif", frames=3)
    assert content[0].type == "image"
    summary = json.loads(content[1].text)
    assert summary["frame_count"] == 3


def test_default_parameters_work(animated_gif: Path) -> None:
    result = render(str(animated_gif))
    assert result.frame_count >= 1
    assert result.grid_width >= 32


def test_scale_bounds(animated_gif: Path) -> None:
    with pytest.raises(RenderError):
        render(str(animated_gif), scale=8)


def test_empty_source_rejected() -> None:
    with pytest.raises(RenderError):
        render("   ")


def test_non_image_file_reports_error(tmp_path: Path) -> None:
    bogus = tmp_path / "notes.gif"
    bogus.write_text("this is not an image")
    with pytest.raises(RenderError):
        render(str(bogus))

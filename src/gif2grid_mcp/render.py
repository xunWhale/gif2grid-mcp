"""Fetch the input, sample it, and describe what came back."""

from __future__ import annotations

import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gif2grid import contact_sheet, extract_frames

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_FRAMES = 64
MAX_SCALE = 1024


class RenderError(Exception):
    """A failure the caller can act on, with a message worth showing a user."""


@dataclass(frozen=True)
class RenderResult:
    """A rendered contact sheet plus the facts an agent needs to describe it."""

    image: object
    frame_count: int
    frame_timestamps_ms: list[int]
    grid_width: int
    grid_height: int
    source_name: str


def _download(url: str, directory: Path) -> Path:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > MAX_DOWNLOAD_BYTES:
                raise RenderError(
                    f"refusing to download {url}: {int(length)} bytes exceeds "
                    f"the {MAX_DOWNLOAD_BYTES} byte limit"
                )
            payload = response.read(MAX_DOWNLOAD_BYTES + 1)
    except RenderError:
        raise
    except Exception as exc:
        raise RenderError(f"could not download {url}: {exc}") from exc

    if len(payload) > MAX_DOWNLOAD_BYTES:
        raise RenderError(f"refusing to download {url}: file is too large")

    target = directory / "download"
    target.write_bytes(payload)
    return target


def render(source, frames=9, cols=None, scale=320, labels=True):
    """Sample ``source`` and lay the frames out as one labelled image."""
    if not source or not source.strip():
        raise RenderError("source is empty; pass a local path or an http(s) URL")
    if not 1 <= frames <= MAX_FRAMES:
        raise RenderError(f"frames must be between 1 and {MAX_FRAMES}, got {frames}")
    if not 32 <= scale <= MAX_SCALE:
        raise RenderError(f"scale must be between 32 and {MAX_SCALE}, got {scale}")
    if cols is not None and not 1 <= cols <= MAX_FRAMES:
        raise RenderError(f"cols must be between 1 and {MAX_FRAMES}, got {cols}")

    with tempfile.TemporaryDirectory(prefix="gif2grid-mcp-") as tmp:
        workdir = Path(tmp)
        if source.startswith(("http://", "https://")):
            path = _download(source, workdir)
            name = source.rsplit("/", 1)[-1] or "download"
        else:
            path = Path(source).expanduser()
            name = path.name
            if not path.exists():
                raise RenderError(f"no such file: {source}")

        try:
            extracted = extract_frames(path, frames=frames)
        except FileNotFoundError as exc:
            raise RenderError(f"no such file: {source}") from exc
        except Exception as exc:
            raise RenderError(str(exc)) from exc

        if not extracted:
            raise RenderError(f"could not read any frames out of {name}")

        try:
            sheet = contact_sheet(extracted, cols=cols, labels=labels, scale=scale)
        except Exception as exc:
            raise RenderError(f"could not lay out the contact sheet: {exc}") from exc

        timestamps = [frame.timestamp_ms for frame in extracted]
        width, height = sheet.size

    return RenderResult(
        image=sheet,
        frame_count=len(extracted),
        frame_timestamps_ms=timestamps,
        grid_width=width,
        grid_height=height,
        source_name=name,
    )

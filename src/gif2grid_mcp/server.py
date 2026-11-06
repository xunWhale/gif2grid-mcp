"""The MCP surface: one tool, one job."""

from __future__ import annotations

import base64
import io
import json
from typing import Optional

from mcp.server.mcpserver import MCPServer
from mcp.types import ImageContent, TextContent

from gif2grid_mcp.render import RenderError, render

mcp = MCPServer(
    "gif2grid",
    instructions=(
        "Use gif_to_grid whenever an animated image or video matters to the answer. "
        "Most pipelines hand a vision model a single still frame, which erases motion; "
        "this tool returns one image containing several evenly spaced frames, each "
        "labelled with its frame number and millisecond offset."
    ),
)


def _encode_png(image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@mcp.tool()
def gif_to_grid(
    source: str,
    frames: int = 9,
    cols: Optional[int] = None,
    scale: int = 320,
    labels: bool = True,
) -> list:
    """Turn an animated image into one timestamped contact sheet.

    Args:
        source: Local path or http(s) URL to a GIF, WebP, APNG, or MP4.
        frames: How many frames to sample evenly across the timeline (1-64).
        cols: Fixed column count; omit to let the layout pick a near-square grid.
        scale: Maximum edge length of each cell in pixels (32-1024).
        labels: Draw the frame number and millisecond offset on each cell.

    Returns one PNG contact sheet plus a JSON summary of what was sampled.
    """
    try:
        result = render(source, frames=frames, cols=cols, scale=scale, labels=labels)
    except RenderError as exc:
        return [TextContent(type="text", text=f"gif_to_grid failed: {exc}")]

    summary = {
        "source": result.source_name,
        "frame_count": result.frame_count,
        "frame_timestamps_ms": result.frame_timestamps_ms,
        "grid": {"width": result.grid_width, "height": result.grid_height},
        "note": (
            "Each cell is one sampled frame, in timeline order. Timestamps are the "
            "source offset in milliseconds, so a gap between two cells is a gap in time."
        ),
    }
    return [
        ImageContent(type="image", data=_encode_png(result.image), mime_type="image/png"),
        TextContent(type="text", text=json.dumps(summary, ensure_ascii=False)),
    ]


def main() -> None:
    """Run the server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

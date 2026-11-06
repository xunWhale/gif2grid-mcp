# gif2grid-mcp

[![CI](https://github.com/xunWhale/gif2grid-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/xunWhale/gif2grid-mcp/actions/workflows/ci.yml)

An MCP server that turns an animated image into **one timestamped contact sheet**, so an agent can actually see what happens over time instead of receiving a single still frame.

## The problem

Almost every multimodal pipeline flattens an animation to one frame before the model sees it. The model then reasons confidently about a moment that may not even be representative.

This happened to me for real: a GIF of someone kicking a bottle arrived as one mid-stride frame, and the model described the clip as "a person sprinting forward." The action was gone, and the description was wrong.

Sending five separate images fixes the description but multiplies the token cost. One image with five labelled cells fixes it for the price of one image.

## Install

```bash
pip install "gif2grid-mcp @ git+https://github.com/xunWhale/gif2grid-mcp"
```

It depends on [`gif2grid`](https://github.com/xunWhale/gif2grid) for the sampling and layout.

## Wire it into your client

Claude Desktop / Cursor / any stdio MCP client:

```json
{
  "mcpServers": {
    "gif2grid": {
      "command": "gif2grid-mcp"
    }
  }
}
```

If the executable is not on `PATH`:

```json
{
  "mcpServers": {
    "gif2grid": {
      "command": "python",
      "args": ["-m", "gif2grid_mcp.server"]
    }
  }
}
```

## The tool

### `gif_to_grid`

| Argument | Type | Default | Meaning |
| :--- | :--- | :--- | :--- |
| `source` | string | required | Local path or `http(s)` URL to a GIF, WebP, APNG, or MP4 |
| `frames` | int | `9` | How many frames to sample evenly across the timeline (1–64) |
| `cols` | int or null | `null` | Fixed column count; omit for a near-square grid |
| `scale` | int | `320` | Maximum edge length per cell in pixels (32–1024) |
| `labels` | bool | `true` | Draw frame number and millisecond offset on each cell |

Returns two content blocks:

1. a PNG contact sheet (`image`), and
2. a JSON summary (`text`) with the frame count, every sampled timestamp in milliseconds, and the grid size.

Timestamps let the model talk about *when* something happened, not just *that* it happened. A gap between two cells is a gap in time.

MP4 input shells out to `ffmpeg`/`ffprobe`. When they are missing, the tool returns a text error saying so rather than failing silently.

## What it looks like

Input: [`demo` in the gif2grid repo](https://github.com/xunWhale/gif2grid#what-it-looks-like) — a real 10-frame animation. A single-frame pipeline hands the model this:

![single frame](https://raw.githubusercontent.com/xunWhale/gif2grid/main/demo/single-frame.png)

`gif_to_grid` hands it this, labelled with frame numbers and offsets:

![contact sheet](https://raw.githubusercontent.com/xunWhale/gif2grid/main/demo/motion-grid.png)

## Development

```bash
git clone https://github.com/xunWhale/gif2grid-mcp
cd gif2grid-mcp
python -m venv .venv && . .venv/bin/activate
pip install -e . pytest
pytest -q
python scripts/smoke.py   # real stdio round trip against a real GIF
```

`smoke-output.txt` and `pytest-output.txt` in this repo are checked in from an actual run, not written by hand.

## License

MIT

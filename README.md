# Claude Code Status Line

A customizable status line for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that displays model name, context window usage, and rate limit info.

## Styles

### `simple` — plain text, no bars

![simple](TODO)

### `gradient` — block bar with green-to-red color gradient

![gradient](TODO)

### `braille` — braille dot bar with color gradient

![braille](TODO)

### `ascii` — ASCII density ramp with color gradient

![ascii](TODO)

### `weather` — single emoji icon per metric

![weather](TODO)

## Requirements

- Claude Code >= v2.1.80

## Install

Download the script into `~/.claude/`:

```bash
curl -o ~/.claude/statusline.py https://raw.githubusercontent.com/liuyangc3/claude-code-status-line/main/statusline.py
chmod +x ~/.claude/statusline.py
```

## Configuration

Add the `statusLine` block to your settings file.

**Global** (`~/.claude/settings.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.py --style braille"
  }
}
```

**Project-level** (`.claude/settings.local.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.py --style weather"
  }
}
```

Replace `braille` / `weather` with any style: `simple`, `gradient`, `braille`, `ascii`, `weather`.

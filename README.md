# Claude Code Status Line

A customizable status line for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that displays model name, context window usage, and rate limit info.

## Styles

### `simple` — plain text, no bars

<img width="688" height="40" alt="simple" src="https://github.com/user-attachments/assets/9c354520-a970-4d71-b125-af3462ad7cab" />

### `gradient` — block bar with green-to-red color gradient

<img width="684" height="42" alt="gradient" src="https://github.com/user-attachments/assets/2cc401f2-4cf6-4637-a4b8-74a31ea3eff0" />

### `braille` — braille dot bar with color gradient

<img width="661" height="46" alt="braille" src="https://github.com/user-attachments/assets/158db7ed-06fc-4473-9b5f-2580b8810fde" />

### `ascii` — ASCII density ramp with color gradient

<img width="693" height="41" alt="ascii" src="https://github.com/user-attachments/assets/74270ffa-7c56-4cdb-9b42-13b0d0636a76" />

### `weather` — single emoji icon per metric

<img width="683" height="60" alt="weather" src="https://github.com/user-attachments/assets/69bf6da8-4590-4703-ac27-3c907d9056a3" />

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

### Flags

| Flag | Description |
|------|-------------|
| `--style <name>` | Choose a style: `simple`, `gradient`, `braille`, `ascii`, `weather` (default: `simple`) |
| `--token` | Show token usage (input/output) right-aligned on the status line |
| `--debug` | Write diagnostics to `statusline.log` next to the script |

### Example with token display

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.py --style braille --token"
  }
}
```

## References

- [Claude Code StatusLine Rate Limits](https://nyosegawa.com/posts/claude-code-statusline-rate-limits/#pattern-5%3A-braille-dots)

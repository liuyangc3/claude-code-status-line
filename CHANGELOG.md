# Changelog

## 0.2.1

### Fixed
- Fix status line not showing on first load when Claude Code sends null values in status JSON
- Use `or {}` / `or 0` instead of `.get()` defaults to handle JSON null values for `model`, `context_window`, `rate_limits`, and token counts

### Added
- `--git` flag to show current git branch (e.g. `⎇ main`) in pink after context info

### Changed
- Context display now shows token usage: `ctx ⣿⣿⣄ [23.4k/200k](30%)`
- Use ASCII pipe `|` separator instead of Unicode `│`

## 0.2.0

### Added
- `--token` flag to display input/output token usage right-aligned on the status line
- `--debug` flag to write diagnostics to `statusline.log`
- `TokenInfo` class for token formatting and terminal width detection
- Human-readable token numbers (e.g. `2.5k`, `1m`)
- Terminal width detection via `/dev/tty` for piped environments

### Changed
- Refactored all styles to inherit from `Style` base class instead of `SimpleStyle`
- Moved shared `_format`, `_parts`, and `render` methods into `Style` base class
- Removed duplicate `render` methods from `BrailleStyle`, `AsciiStyle`, `WeatherStyle`
- Context window defaults to 0% when `used_percentage` is missing

## 0.1.0

- Initial release with `simple`, `gradient`, `braille`, `ascii`, `weather` styles

#!/usr/bin/env python3

"""
 ▐▛███▜▌
▝▜█████▛▘
  ▘▘ ▝▝
"""

import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BLOCKS = ' ▏▎▍▌▋▊▉█'
RESET = '\033[0m'
DIM = '\033[2m'
ANSI_RE = re.compile(r'\033\[[0-9;]*m')


class Transcript:
    """Parse Claude Code transcript JSONL to extract tool usage."""

    @staticmethod
    def session_id(transcript_path):
        """Extract session ID (UUID) from transcript path."""
        if not transcript_path:
            return None
        return Path(transcript_path).stem

    @staticmethod
    def parse(transcript_path):
        """Return dict of {tool_name: count} from completed tool calls."""
        tool_map = {}   # id -> {name, target, status}
        if not transcript_path or not Path(transcript_path).exists():
            return {}
        try:
            with open(transcript_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = (entry.get('message') or {}).get('content')
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        btype = block.get('type')
                        if btype == 'tool_use' and block.get('id') and block.get('name'):
                            name = block['name']
                            if name in ('Task', 'TodoWrite', 'TaskCreate', 'TaskUpdate'):
                                continue
                            tool_map[block['id']] = {'name': name, 'status': 'running'}
                        elif btype == 'tool_result' and block.get('tool_use_id'):
                            tool = tool_map.get(block['tool_use_id'])
                            if tool:
                                tool['status'] = 'error' if block.get('is_error') else 'completed'
        except OSError:
            pass
        return tool_map

    @staticmethod
    def summarize(tool_map):
        """Return list of (name, count) sorted by count desc for completed tools."""
        counts = {}
        running = []
        for tool in tool_map.values():
            if tool['status'] == 'completed':
                counts[tool['name']] = counts.get(tool['name'], 0) + 1
            elif tool['status'] == 'running':
                running.append(tool['name'])
        completed = sorted(counts.items(), key=lambda x: -x[1])
        return running, completed


class TokenInfo:
    @staticmethod
    def visible_len(s):
        return len(ANSI_RE.sub('', s))

    @staticmethod
    def format_num(n):
        if n >= 1_000_000:
            v = n / 1_000_000
            return f'{v:.1f}m'.replace('.0m', 'm')
        if n >= 1_000:
            v = n / 1_000
            return f'{v:.1f}k'.replace('.0k', 'k')
        return str(n)

    @staticmethod
    def get_terminal_width():
        try:
            fd = os.open('/dev/tty', os.O_RDONLY)
            try:
                cols = os.get_terminal_size(fd).columns
            finally:
                os.close(fd)
        except (ValueError, OSError):
            cols = shutil.get_terminal_size().columns
        return cols

    @classmethod
    def format(cls, data):
        ctx = data.get('context_window') or {}
        in_tok = ctx.get('total_input_tokens') or 0
        out_tok = ctx.get('total_output_tokens') or 0
        return f'Token {DIM}|{RESET} {DIM}in:{RESET} {cls.format_num(in_tok)} {DIM}/ out:{RESET} {cls.format_num(out_tok)}'


class Style:
    def _format(self, label, pct, suffix=''):
        return f'{label} {suffix}({round(pct)}%)' if suffix else f'{label} {round(pct)}%'

    def _parts(self, data, show_git=False):
        model = (data.get('model') or {}).get('display_name', 'Unknow')
        parts = [model]

        cw = data.get('context_window') or {}
        ctx_pct = cw.get('used_percentage') or 0
        used = (cw.get('total_input_tokens') or 0) + (cw.get('total_output_tokens') or 0)
        size = cw.get('context_window_size') or 0
        ctx_suffix = f'[{TokenInfo.format_num(used)}/{TokenInfo.format_num(size)}]' if size else ''
        parts.append(self._format('ctx', ctx_pct, ctx_suffix))

        if show_git:
            branch = self._git_branch(data)
            if branch:
                parts.append(f'\033[38;2;255;105;180m⎇ {branch}{RESET}')

        five = ((data.get('rate_limits') or {}).get('five_hour') or {}).get('used_percentage')
        if five is not None:
            parts.append(self._format('5h', five))

        week = ((data.get('rate_limits') or {}).get('seven_day') or {}).get('used_percentage')
        if week is not None:
            parts.append(self._format('7d', week))

        return parts

    @staticmethod
    def _git_branch(data):
        cwd = data.get('cwd') or (data.get('workspace') or {}).get('current_dir')
        if not cwd:
            return None
        try:
            r = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=cwd, capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
        return None

    def render(self, data, debug=False, show_token=False, show_git=False, show_tool=False):
        parts = self._parts(data, show_git=show_git)
        left = f' {DIM}|{RESET} '.join(parts)
        if not show_token:
            print(left, end='')
        else:
            token = TokenInfo.format(data)
            width = TokenInfo.get_terminal_width()
            left_len = TokenInfo.visible_len(left)
            token_len = TokenInfo.visible_len(token)
            token_col = width - token_len + 1
            if debug:
                diag = f'width={width} left={left_len} token={token_len} col={token_col}\n'
                Path(__file__).parent.joinpath('statusline.log').write_text(diag)
            pad = width - left_len - token_len - 8  # reserve 8 chars for Claude Code's right-side UI
            if pad >= 2:
                print(left + ' ' * pad + token, end='')
            else:
                print(left + f' {DIM}|{RESET} ' + token, end='')

        if show_tool:
            transcript_path = data.get('transcript_path')
            tool_map = Transcript.parse(transcript_path)
            running, completed = Transcript.summarize(tool_map)
            tool_parts = []
            for name in running[-2:]:
                tool_parts.append(f'\033[33m◐{RESET} {name}')
            for name, count in completed:
                tool_parts.append(f'\033[32m✓{RESET} {name} {DIM}x{count}{RESET}')
            if tool_parts:
                print('\n' + f' {DIM}|{RESET} '.join(tool_parts), end='')

        if debug:
            session_id = Transcript.session_id(data.get('transcript_path'))
            if session_id:
                print(f'\n{DIM}session: {session_id}{RESET}', end='')


class SimpleStyle(Style):
    pass


class GradientStyle(Style):
    def _rgb_foreground(self, r, g, b):
        return f'\033[38;2;{r};{g};{b}m'

    def _bar(self, pct, width=10):
        pct = min(max(pct, 0), 100)
        filled = pct * width / 100
        full = int(filled)
        frac = int((filled - full) * 8)
        b = '█' * full
        if full < width:
            b += BLOCKS[frac]
            b += '░' * (width - full - 1)
        return b

    def _color_gradient(self, pct):
        """Green at 0% -> Yellow at 50% -> Red at 100%."""
        if pct < 50:
            red = int(pct * 5.1)
            return self._rgb_foreground(red, 200, 80)
        else:
            green = int(200 - (pct - 50) * 4)
            return self._rgb_foreground(255, max(green, 0), 60)

    def _format(self, label, pct, suffix=''):
        return f'{label} {self._color_gradient(pct)}{self._bar(pct)}{RESET} {suffix}({round(pct)}%)' if suffix else f'{label} {self._color_gradient(pct)}{self._bar(pct)} {round(pct)}%{RESET}'


class BrailleStyle(Style):
    BRAILLE = ' ⣀⣄⣤⣦⣶⣷⣿'

    def _rgb_foreground(self, r, g, b):
        return f'\033[38;2;{r};{g};{b}m'

    def _color_gradient(self, pct):
        if pct < 50:
            r = int(pct * 5.1)
            return self._rgb_foreground(r, 200, 80)
        else:
            g = int(200 - (pct - 50) * 4)
            return self._rgb_foreground(255, max(g, 0), 60)

    def _bar(self, pct, width=8):
        pct = min(max(pct, 0), 100)
        level = pct / 100
        bar = ''
        for i in range(width):
            seg_start = i / width
            seg_end = (i + 1) / width
            if level >= seg_end:
                bar += self.BRAILLE[7]
            elif level <= seg_start:
                bar += self.BRAILLE[0]
            else:
                frac = (level - seg_start) / (seg_end - seg_start)
                bar += self.BRAILLE[min(int(frac * 7), 7)]
        return bar

    def _format(self, label, pct, suffix=''):
        return f'{DIM}{label}{RESET} {self._color_gradient(pct)}{self._bar(pct)}{RESET} {suffix}({round(pct)}%)' if suffix else f'{DIM}{label}{RESET} {self._color_gradient(pct)}{self._bar(pct)}{RESET} {round(pct)}%'



class AsciiStyle(Style):
    RAMP = ' .:-=+*#'

    def _rgb_foreground(self, r, g, b):
        return f'\033[38;2;{r};{g};{b}m'

    def _color_gradient(self, pct):
        if pct < 50:
            r = int(pct * 5.1)
            return self._rgb_foreground(r, 200, 80)
        else:
            g = int(200 - (pct - 50) * 4)
            return self._rgb_foreground(255, max(g, 0), 60)

    def _bar(self, pct, width=10):
        pct = min(max(pct, 0), 100)
        level = pct / 100
        n = len(self.RAMP) - 1
        bar = ''
        for i in range(width):
            seg_start = i / width
            seg_end = (i + 1) / width
            if level >= seg_end:
                bar += self.RAMP[n]
            elif level <= seg_start:
                bar += self.RAMP[0]
            else:
                frac = (level - seg_start) / (seg_end - seg_start)
                bar += self.RAMP[min(int(frac * n), n)]
        return bar

    def _format(self, label, pct, suffix=''):
        return f'{DIM}{label}{RESET} {self._color_gradient(pct)}[{self._bar(pct)}]{RESET} {suffix}({round(pct)}%)' if suffix else f'{DIM}{label}{RESET} {self._color_gradient(pct)}[{self._bar(pct)}]{RESET} {round(pct)}%'


class WeatherStyle(Style):
    WEATHER = ('☀️', '🌤️', '⛅', '🌧️', '⛈️')

    def _icon(self, pct):
        if pct < 20:
            return self.WEATHER[0]
        elif pct < 40:
            return self.WEATHER[1]
        elif pct < 60:
            return self.WEATHER[2]
        elif pct < 80:
            return self.WEATHER[3]
        else:
            return self.WEATHER[4]

    def _format(self, label, pct, suffix=''):
        return f'{DIM}{label}{RESET} {self._icon(pct)} {suffix}({round(pct)}%)' if suffix else f'{DIM}{label}{RESET} {self._icon(pct)} {round(pct)}%'


STYLES = {
    'simple': SimpleStyle(),
    'gradient': GradientStyle(),
    'braille': BrailleStyle(),
    'ascii': AsciiStyle(),
    'weather': WeatherStyle(),
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--style', choices=STYLES, default='simple')
    parser.add_argument('--token', action='store_true', default=False)
    parser.add_argument('--git', action='store_true', default=False)
    parser.add_argument('--tool', action='store_true', default=False)
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    raw = sys.stdin.read()
    data = json.loads(raw)
    if args.debug:
        Path(__file__).parent.joinpath('statusline_input.log').write_text(raw)
    STYLES[args.style].render(data, debug=args.debug, show_token=args.token, show_git=args.git, show_tool=args.tool)

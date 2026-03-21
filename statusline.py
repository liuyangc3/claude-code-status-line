#!/usr/bin/env python3

"""
 ▐▛███▜▌
▝▜█████▛▘
  ▘▘ ▝▝
"""

import argparse, json, os, re, shutil, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BLOCKS = ' ▏▎▍▌▋▊▉█'
RESET = '\033[0m'
DIM = '\033[2m'
ANSI_RE = re.compile(r'\033\[[0-9;]*m')


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
        return f'Token {DIM}│{RESET} {DIM}in:{RESET} {cls.format_num(in_tok)} {DIM}/ out:{RESET} {cls.format_num(out_tok)}'


class Style:
    def _format(self, label, pct):
        return f'{label} {round(pct)}%'

    def _parts(self, data):
        model = (data.get('model') or {}).get('display_name', 'Unknow')
        parts = [model]

        ctx = (data.get('context_window') or {}).get('used_percentage') or 0
        parts.append(self._format('ctx', ctx))

        five = ((data.get('rate_limits') or {}).get('five_hour') or {}).get('used_percentage')
        if five is not None:
            parts.append(self._format('5h', five))

        week = ((data.get('rate_limits') or {}).get('seven_day') or {}).get('used_percentage')
        if week is not None:
            parts.append(self._format('7d', week))

        return parts

    def render(self, data, debug=False, show_token=False):
        parts = self._parts(data)
        left = f' {DIM}│{RESET} '.join(parts)
        if not show_token:
            print(left, end='')
            return
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
            print(left + f' {DIM}│{RESET} ' + token, end='')


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

    def _format(self, label, pct):
        return f'{label} {self._color_gradient(pct)}{self._bar(pct)} {round(pct)}%{RESET}'


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

    def _format(self, label, pct):
        return f'{DIM}{label}{RESET} {self._color_gradient(pct)}{self._bar(pct)}{RESET} {round(pct)}%'



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

    def _format(self, label, pct):
        return f'{DIM}{label}{RESET} {self._color_gradient(pct)}[{self._bar(pct)}]{RESET} {round(pct)}%'


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

    def _format(self, label, pct):
        return f'{DIM}{label}{RESET} {self._icon(pct)} {round(pct)}%'


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
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    raw = sys.stdin.read()
    data = json.loads(raw)
    STYLES[args.style].render(data, debug=args.debug, show_token=args.token)

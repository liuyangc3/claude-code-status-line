#!/usr/bin/env python3
import argparse, json, sys
from typing import Any, Protocol, runtime_checkable

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BLOCKS = ' ▏▎▍▌▋▊▉█'
RESET = '\033[0m'
DIM = '\033[2m'


@runtime_checkable
class Style(Protocol):
    def render(self, data: dict[str, Any]) -> None: ...


class SimpleStyle:
    def _format(self, label, pct):
        return f'{label} {round(pct)}%'

    def _parts(self, data):
        model = data.get('model', {}).get('display_name', 'Unknow')
        parts = [model]

        ctx = data.get('context_window', {}).get('used_percentage')
        if ctx is not None:
            parts.append(self._format('ctx', ctx))

        five = data.get('rate_limits', {}).get('five_hour', {}).get('used_percentage')
        if five is not None:
            parts.append(self._format('5h', five))

        week = data.get('rate_limits', {}).get('seven_day', {}).get('used_percentage')
        if week is not None:
            parts.append(self._format('7d', week))

        return parts

    def render(self, data):
        parts = self._parts(data)
        print(f'{DIM}│{RESET}'.join(f' {p} ' for p in parts), end='')


class GradientStyle(SimpleStyle):
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


class BrailleStyle(SimpleStyle):
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

    def render(self, data):
        parts = self._parts(data)
        print(f' {DIM}│{RESET} '.join(parts), end='')


class AsciiStyle(SimpleStyle):
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

    def render(self, data):
        parts = self._parts(data)
        print(f' {DIM}│{RESET} '.join(parts), end='')



class WeatherStyle(SimpleStyle):
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

    def render(self, data):
        parts = self._parts(data)
        print(f' {DIM}│{RESET} '.join(parts), end='')


STYLES: dict[str, Style] = {
    'simple': SimpleStyle(),
    'gradient': GradientStyle(),
    'braille': BrailleStyle(),
    'ascii': AsciiStyle(),
    'weather': WeatherStyle(),
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--style', choices=STYLES, default='simple')
    args = parser.parse_args()

    data = json.load(sys.stdin)
    STYLES[args.style].render(data)

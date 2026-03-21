from unittest.mock import patch
from io import StringIO
from statusline import SimpleStyle, GradientStyle, BrailleStyle, AsciiStyle, WeatherStyle

# ctx=10 (0-20), 5h=35 (20-40), 7d=50 (40-60)
SAMPLE_LOW = {
    "model": {"display_name": "Claude Sonnet 4.6"},
    "context_window": {"used_percentage": 10},
    "rate_limits": {
        "five_hour": {"used_percentage": 35},
        "seven_day": {"used_percentage": 50},
    },
}

# ctx=85 (80-100), 5h=95 (80-100), 7d=62 (60-80)
SAMPLE_HIGH = {
    "model": {"display_name": "Claude Haiku 4.5"},
    "context_window": {"used_percentage": 85},
    "rate_limits": {
        "five_hour": {"used_percentage": 95},
        "seven_day": {"used_percentage": 62},
    },
}

RANGES = [
    ("low", SAMPLE_LOW),
    ("high", SAMPLE_HIGH),
]


def capture(style, data):
    buf = StringIO()
    with patch("sys.stdout", buf):
        style.render(data)
    return buf.getvalue()


class TestSimple:
    def test_output(self):
        for range_name, data in RANGES:
            out = capture(SimpleStyle(), data)
            print(f"\nStyle: simple, Range: {range_name}")
            print(out)
            assert data["model"]["display_name"] in out
            assert "█" not in out
            assert "░" not in out

    def test_percentages(self):
        out = capture(SimpleStyle(), SAMPLE_LOW)
        assert "ctx 10%" in out
        assert "5h 35%" in out
        assert "7d 50%" in out


class TestGradient:
    def test_output(self):
        for range_name, data in RANGES:
            out = capture(GradientStyle(), data)
            print(f"\nStyle: gradient, Range: {range_name}")
            print(out)
            assert data["model"]["display_name"] in out
            assert "█" in out
            assert "\033[38;2;" in out


class TestBraille:
    def test_output(self):
        for range_name, data in RANGES:
            out = capture(BrailleStyle(), data)
            print(f"\nStyle: braille, Range: {range_name}")
            print(out)
            assert data["model"]["display_name"] in out
            assert "\033[38;2;" in out
            assert "█" not in out

    def test_braille_chars(self):
        style = BrailleStyle()
        bar_0 = style._bar(0)
        assert all(c == ' ' for c in bar_0)
        bar_100 = style._bar(100)
        assert all(c == '⣿' for c in bar_100)

    def test_partial_bar(self):
        style = BrailleStyle()
        bar_50 = style._bar(50)
        assert '⣿' in bar_50
        assert ' ' in bar_50


class TestAscii:
    def test_output(self):
        for range_name, data in RANGES:
            out = capture(AsciiStyle(), data)
            print(f"\nStyle: ascii, Range: {range_name}")
            print(out)
            assert data["model"]["display_name"] in out
            assert "[" in out and "]" in out
            assert "\033[38;2;" in out

    def test_bar_chars(self):
        style = AsciiStyle()
        bar_0 = style._bar(0)
        assert all(c == ' ' for c in bar_0)
        bar_100 = style._bar(100)
        assert all(c == '#' for c in bar_100)

    def test_partial_bar(self):
        style = AsciiStyle()
        bar_50 = style._bar(50)
        assert '#' in bar_50
        assert ' ' in bar_50


class TestWeather:
    def test_output(self):
        for range_name, data in RANGES:
            out = capture(WeatherStyle(), data)
            print(f"\nStyle: weather, Range: {range_name}")
            print(out)
            assert data["model"]["display_name"] in out

    def test_low_icons(self):
        out = capture(WeatherStyle(), SAMPLE_LOW)
        assert '☀️' in out
        assert '🌤️' in out
        assert '⛅' in out

    def test_high_icons(self):
        out = capture(WeatherStyle(), SAMPLE_HIGH)
        assert '⛈️' in out
        assert '🌧️' in out

    def test_icon_thresholds(self):
        style = WeatherStyle()
        assert style._icon(0) == '☀️'
        assert style._icon(19) == '☀️'
        assert style._icon(20) == '🌤️'
        assert style._icon(39) == '🌤️'
        assert style._icon(40) == '⛅'
        assert style._icon(59) == '⛅'
        assert style._icon(60) == '🌧️'
        assert style._icon(79) == '🌧️'
        assert style._icon(80) == '⛈️'
        assert style._icon(100) == '⛈️'

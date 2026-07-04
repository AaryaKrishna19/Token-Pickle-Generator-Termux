"""
ui.py
------
Tiny shared terminal UI kit for this project's scripts.
No external dependencies — pure ANSI escape codes, safe on Termux.

Automatically detects the terminal width so boxes/banners never wrap
awkwardly on narrow phone screens (this was a real bug: a fixed 60-char
box wrapped mid-line on a ~50-column Termux terminal).
"""

import shutil
import sys

APP_NAME = "Drive Token Generator"
CREDITS = "github.com/AaryaKrishna19"


class Ui:
    _use_color = sys.stdout.isatty()

    RESET = "\033[0m" if _use_color else ""
    BOLD = "\033[1m" if _use_color else ""
    DIM = "\033[2m" if _use_color else ""
    CYAN = "\033[36m" if _use_color else ""
    GREEN = "\033[32m" if _use_color else ""
    YELLOW = "\033[33m" if _use_color else ""
    RED = "\033[31m" if _use_color else ""
    MAGENTA = "\033[35m" if _use_color else ""
    GRAY = "\033[90m" if _use_color else ""

    MIN_WIDTH = 28
    MAX_WIDTH = 56

    @classmethod
    def width(cls) -> int:
        """Terminal width clamped to a sane range, so the box never wraps
        on narrow phone terminals but also doesn't look silly stretched
        across a wide desktop terminal."""
        cols = shutil.get_terminal_size(fallback=(40, 20)).columns
        return max(cls.MIN_WIDTH, min(cols - 2, cls.MAX_WIDTH))

    @classmethod
    def _center(cls, text: str, width: int) -> str:
        if len(text) >= width:
            return text[:width]
        pad = width - len(text)
        left = pad // 2
        right = pad - left
        return " " * left + text + " " * right

    @classmethod
    def banner(cls, subtitle: str = ""):
        w = cls.width()
        line = "─" * w
        print(f"{cls.CYAN}╭{line}╮{cls.RESET}")
        print(f"{cls.CYAN}│{cls.RESET}{cls.BOLD}{cls._center(APP_NAME, w)}{cls.RESET}{cls.CYAN}│{cls.RESET}")
        if subtitle:
            print(f"{cls.CYAN}│{cls.DIM}{cls._center(subtitle, w)}{cls.RESET}{cls.CYAN}│{cls.RESET}")
        print(f"{cls.CYAN}╰{line}╯{cls.RESET}")

    @classmethod
    def footer(cls):
        w = cls.width()
        print(f"{cls.GRAY}{cls._center('by ' + CREDITS, w)}{cls.RESET}")

    @classmethod
    def step(cls, number: int, text: str):
        print(f"\n{cls.MAGENTA}{cls.BOLD}▸ Step {number}{cls.RESET}  {text}")

    @classmethod
    def ok(cls, text: str):
        print(f"{cls.GREEN}✔ {text}{cls.RESET}")

    @classmethod
    def info(cls, text: str):
        print(f"{cls.CYAN}ℹ {text}{cls.RESET}")

    @classmethod
    def warn(cls, text: str):
        print(f"{cls.YELLOW}⚠ {text}{cls.RESET}")

    @classmethod
    def error(cls, text: str):
        print(f"{cls.RED}✘ {text}{cls.RESET}", file=sys.stderr)

    @classmethod
    def rule(cls):
        print(f"{cls.DIM}{'·' * cls.width()}{cls.RESET}")

    @classmethod
    def kv(cls, key: str, value: str):
        """Key/value line that wraps the value onto the next line if the
        terminal is too narrow to fit both on one line."""
        w = cls.width()
        line = f"{key} {value}"
        if len(line) <= w:
            print(f"{cls.CYAN}ℹ {cls.RESET}{cls.BOLD}{key}{cls.RESET} {value}")
        else:
            print(f"{cls.CYAN}ℹ {cls.RESET}{cls.BOLD}{key}{cls.RESET}")
            print(f"  {cls.DIM}{value}{cls.RESET}")

    @classmethod
    def url_block(cls, url: str):
        """Prints a long URL clearly. URLs are usually wider than any phone
        screen, so this doesn't try to box it — it just terminal-wraps
        naturally, with a subtle marker line to show where it starts/ends."""
        w = cls.width()
        print(f"{cls.YELLOW}{'┈' * w}{cls.RESET}")
        print(f"{cls.YELLOW}{url}{cls.RESET}")
        print(f"{cls.YELLOW}{'┈' * w}{cls.RESET}")

    @classmethod
    def prompt(cls, text: str) -> str:
        return input(f"{cls.BOLD}› {text}{cls.RESET}").strip()

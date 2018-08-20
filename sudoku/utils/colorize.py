from enum import Enum
from typing import AnyStr


class Color(Enum):
    BOLD = '1'
    CYAN = '0;36'
    GREEN = '0;32'
    RED = '0;31'
    YELLOW = '0;33'


def bold(text: AnyStr) -> AnyStr:
    return colorize(text, Color.BOLD)


def cyan(text: AnyStr) -> AnyStr:
    return colorize(text, Color.CYAN)


def green(text: AnyStr) -> AnyStr:
    return colorize(text, Color.GREEN)


def red(text: AnyStr) -> AnyStr:
    return colorize(text, Color.RED)


def yellow(text: AnyStr) -> AnyStr:
    return colorize(text, Color.YELLOW)


def colorize(text: AnyStr, color: Color) -> AnyStr:
    return f'\033[{color.value}m{text}\033[0m'

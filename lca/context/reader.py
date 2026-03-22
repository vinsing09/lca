from pathlib import Path
import sys


class ReaderError(Exception):
    pass


def read_file(path: Path) -> str:
    if not path.exists():
        raise ReaderError(f"File not found: {path}")
    if not path.is_file():
        raise ReaderError(f"Not a file: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ReaderError(f"File is not valid UTF-8: {path}")


def read_stdin() -> str:
    if sys.stdin.isatty():
        raise ReaderError("No input piped to stdin (stdin is a tty)")
    return sys.stdin.read()


def read_code_string(code: str) -> str:
    if not code or not code.strip():
        raise ReaderError("Code string is empty or whitespace")
    return code

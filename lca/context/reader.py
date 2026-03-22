import sys
from pathlib import Path


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


def read_function(path: Path, fn_name: str) -> tuple[str, str, int, int]:
    """Read a single named function from path.

    Returns (text, language, start_char, end_char) where
    full_source[start_char:end_char] == text.

    Raises ReaderError if the file cannot be read, the language is unsupported,
    or the function is not found.
    """
    from lca.context.extractor import (
        ExtractionError,
        detect_language,
        extract_function_with_offsets,
    )

    source = read_file(path)
    try:
        language = detect_language(path)
    except ExtractionError as exc:
        raise ReaderError(str(exc)) from exc
    try:
        text, start_char, end_char = extract_function_with_offsets(source, fn_name, language)
    except ExtractionError:
        raise ReaderError(
            f"Function '{fn_name}' not found in {path}. Check the name and try again."
        )
    return text, language, start_char, end_char

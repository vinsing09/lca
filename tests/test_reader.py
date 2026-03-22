import io
import sys
from pathlib import Path

import pytest

from lca.context.reader import ReaderError, read_code_string, read_file, read_stdin


def test_read_file_missing(tmp_path):
    with pytest.raises(ReaderError, match="not found"):
        read_file(tmp_path / "nope.py")


def test_read_file_not_a_file(tmp_path):
    with pytest.raises(ReaderError, match="Not a file"):
        read_file(tmp_path)  # directory, not a file


def test_read_file_binary(tmp_path):
    f = tmp_path / "binary.bin"
    f.write_bytes(b"\xff\xfe" + "hello".encode("utf-16-le"))
    with pytest.raises(ReaderError, match="UTF-8"):
        read_file(f)


def test_read_file_ok(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("print('hi')\n", encoding="utf-8")
    assert read_file(f) == "print('hi')\n"


def test_read_stdin_tty(monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    with pytest.raises(ReaderError, match="tty"):
        read_stdin()


def test_read_stdin_piped(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello from pipe"))
    result = read_stdin()
    assert result == "hello from pipe"


def test_read_code_string_empty():
    with pytest.raises(ReaderError, match="empty"):
        read_code_string("")


def test_read_code_string_whitespace():
    with pytest.raises(ReaderError, match="empty"):
        read_code_string("   \n\t  ")


def test_read_code_string_ok():
    assert read_code_string("x = 1") == "x = 1"

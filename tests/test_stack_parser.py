"""Unit tests for lca.context.stack_parser."""

from pathlib import Path

import pytest

from lca.context.stack_parser import find_function_at_line, parse_error

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# parse_error — format handling
# ---------------------------------------------------------------------------

def test_python_format_with_quotes():
    text = 'File "src/payment.py", line 67, in apply_tax'
    file_path, fn, line = parse_error(text)
    assert file_path == "src/payment.py"
    assert fn == "apply_tax"
    assert line == 67


def test_python_format_without_quotes():
    text = "File src/payment.py, line 67, in apply_tax"
    file_path, fn, line = parse_error(text)
    assert file_path == "src/payment.py"
    assert fn == "apply_tax"
    assert line == 67


def test_javascript_format():
    text = "    at apply_tax (src/payment.js:67:12)"
    file_path, fn, line = parse_error(text)
    assert file_path == "src/payment.js"
    assert fn == "apply_tax"
    assert line == 67


def test_go_format():
    text = "src/payment.go:67 +0x1a2"
    file_path, fn, line = parse_error(text)
    assert file_path == "src/payment.go"
    assert line == 67
    # func name may be None without preceding context line; just check file/line


def test_go_format_with_function_context():
    text = "main.apply_tax(...)\n\tsrc/payment.go:67 +0x1a2"
    file_path, fn, line = parse_error(text)
    assert file_path == "src/payment.go"
    assert fn == "apply_tax"
    assert line == 67


def test_generic_at_line_format():
    text = "apply_tax at line 67"
    file_path, fn, line = parse_error(text)
    assert fn == "apply_tax"
    assert line == 67
    assert file_path is None


def test_generic_in_error_format():
    text = "KeyError in apply_tax"
    file_path, fn, line = parse_error(text)
    assert fn == "apply_tax"
    assert file_path is None
    assert line is None


def test_generic_in_error_with_line():
    text = "TypeError in apply_tax at line 67"
    file_path, fn, line = parse_error(text)
    assert fn == "apply_tax"
    assert line == 67


# ---------------------------------------------------------------------------
# parse_error — returns LAST frame in multi-frame trace
# ---------------------------------------------------------------------------

def test_returns_last_frame_not_first():
    trace = (
        'Traceback (most recent call last):\n'
        '  File "src/outer.py", line 10, in outer_func\n'
        '    inner()\n'
        '  File "src/payment.py", line 67, in apply_tax\n'
        '    raise ValueError("invalid")\n'
        'ValueError: invalid amount\n'
    )
    file_path, fn, line = parse_error(trace)
    assert file_path == "src/payment.py"
    assert fn == "apply_tax"
    assert line == 67


def test_last_frame_not_first_js():
    trace = (
        "Error: invalid\n"
        "    at outerFn (src/outer.js:10:5)\n"
        "    at apply_tax (src/payment.js:67:12)\n"
    )
    file_path, fn, line = parse_error(trace)
    assert fn == "apply_tax"
    assert line == 67


# ---------------------------------------------------------------------------
# parse_error — no match cases
# ---------------------------------------------------------------------------

def test_plain_english_returns_none():
    result = parse_error("null pointer dereference")
    assert result == (None, None, None)


def test_plain_english_no_false_positive():
    result = parse_error("connection timed out after 30 seconds")
    assert result == (None, None, None)


def test_empty_string_returns_none():
    result = parse_error("")
    assert result == (None, None, None)


def test_exception_message_only_returns_none():
    # A bare exception message without a traceback or line reference
    result = parse_error("KeyError: 'missing_key'")
    assert result == (None, None, None)


# ---------------------------------------------------------------------------
# find_function_at_line — using sample.py fixture
# ---------------------------------------------------------------------------
# sample.py functions: greet(1), add(6), method(11), decorator(15), decorated(19)

def test_find_function_at_exact_start_line():
    # Line 1 is the start of greet — should return greet
    assert find_function_at_line(FIXTURES_DIR / "sample.py", 1) == "greet"


def test_find_function_at_start_line_of_add():
    assert find_function_at_line(FIXTURES_DIR / "sample.py", 6) == "add"


def test_find_function_inside_function():
    # Line 2 is inside greet (which starts at line 1)
    assert find_function_at_line(FIXTURES_DIR / "sample.py", 2) == "greet"


def test_find_function_correct_when_line_equals_start():
    # Line 19 is exactly the start of 'decorated'
    assert find_function_at_line(FIXTURES_DIR / "sample.py", 19) == "decorated"


def test_find_function_returns_none_for_line_zero():
    assert find_function_at_line(FIXTURES_DIR / "sample.py", 0) is None


def test_find_function_returns_none_beyond_end_of_file():
    assert find_function_at_line(FIXTURES_DIR / "sample.py", 9999) is None


def test_find_function_returns_none_for_missing_file(tmp_path):
    assert find_function_at_line(tmp_path / "missing.py", 5) is None


def test_find_function_returns_none_for_negative_line():
    assert find_function_at_line(FIXTURES_DIR / "sample.py", -1) is None

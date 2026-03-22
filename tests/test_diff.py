import io
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from lca.output.diff import (
    apply_edit,
    confirm_apply,
    has_changes,
    make_unified_diff,
    strip_model_fences,
)


# ---------------------------------------------------------------------------
# strip_model_fences
# ---------------------------------------------------------------------------

def test_strip_python_fence():
    text = "```python\ndef foo():\n    pass\n```"
    assert strip_model_fences(text) == "def foo():\n    pass"


def test_strip_plain_fence():
    text = "```\nx = 1\n```"
    assert strip_model_fences(text) == "x = 1"


def test_no_fence_unchanged():
    text = "def foo():\n    pass"
    assert strip_model_fences(text) == text


def test_partial_fence_not_stripped():
    text = "Here is code:\n```python\ndef foo(): pass\n```\nDone."
    assert strip_model_fences(text) == text


# ---------------------------------------------------------------------------
# make_unified_diff
# ---------------------------------------------------------------------------

def test_diff_identical_returns_empty():
    assert make_unified_diff("a = 1\n", "a = 1\n") == ""


def test_diff_different_returns_nonempty():
    diff = make_unified_diff("a = 1\n", "a = 2\n")
    assert diff != ""


def test_diff_contains_fromfile_header():
    diff = make_unified_diff("old\n", "new\n", filename="foo.py")
    assert "a/foo.py" in diff


def test_diff_contains_tofile_header():
    diff = make_unified_diff("old\n", "new\n", filename="foo.py")
    assert "b/foo.py" in diff


# ---------------------------------------------------------------------------
# has_changes
# ---------------------------------------------------------------------------

def test_has_changes_empty():
    assert has_changes("") is False


def test_has_changes_nonempty():
    assert has_changes("some diff") is True


# ---------------------------------------------------------------------------
# apply_edit
# ---------------------------------------------------------------------------

def test_apply_edit_writes_content(tmp_path):
    target = tmp_path / "out.py"
    apply_edit(target, "x = 42\n")
    assert target.read_text(encoding="utf-8") == "x = 42\n"


def test_apply_edit_overwrites_existing(tmp_path):
    target = tmp_path / "out.py"
    target.write_text("old content\n", encoding="utf-8")
    apply_edit(target, "new content\n")
    assert target.read_text(encoding="utf-8") == "new content\n"


def test_apply_edit_temp_in_same_directory(tmp_path, monkeypatch):
    """Verify the temp file is created in the target's parent directory."""
    target = tmp_path / "out.py"
    created_dirs: list[str] = []

    import tempfile as _tempfile
    real_mkstemp = _tempfile.mkstemp

    def spy_mkstemp(dir=None, **kwargs):
        created_dirs.append(str(dir))
        return real_mkstemp(dir=dir, **kwargs)

    monkeypatch.setattr("lca.output.diff.tempfile.mkstemp", spy_mkstemp)
    apply_edit(target, "content\n")
    assert created_dirs and created_dirs[0] == str(tmp_path)


# ---------------------------------------------------------------------------
# confirm_apply
# ---------------------------------------------------------------------------

def _console() -> Console:
    return Console(file=io.StringIO())


def test_confirm_apply_y_returns_true():
    with patch("builtins.input", return_value="y"):
        assert confirm_apply(_console()) is True


def test_confirm_apply_yes_returns_true():
    with patch("builtins.input", return_value="yes"):
        assert confirm_apply(_console()) is True


def test_confirm_apply_yes_case_insensitive():
    with patch("builtins.input", return_value="YES"):
        assert confirm_apply(_console()) is True


def test_confirm_apply_empty_returns_false():
    with patch("builtins.input", return_value=""):
        assert confirm_apply(_console()) is False


def test_confirm_apply_n_returns_false():
    with patch("builtins.input", return_value="n"):
        assert confirm_apply(_console()) is False


def test_confirm_apply_no_returns_false():
    with patch("builtins.input", return_value="no"):
        assert confirm_apply(_console()) is False


def test_confirm_apply_eoferror_returns_false():
    with patch("builtins.input", side_effect=EOFError):
        assert confirm_apply(_console()) is False

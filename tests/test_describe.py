"""Tests for `lca describe`. stream_chat is mocked — no model calls."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from lca.cli import app

runner = CliRunner()

_DESCRIBE_STREAM = "lca.commands.describe.stream_chat"

CANNED_DOC = (
    "## Overview\n"
    "This is a test codebase.\n\n"
    "## Modules\n"
    "### mod.py\n"
    "A utility module.\n"
    "Functions: foo, bar\n"
)


def _mock_stream(text: str):
    def _gen(**_kwargs):
        yield text
    return _gen


@pytest.fixture(autouse=True)
def _skip_setup(monkeypatch):
    monkeypatch.setattr("lca.cli._setup", lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# Helper: create a minimal Python file with named functions
# ---------------------------------------------------------------------------

def _make_py(tmp_path: Path, name: str, functions: list[str]) -> Path:
    f = tmp_path / name
    f.write_text(
        "\n\n".join(f"def {fn}(): pass" for fn in functions) + "\n",
        encoding="utf-8",
    )
    return f


# ---------------------------------------------------------------------------
# TestDescribeCommand
# ---------------------------------------------------------------------------

class TestDescribeCommand:
    def test_valid_directory_exits_0(self, tmp_path):
        _make_py(tmp_path, "mod.py", ["foo", "bar"])
        with patch(_DESCRIBE_STREAM, side_effect=_mock_stream(CANNED_DOC)):
            result = runner.invoke(app, ["describe", str(tmp_path)])
        assert result.exit_code == 0

    def test_output_contains_overview(self, tmp_path):
        _make_py(tmp_path, "mod.py", ["foo"])
        with patch(_DESCRIBE_STREAM, side_effect=_mock_stream(CANNED_DOC)):
            result = runner.invoke(app, ["describe", str(tmp_path)])
        assert "## Overview" in result.output

    def test_output_contains_modules(self, tmp_path):
        _make_py(tmp_path, "mod.py", ["foo"])
        with patch(_DESCRIBE_STREAM, side_effect=_mock_stream(CANNED_DOC)):
            result = runner.invoke(app, ["describe", str(tmp_path)])
        assert "## Modules" in result.output

    def test_output_flag_writes_file(self, tmp_path):
        _make_py(tmp_path, "mod.py", ["foo"])
        out_file = tmp_path / "ARCH.md"
        with patch(_DESCRIBE_STREAM, side_effect=_mock_stream(CANNED_DOC)):
            result = runner.invoke(app, ["describe", str(tmp_path), "-o", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        assert out_file.read_text(encoding="utf-8") == CANNED_DOC

    def test_output_flag_also_prints_to_terminal(self, tmp_path):
        _make_py(tmp_path, "mod.py", ["foo"])
        out_file = tmp_path / "ARCH.md"
        with patch(_DESCRIBE_STREAM, side_effect=_mock_stream(CANNED_DOC)):
            result = runner.invoke(app, ["describe", str(tmp_path), "-o", str(out_file)])
        # CANNED_DOC content AND the ✓ confirmation should both appear
        assert "## Overview" in result.output
        assert "Architecture saved to" in result.output

    def test_empty_directory_exits_0(self, tmp_path):
        # tmp_path has no supported-extension files
        result = runner.invoke(app, ["describe", str(tmp_path)])
        assert result.exit_code == 0

    def test_empty_directory_prints_no_supported_files(self, tmp_path):
        result = runner.invoke(app, ["describe", str(tmp_path)])
        assert "No supported files found" in result.output

    def test_many_functions_prints_warning(self, tmp_path):
        # Create a file with 201 functions — triggers the > 200 warning
        functions = [f"func_{i}" for i in range(201)]
        _make_py(tmp_path, "big.py", functions)
        with patch(_DESCRIBE_STREAM, side_effect=_mock_stream(CANNED_DOC)):
            result = runner.invoke(app, ["describe", str(tmp_path)])
        assert "Warning" in result.output
        assert "201" in result.output


# ---------------------------------------------------------------------------
# TestDescribeIndexing
# ---------------------------------------------------------------------------

class TestDescribeIndexing:
    def test_prompt_contains_file_name(self, tmp_path):
        _make_py(tmp_path, "mymod.py", ["alpha", "beta"])
        mock_fn = MagicMock(side_effect=_mock_stream(CANNED_DOC))
        with patch(_DESCRIBE_STREAM, mock_fn):
            runner.invoke(app, ["describe", str(tmp_path)])
        user_prompt = mock_fn.call_args.kwargs["user_prompt"]
        assert "mymod.py" in user_prompt

    def test_prompt_contains_function_names(self, tmp_path):
        _make_py(tmp_path, "mymod.py", ["alpha", "beta"])
        mock_fn = MagicMock(side_effect=_mock_stream(CANNED_DOC))
        with patch(_DESCRIBE_STREAM, mock_fn):
            runner.invoke(app, ["describe", str(tmp_path)])
        user_prompt = mock_fn.call_args.kwargs["user_prompt"]
        assert "alpha" in user_prompt
        assert "beta" in user_prompt

    def test_prompt_uses_relative_paths(self, tmp_path):
        _make_py(tmp_path, "mymod.py", ["foo"])
        mock_fn = MagicMock(side_effect=_mock_stream(CANNED_DOC))
        with patch(_DESCRIBE_STREAM, mock_fn):
            runner.invoke(app, ["describe", str(tmp_path)])
        user_prompt = mock_fn.call_args.kwargs["user_prompt"]
        # Relative path appears
        assert "mymod.py" in user_prompt
        # Absolute directory prefix does NOT appear
        assert str(tmp_path) not in user_prompt

    def test_prompt_contains_line_counts(self, tmp_path):
        _make_py(tmp_path, "mymod.py", ["foo"])
        mock_fn = MagicMock(side_effect=_mock_stream(CANNED_DOC))
        with patch(_DESCRIBE_STREAM, mock_fn):
            runner.invoke(app, ["describe", str(tmp_path)])
        user_prompt = mock_fn.call_args.kwargs["user_prompt"]
        assert "lines" in user_prompt

    def test_prompt_covers_multiple_files(self, tmp_path):
        _make_py(tmp_path, "alpha.py", ["a1"])
        _make_py(tmp_path, "beta.py", ["b1"])
        mock_fn = MagicMock(side_effect=_mock_stream(CANNED_DOC))
        with patch(_DESCRIBE_STREAM, mock_fn):
            runner.invoke(app, ["describe", str(tmp_path)])
        user_prompt = mock_fn.call_args.kwargs["user_prompt"]
        assert "alpha.py" in user_prompt
        assert "beta.py" in user_prompt

"""CLI integration tests for `lca find`. No real model calls — stream_chat is mocked."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lca.cli import app

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_FIND_STREAM = "lca.commands.find.stream_chat"


def _mock_stream(text: str):
    """Return a generator factory that yields text as a single chunk."""
    def _gen(**_kwargs):
        yield text
    return _gen


@pytest.fixture(autouse=True)
def _skip_setup(monkeypatch):
    monkeypatch.setattr("lca.cli._setup", lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestFindValidation:
    def test_no_file_no_dir_exits_2(self):
        result = runner.invoke(app, ["find", "loads config"])
        assert result.exit_code == 2

    def test_both_file_and_dir_exits_2(self, tmp_path):
        result = runner.invoke(app, [
            "find", "loads config",
            "-f", str(FIXTURES_DIR / "sample.py"),
            "-d", str(FIXTURES_DIR),
        ])
        assert result.exit_code == 2

    def test_nonexistent_file_exits_0_no_functions(self, tmp_path):
        result = runner.invoke(app, ["find", "loads config", "-f", str(tmp_path / "missing.py")])
        assert result.exit_code == 0
        assert "No functions found" in result.output


# ---------------------------------------------------------------------------
# Single-file mode
# ---------------------------------------------------------------------------

class TestFindSingleFile:
    def test_exits_0_with_match(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet"]')):
            result = runner.invoke(app, ["find", "greeting function", "-f", str(FIXTURES_DIR / "sample.py")])
        assert result.exit_code == 0

    def test_output_contains_matched_name(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet"]')):
            result = runner.invoke(app, ["find", "greeting function", "-f", str(FIXTURES_DIR / "sample.py")])
        assert "greet" in result.output

    def test_output_contains_double_colon(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet"]')):
            result = runner.invoke(app, ["find", "greeting function", "-f", str(FIXTURES_DIR / "sample.py")])
        assert "::" in result.output

    def test_output_contains_line_number(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet"]')):
            result = runner.invoke(app, ["find", "greeting function", "-f", str(FIXTURES_DIR / "sample.py")])
        assert "line" in result.output
        assert "1" in result.output  # greet is at line 1


# ---------------------------------------------------------------------------
# Directory mode
# ---------------------------------------------------------------------------

class TestFindDirectory:
    def test_exits_0_with_matches(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet"]')):
            result = runner.invoke(app, ["find", "greeting function", "-d", str(FIXTURES_DIR)])
        assert result.exit_code == 0

    def test_output_grouped_by_file(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet"]')):
            result = runner.invoke(app, ["find", "greeting function", "-d", str(FIXTURES_DIR)])
        # In directory mode the file path is printed on its own line
        assert "sample" in result.output
        assert "::" in result.output

    def test_output_contains_matched_name(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream('["greet", "add"]')):
            result = runner.invoke(app, ["find", "greeting or addition", "-d", str(FIXTURES_DIR)])
        assert "greet" in result.output
        assert "add" in result.output


# ---------------------------------------------------------------------------
# No-match cases
# ---------------------------------------------------------------------------

class TestFindNoMatches:
    def test_empty_array_prints_no_matches(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream("[]")):
            result = runner.invoke(app, ["find", "does not exist", "-f", str(FIXTURES_DIR / "sample.py")])
        assert result.exit_code == 0
        assert "No functions found" in result.output

    def test_empty_array_does_not_print_double_colon(self):
        with patch(_FIND_STREAM, side_effect=_mock_stream("[]")):
            result = runner.invoke(app, ["find", "does not exist", "-f", str(FIXTURES_DIR / "sample.py")])
        assert "::" not in result.output


# ---------------------------------------------------------------------------
# Fence stripping
# ---------------------------------------------------------------------------

class TestFindFenceStripping:
    def test_json_fences_are_stripped(self):
        fenced = '```json\n["greet"]\n```'
        with patch(_FIND_STREAM, side_effect=_mock_stream(fenced)):
            result = runner.invoke(app, ["find", "greeting function", "-f", str(FIXTURES_DIR / "sample.py")])
        assert result.exit_code == 0
        assert "greet" in result.output

    def test_plain_fences_are_stripped(self):
        fenced = '```\n["add"]\n```'
        with patch(_FIND_STREAM, side_effect=_mock_stream(fenced)):
            result = runner.invoke(app, ["find", "addition", "-f", str(FIXTURES_DIR / "sample.py")])
        assert result.exit_code == 0
        assert "add" in result.output

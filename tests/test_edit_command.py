from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lca.cli import app
from lca.llm.client import OllamaError

_EDIT_STREAM = "lca.commands.edit.stream_chat"
_EDIT_MODEL_CHECK = "lca.commands.edit.check_model_available"


@pytest.fixture(autouse=True)
def skip_setup(monkeypatch):
    monkeypatch.setattr("lca.cli._setup", lambda *a, **kw: None)


def _make_file(tmp_path: Path, lines: int, content: str | None = None) -> Path:
    f = tmp_path / "code.py"
    if content is not None:
        f.write_text(content, encoding="utf-8")
    else:
        f.write_text("\n".join(f"x = {i}" for i in range(lines)), encoding="utf-8")
    return f


def _mock_stream(text: str):
    """Return a side_effect factory yielding the given text as one chunk."""
    def _gen(**_kwargs):
        yield text
    return _gen


# ---------------------------------------------------------------------------
# TestEditMissingFile
# ---------------------------------------------------------------------------

class TestEditMissingFile:
    def test_no_file_flag_exits_2(self):
        runner = CliRunner()
        result = runner.invoke(app, ["edit", "add docstrings"])
        assert result.exit_code == 2

    def test_no_file_flag_mentions_file(self):
        runner = CliRunner()
        result = runner.invoke(app, ["edit", "add docstrings"])
        assert "-f" in result.output or "file" in result.output.lower()


# ---------------------------------------------------------------------------
# TestEditInputValidation
# ---------------------------------------------------------------------------

class TestEditInputValidation:
    def test_file_not_found_exits_2(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(app, ["edit", "add docstrings", "-f", str(tmp_path / "missing.py")])
        assert result.exit_code == 2

    def test_oversized_file_exits_3(self, tmp_path):
        f = _make_file(tmp_path, lines=151)
        runner = CliRunner()
        result = runner.invoke(app, ["edit", "add docstrings", "-f", str(f)])
        assert result.exit_code == 3

    def test_oversized_file_mentions_limit(self, tmp_path):
        f = _make_file(tmp_path, lines=151)
        runner = CliRunner()
        result = runner.invoke(app, ["edit", "add docstrings", "-f", str(f)])
        assert "150" in result.output

    def test_exactly_150_lines_not_exit_3(self, tmp_path):
        f = _make_file(tmp_path, lines=150)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream("\n".join(f"x = {i}" for i in range(150)))), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add docstrings", "-f", str(f)], input="n")
        assert result.exit_code != 3


# ---------------------------------------------------------------------------
# TestEditNoChanges
# ---------------------------------------------------------------------------

class TestEditNoChanges:
    def test_no_changes_exits_0(self, tmp_path):
        original = "x = 1\ny = 2\n"
        f = _make_file(tmp_path, lines=0, content=original)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(original)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add docstrings", "-f", str(f)])
        assert result.exit_code == 0

    def test_no_changes_output_mentions_no_changes(self, tmp_path):
        original = "x = 1\ny = 2\n"
        f = _make_file(tmp_path, lines=0, content=original)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(original)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add docstrings", "-f", str(f)])
        assert "no change" in result.output.lower()


# ---------------------------------------------------------------------------
# TestEditConfirmFlow
# ---------------------------------------------------------------------------

class TestEditConfirmFlow:
    _ORIGINAL = "x = 1\ny = 2\n"
    _EDITED = "# added comment\nx = 1\ny = 2\n"

    def test_confirm_n_exits_1(self, tmp_path):
        f = _make_file(tmp_path, lines=0, content=self._ORIGINAL)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(self._EDITED)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add a comment", "-f", str(f)], input="n\n")
        assert result.exit_code == 1

    def test_confirm_n_file_unchanged(self, tmp_path):
        f = _make_file(tmp_path, lines=0, content=self._ORIGINAL)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(self._EDITED)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            runner.invoke(app, ["edit", "add a comment", "-f", str(f)], input="n\n")
        assert f.read_text(encoding="utf-8") == self._ORIGINAL

    def test_confirm_y_exits_0(self, tmp_path):
        f = _make_file(tmp_path, lines=0, content=self._ORIGINAL)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(self._EDITED)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add a comment", "-f", str(f)], input="y\n")
        assert result.exit_code == 0

    def test_confirm_y_file_updated(self, tmp_path):
        f = _make_file(tmp_path, lines=0, content=self._ORIGINAL)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(self._EDITED)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            runner.invoke(app, ["edit", "add a comment", "-f", str(f)], input="y\n")
        assert f.read_text(encoding="utf-8") == self._EDITED


# ---------------------------------------------------------------------------
# TestEditOllamaError
# ---------------------------------------------------------------------------

class TestEditOllamaError:
    def test_ollama_error_exits_2(self, tmp_path):
        f = _make_file(tmp_path, lines=5)
        def _raise(**_kwargs):
            raise OllamaError("connection refused")
            yield  # make it a generator
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_raise), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add docstrings", "-f", str(f)])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# TestEditFenceStripping
# ---------------------------------------------------------------------------

class TestEditFenceStripping:
    _ORIGINAL = "x = 1\ny = 2\n"
    _INNER = "# stripped\nx = 1\ny = 2\n"
    _FENCED = f"```python\n{_INNER}```"

    def test_fenced_output_exits_0(self, tmp_path):
        f = _make_file(tmp_path, lines=0, content=self._ORIGINAL)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(self._FENCED)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["edit", "add a comment", "-f", str(f)], input="y\n")
        assert result.exit_code == 0

    def test_fenced_output_file_has_no_fences(self, tmp_path):
        f = _make_file(tmp_path, lines=0, content=self._ORIGINAL)
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream(self._FENCED)), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            runner.invoke(app, ["edit", "add a comment", "-f", str(f)], input="y\n")
        content = f.read_text(encoding="utf-8")
        assert "```" not in content

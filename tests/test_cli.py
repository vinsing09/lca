from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lca.cli import app
from lca.llm.client import OllamaError

runner = CliRunner()

# Targets to patch (resolved at import time inside command functions)
_EXPLAIN_STREAM = "lca.commands.explain.stream_chat"
_EXPLAIN_MODEL_CHECK = "lca.commands.explain.check_model_available"
_REVIEW_STREAM = "lca.commands.review.stream_chat"
_REVIEW_MODEL_CHECK = "lca.commands.review.check_model_available"


def _make_file(tmp_path: Path, lines: int, name: str = "code.py") -> Path:
    f = tmp_path / name
    f.write_text("\n".join(f"x = {i}" for i in range(lines)), encoding="utf-8")
    return f


def _mock_stream(text: str = "streamed output"):
    """Return a generator factory that yields a single chunk."""
    def _gen(**_kwargs):
        yield text
    return _gen


class TestVersion:
    def test_exits_0(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_output_contains_lca_and_version(self):
        result = runner.invoke(app, ["--version"])
        assert "lca" in result.output
        assert "0.1" in result.output


class TestEditStub:
    def test_exits_1(self):
        result = runner.invoke(app, ["edit"])
        assert result.exit_code == 1

    def test_output_mentions_phase_2(self):
        result = runner.invoke(app, ["edit"])
        assert "Phase 2" in result.output


class TestExplainInputValidation:
    def test_missing_file_exits_2(self, tmp_path):
        result = runner.invoke(app, ["explain", "-f", str(tmp_path / "missing.py")])
        assert result.exit_code == 2

    def test_oversized_file_exits_3(self, tmp_path):
        f = _make_file(tmp_path, lines=301)
        result = runner.invoke(app, ["explain", "-f", str(f)])
        assert result.exit_code == 3

    def test_oversized_file_error_mentions_limit(self, tmp_path):
        f = _make_file(tmp_path, lines=301)
        result = runner.invoke(app, ["explain", "-f", str(f)])
        assert "300" in result.output

    def test_valid_file_exits_0(self, tmp_path):
        f = _make_file(tmp_path, lines=5)
        with patch(_EXPLAIN_STREAM, side_effect=_mock_stream()), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["explain", "-f", str(f)])
        assert result.exit_code == 0

    def test_valid_file_output_contains_streamed_text(self, tmp_path):
        f = _make_file(tmp_path, lines=5)
        with patch(_EXPLAIN_STREAM, side_effect=_mock_stream("hello from model")), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["explain", "-f", str(f)])
        assert "hello from model" in result.output

    def test_code_snippet_exits_0(self, tmp_path):
        with patch(_EXPLAIN_STREAM, side_effect=_mock_stream()), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["explain", "x = 1 + 2"])
        assert result.exit_code == 0


class TestReviewInputValidation:
    def test_missing_file_exits_2(self, tmp_path):
        result = runner.invoke(app, ["review", "-f", str(tmp_path / "missing.py")])
        assert result.exit_code == 2

    def test_oversized_file_exits_3(self, tmp_path):
        f = _make_file(tmp_path, lines=301)
        result = runner.invoke(app, ["review", "-f", str(f)])
        assert result.exit_code == 3

    def test_valid_file_exits_0(self, tmp_path):
        f = _make_file(tmp_path, lines=5)
        with patch(_REVIEW_STREAM, side_effect=_mock_stream()), \
             patch(_REVIEW_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["review", "-f", str(f)])
        assert result.exit_code == 0


class TestOllamaErrors:
    def test_explain_ollama_error_exits_2(self, tmp_path):
        f = _make_file(tmp_path, lines=5)
        def _raise(**_kwargs):
            raise OllamaError("connection refused")
            yield  # make it a generator
        with patch(_EXPLAIN_STREAM, side_effect=_raise), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["explain", "-f", str(f)])
        assert result.exit_code == 2

    def test_review_ollama_error_exits_2(self, tmp_path):
        f = _make_file(tmp_path, lines=5)
        def _raise(**_kwargs):
            raise OllamaError("connection refused")
            yield
        with patch(_REVIEW_STREAM, side_effect=_raise), \
             patch(_REVIEW_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["review", "-f", str(f)])
        assert result.exit_code == 2

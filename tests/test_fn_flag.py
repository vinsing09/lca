"""Integration tests for the --fn flag across explain, review, and edit commands."""
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lca.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PY = FIXTURES / "sample.py"

_EXPLAIN_STREAM = "lca.commands.explain.stream_chat"
_EXPLAIN_MODEL_CHECK = "lca.commands.explain.check_model_available"
_REVIEW_STREAM = "lca.commands.review.stream_chat"
_REVIEW_MODEL_CHECK = "lca.commands.review.check_model_available"
_EDIT_STREAM = "lca.commands.edit.stream_chat"
_EDIT_MODEL_CHECK = "lca.commands.edit.check_model_available"


@pytest.fixture(autouse=True)
def skip_setup(monkeypatch):
    monkeypatch.setattr("lca.cli._setup", lambda *a, **kw: None)


def _captured_prompt():
    """Return a side_effect that captures the user_prompt kwarg and yields a chunk."""
    captured = {}

    def _gen(**kwargs):
        captured["user_prompt"] = kwargs.get("user_prompt", "")
        yield "result text"

    return _gen, captured


def _mock_stream(text: str = "result text"):
    def _gen(**_kwargs):
        yield text
    return _gen


# ---------------------------------------------------------------------------
# TestExplainFnFlag
# ---------------------------------------------------------------------------

class TestExplainFnFlag:
    def test_fn_valid_exits_0(self):
        runner = CliRunner()
        with patch(_EXPLAIN_STREAM, side_effect=_mock_stream()), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["explain", "--fn", "greet", "-f", str(SAMPLE_PY)])
        assert result.exit_code == 0

    def test_fn_prompt_contains_only_target_function(self):
        runner = CliRunner()
        gen, captured = _captured_prompt()
        with patch(_EXPLAIN_STREAM, side_effect=gen), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            runner.invoke(app, ["explain", "--fn", "greet", "-f", str(SAMPLE_PY)])
        prompt = captured.get("user_prompt", "")
        assert "greet" in prompt
        assert "def add" not in prompt

    def test_fn_nonexistent_exits_2(self):
        runner = CliRunner()
        result = runner.invoke(app, ["explain", "--fn", "no_such_fn", "-f", str(SAMPLE_PY)])
        assert result.exit_code == 2

    def test_fn_nonexistent_mentions_function_name(self):
        runner = CliRunner()
        result = runner.invoke(app, ["explain", "--fn", "no_such_fn", "-f", str(SAMPLE_PY)])
        assert "no_such_fn" in result.output

    def test_fn_without_file_exits_2(self):
        runner = CliRunner()
        result = runner.invoke(app, ["explain", "--fn", "greet"])
        assert result.exit_code == 2

    def test_fn_without_file_mentions_file(self):
        runner = CliRunner()
        result = runner.invoke(app, ["explain", "--fn", "greet"])
        assert "-f" in result.output or "file" in result.output.lower()

    def test_fn_unsupported_extension_exits_2(self, tmp_path):
        f = tmp_path / "code.txt"
        f.write_text("def greet(): pass\n", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(app, ["explain", "--fn", "greet", "-f", str(f)])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# TestReviewFnFlag
# ---------------------------------------------------------------------------

class TestReviewFnFlag:
    def test_fn_valid_exits_0(self):
        runner = CliRunner()
        with patch(_REVIEW_STREAM, side_effect=_mock_stream()), \
             patch(_REVIEW_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["review", "--fn", "greet", "-f", str(SAMPLE_PY)])
        assert result.exit_code == 0

    def test_fn_nonexistent_exits_2(self):
        runner = CliRunner()
        result = runner.invoke(app, ["review", "--fn", "no_such_fn", "-f", str(SAMPLE_PY)])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# TestEditFnFlag
# ---------------------------------------------------------------------------

class TestEditFnFlag:
    def test_fn_valid_exits_0(self, tmp_path):
        # Copy sample.py so edit can write to it
        target = tmp_path / "sample.py"
        target.write_text(SAMPLE_PY.read_text(encoding="utf-8"), encoding="utf-8")
        runner = CliRunner()
        with patch(_EDIT_STREAM, side_effect=_mock_stream("def greet(name): return 'Hi'")), \
             patch(_EDIT_MODEL_CHECK, return_value=True):
            result = runner.invoke(
                app,
                ["edit", "simplify", "--fn", "greet", "-f", str(target)],
                input="y\n",
            )
        assert result.exit_code == 0

    def test_fn_long_function_exits_3(self, tmp_path):
        # Build a file containing a single function > 150 lines
        lines = ["def big_fn():"]
        lines += [f"    x_{i} = {i}" for i in range(155)]
        lines.append("    return x_0")
        f = tmp_path / "big.py"
        f.write_text("\n".join(lines), encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(app, ["edit", "simplify", "--fn", "big_fn", "-f", str(f)])
        assert result.exit_code == 3


# ---------------------------------------------------------------------------
# TestSourceLabel
# ---------------------------------------------------------------------------

class TestSourceLabel:
    def test_explain_source_label_contains_double_colon(self):
        runner = CliRunner()
        with patch(_EXPLAIN_STREAM, side_effect=_mock_stream()), \
             patch(_EXPLAIN_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["explain", "--fn", "greet", "-f", str(SAMPLE_PY)])
        assert "::" in result.output

    def test_review_source_label_contains_double_colon(self):
        runner = CliRunner()
        with patch(_REVIEW_STREAM, side_effect=_mock_stream()), \
             patch(_REVIEW_MODEL_CHECK, return_value=True):
            result = runner.invoke(app, ["review", "--fn", "greet", "-f", str(SAMPLE_PY)])
        assert "::" in result.output

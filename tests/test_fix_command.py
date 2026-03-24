"""CLI integration tests for `lca fix`. edit_run is mocked — no model calls."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lca.cli import app

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_EDIT_RUN = "lca.commands.fix.edit_run"


@pytest.fixture(autouse=True)
def _skip_setup(monkeypatch):
    monkeypatch.setattr("lca.cli._setup", lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestFixValidation:
    def test_no_description_no_error_exits_2(self):
        result = runner.invoke(app, ["fix"])
        assert result.exit_code == 2

    def test_error_only_with_file_exits_0(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        with patch(_EDIT_RUN):
            result = runner.invoke(app, ["fix", "--error", "some error", "-f", str(f)])
        assert result.exit_code == 0

    def test_description_only_with_file_exits_0(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        with patch(_EDIT_RUN):
            result = runner.invoke(app, ["fix", "add a docstring", "-f", str(f)])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------

class TestFixAutoDetection:
    def test_python_stack_trace_auto_detects_function(self):
        trace = 'File "lca/config.py", line 89, in _merge'
        with patch(_EDIT_RUN):
            result = runner.invoke(app, [
                "fix", "--error", trace,
                "-f", str(FIXTURES_DIR / "sample.py"),
            ])
        assert result.exit_code == 0
        assert "Auto-detected" in result.output

    def test_python_stack_trace_auto_detects_function_name(self):
        trace = 'File "lca/config.py", line 89, in _merge'
        with patch(_EDIT_RUN):
            result = runner.invoke(app, [
                "fix", "--error", trace,
                "-f", str(FIXTURES_DIR / "sample.py"),
            ])
        assert "_merge" in result.output

    def test_parseable_file_path_used_without_f(self, tmp_path):
        f = tmp_path / "module.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        # Use absolute path so Path(str(f)).exists() is True
        error_msg = f'File "{f}", line 1, in foo'
        with patch(_EDIT_RUN):
            result = runner.invoke(app, ["fix", "--error", error_msg])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Resolution failures
# ---------------------------------------------------------------------------

class TestFixResolutionFailure:
    def test_unparseable_error_no_file_no_dir_exits_2(self):
        result = runner.invoke(app, ["fix", "--error", "null pointer dereference"])
        assert result.exit_code == 2

    def test_function_not_found_in_directory_exits_2(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def other_func(): pass\n", encoding="utf-8")
        result = runner.invoke(app, [
            "fix", "--error", "KeyError in totally_missing_func",
            "-d", str(tmp_path),
        ])
        assert result.exit_code == 2

    def test_error_with_no_file_info_no_dir_exits_2(self):
        # Error provides a function name via "in func" but no -f or -d
        result = runner.invoke(app, ["fix", "--error", "KeyError in apply_tax"])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# Targeting output
# ---------------------------------------------------------------------------

class TestFixTargetingOutput:
    def test_output_always_contains_targeting(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        with patch(_EDIT_RUN):
            result = runner.invoke(app, ["fix", "add types", "-f", str(f)])
        assert "Targeting:" in result.output

    def test_explicit_fn_no_auto_detected_message(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        with patch(_EDIT_RUN):
            result = runner.invoke(app, ["fix", "add types", "-f", str(f), "--fn", "foo"])
        assert "Auto-detected" not in result.output
        assert "foo" in result.output

    def test_auto_detected_fn_shows_message(self):
        trace = 'File "lca/config.py", line 89, in _merge'
        with patch(_EDIT_RUN):
            result = runner.invoke(app, [
                "fix", "--error", trace,
                "-f", str(FIXTURES_DIR / "sample.py"),
            ])
        assert "Auto-detected" in result.output

    def test_whole_file_shown_when_no_fn(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        with patch(_EDIT_RUN):
            result = runner.invoke(app, ["fix", "--error", "null pointer dereference", "-f", str(f)])
        assert "whole file" in result.output

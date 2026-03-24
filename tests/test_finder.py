"""Unit tests for lca.context.finder — no model calls needed."""

from pathlib import Path

import pytest

from lca.context.finder import index_directory, list_functions_in_file

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# list_functions_in_file
# ---------------------------------------------------------------------------

def test_list_functions_returns_expected_names():
    functions = list_functions_in_file(FIXTURES_DIR / "sample.py")
    names = {name for name, _ in functions}
    assert names == {"greet", "add", "method", "decorator", "decorated"}


def test_list_functions_returns_start_lines():
    functions = list_functions_in_file(FIXTURES_DIR / "sample.py")
    d = dict(functions)
    assert d["greet"] == 1
    assert d["add"] == 6
    assert d["method"] == 11
    assert d["decorator"] == 15
    assert d["decorated"] == 19  # decorated_definition starts at @decorator line


def test_list_functions_unsupported_extension(tmp_path):
    f = tmp_path / "script.rb"
    f.write_text("def hello; end\n", encoding="utf-8")
    assert list_functions_in_file(f) == []


def test_list_functions_nonexistent_file(tmp_path):
    assert list_functions_in_file(tmp_path / "missing.py") == []


def test_list_functions_unparseable_file(tmp_path):
    # Write binary content that tree-sitter cannot parse as Python meaningfully.
    # tree-sitter is resilient, so we test with a truly broken source by
    # creating a file that can't be decoded as UTF-8.
    f = tmp_path / "bad.py"
    f.write_bytes(b"\xff\xfe invalid utf8 \x00\x01")
    assert list_functions_in_file(f) == []


def test_list_functions_javascript():
    functions = list_functions_in_file(FIXTURES_DIR / "sample.js")
    names = {name for name, _ in functions}
    assert "greet" in names
    assert "add" in names


def test_list_functions_go():
    functions = list_functions_in_file(FIXTURES_DIR / "sample.go")
    names = {name for name, _ in functions}
    assert "greet" in names
    assert "add" in names


# ---------------------------------------------------------------------------
# index_directory
# ---------------------------------------------------------------------------

def test_index_directory_finds_functions_across_files():
    results = index_directory(FIXTURES_DIR)
    all_names = {name for _, name, _ in results}
    # greet and add appear in sample.py, sample.js, and sample.go
    assert "greet" in all_names
    assert "add" in all_names


def test_index_directory_returns_file_paths():
    results = index_directory(FIXTURES_DIR)
    files = {path for path, _, _ in results}
    assert any(p.name == "sample.py" for p in files)
    assert any(p.name == "sample.js" for p in files)
    assert any(p.name == "sample.go" for p in files)


def test_index_directory_skips_pycache(tmp_path):
    # Create a valid .py file in __pycache__ — should be skipped
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    hidden = pycache / "hidden.py"
    hidden.write_text("def should_not_appear(): pass\n", encoding="utf-8")
    # Create a real file in the root
    visible = tmp_path / "visible.py"
    visible.write_text("def should_appear(): pass\n", encoding="utf-8")

    results = index_directory(tmp_path)
    names = [name for _, name, _ in results]
    assert "should_appear" in names
    assert "should_not_appear" not in names


def test_index_directory_skips_venv(tmp_path):
    venv = tmp_path / ".venv"
    venv.mkdir()
    hidden = venv / "lib.py"
    hidden.write_text("def venv_fn(): pass\n", encoding="utf-8")
    real = tmp_path / "app.py"
    real.write_text("def app_fn(): pass\n", encoding="utf-8")

    results = index_directory(tmp_path)
    names = [name for _, name, _ in results]
    assert "app_fn" in names
    assert "venv_fn" not in names


def test_index_directory_respects_extensions_filter(tmp_path):
    py_file = tmp_path / "mod.py"
    py_file.write_text("def py_fn(): pass\n", encoding="utf-8")
    go_file = tmp_path / "mod.go"
    go_file.write_text("package main\nfunc go_fn() {}\n", encoding="utf-8")

    results = index_directory(tmp_path, extensions=[".py"])
    names = [name for _, name, _ in results]
    assert "py_fn" in names
    assert "go_fn" not in names


def test_index_directory_sorted_by_file_then_line(tmp_path):
    # Single file with two functions — lines must be in order
    f = tmp_path / "order.py"
    f.write_text(
        "def alpha(): pass\n\ndef beta(): pass\n",
        encoding="utf-8",
    )
    results = index_directory(tmp_path, extensions=[".py"])
    lines = [line for _, _, line in results]
    assert lines == sorted(lines)


def test_index_directory_sorted_across_files(tmp_path):
    # Two files: b.py and a.py — a.py should come first alphabetically
    (tmp_path / "b.py").write_text("def b_fn(): pass\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("def a_fn(): pass\n", encoding="utf-8")

    results = index_directory(tmp_path, extensions=[".py"])
    paths = [str(p) for p, _, _ in results]
    assert paths == sorted(paths)

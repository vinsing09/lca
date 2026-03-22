from pathlib import Path

import pytest

from lca.context.extractor import (
    ExtractionError,
    detect_language,
    extract_function,
    extract_function_with_offsets,
)

FIXTURES = Path(__file__).parent / "fixtures"

PY_SRC = (FIXTURES / "sample.py").read_text(encoding="utf-8")
JS_SRC = (FIXTURES / "sample.js").read_text(encoding="utf-8")
GO_SRC = (FIXTURES / "sample.go").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# detect_language
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    @pytest.mark.parametrize("ext,expected", [
        (".py", "python"),
        (".js", "javascript"),
        (".ts", "javascript"),
        (".go", "go"),
    ])
    def test_supported_extensions(self, tmp_path, ext, expected):
        f = tmp_path / f"file{ext}"
        f.touch()
        assert detect_language(f) == expected

    @pytest.mark.parametrize("ext", [".rb", ".rs", ".txt"])
    def test_unsupported_raises(self, tmp_path, ext):
        f = tmp_path / f"file{ext}"
        f.touch()
        with pytest.raises(ExtractionError):
            detect_language(f)


# ---------------------------------------------------------------------------
# Python extractions
# ---------------------------------------------------------------------------

class TestExtractPython:
    def test_finds_greet(self):
        result = extract_function(PY_SRC, "greet", "python")
        assert "greet" in result

    def test_finds_add(self):
        result = extract_function(PY_SRC, "add", "python")
        assert "add" in result

    def test_finds_method_inside_class(self):
        result = extract_function(PY_SRC, "method", "python")
        assert "method" in result

    def test_greet_contains_signature(self):
        result = extract_function(PY_SRC, "greet", "python")
        assert "def greet" in result

    def test_greet_does_not_contain_add(self):
        result = extract_function(PY_SRC, "greet", "python")
        assert "def add" not in result

    def test_nonexistent_raises(self):
        with pytest.raises(ExtractionError):
            extract_function(PY_SRC, "nonexistent_fn", "python")


# ---------------------------------------------------------------------------
# JavaScript extractions
# ---------------------------------------------------------------------------

class TestExtractJavaScript:
    def test_finds_greet(self):
        result = extract_function(JS_SRC, "greet", "javascript")
        assert "greet" in result

    def test_finds_add_arrow(self):
        result = extract_function(JS_SRC, "add", "javascript")
        assert "add" in result

    def test_greet_contains_signature(self):
        result = extract_function(JS_SRC, "greet", "javascript")
        assert "function greet" in result

    def test_greet_does_not_contain_add(self):
        result = extract_function(JS_SRC, "greet", "javascript")
        assert "add" not in result

    def test_nonexistent_raises(self):
        with pytest.raises(ExtractionError):
            extract_function(JS_SRC, "nonexistent_fn", "javascript")


# ---------------------------------------------------------------------------
# Go extractions
# ---------------------------------------------------------------------------

class TestExtractGo:
    def test_finds_greet(self):
        result = extract_function(GO_SRC, "greet", "go")
        assert "greet" in result

    def test_finds_add(self):
        result = extract_function(GO_SRC, "add", "go")
        assert "add" in result

    def test_greet_contains_signature(self):
        result = extract_function(GO_SRC, "greet", "go")
        assert "func greet" in result

    def test_greet_does_not_contain_add(self):
        result = extract_function(GO_SRC, "greet", "go")
        assert "func add" not in result

    def test_nonexistent_raises(self):
        with pytest.raises(ExtractionError):
            extract_function(GO_SRC, "nonexistent_fn", "go")


# ---------------------------------------------------------------------------
# Unsupported language
# ---------------------------------------------------------------------------

def test_unsupported_language_raises():
    with pytest.raises(ExtractionError):
        extract_function("fn foo() {}", "foo", "ruby")


# ---------------------------------------------------------------------------
# Decorator and idempotency edge cases
# ---------------------------------------------------------------------------

def test_decorated_function_includes_decorator():
    """Extracting a decorated Python function returns the decorator too."""
    py_src = (FIXTURES / "sample.py").read_text(encoding="utf-8")
    result = extract_function(py_src, "decorated", "python")
    assert "@decorator" in result
    assert "def decorated" in result


def test_extract_same_function_twice_is_identical():
    result1 = extract_function(PY_SRC, "greet", "python")
    result2 = extract_function(PY_SRC, "greet", "python")
    assert result1 == result2


# ---------------------------------------------------------------------------
# extract_function_with_offsets
# ---------------------------------------------------------------------------

class TestExtractWithOffsets:
    def test_python_offsets_consistent(self):
        text, start, end = extract_function_with_offsets(PY_SRC, "greet", "python")
        assert PY_SRC[start:end] == text

    def test_javascript_offsets_consistent(self):
        js_src = (FIXTURES / "sample.js").read_text(encoding="utf-8")
        text, start, end = extract_function_with_offsets(js_src, "greet", "javascript")
        assert js_src[start:end] == text

    def test_go_offsets_consistent(self):
        go_src = (FIXTURES / "sample.go").read_text(encoding="utf-8")
        text, start, end = extract_function_with_offsets(go_src, "greet", "go")
        assert go_src[start:end] == text

    def test_offsets_match_extract_function_text(self):
        """extract_function_with_offsets returns the same text as extract_function."""
        text_plain = extract_function(PY_SRC, "add", "python")
        text_with_offsets, _, _ = extract_function_with_offsets(PY_SRC, "add", "python")
        assert text_plain == text_with_offsets

    def test_nonexistent_raises(self):
        with pytest.raises(ExtractionError):
            extract_function_with_offsets(PY_SRC, "nonexistent", "python")

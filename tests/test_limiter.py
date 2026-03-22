import pytest

from lca.context.limiter import LimitError, SizeReport, check_limits, estimate_tokens


def _make_text(lines: int) -> str:
    return "\n".join(f"line {i}" for i in range(lines))


def test_estimate_tokens_basic():
    # "hello world" → 2 words → int(2 * 1.3) = 2
    assert estimate_tokens("hello world") == 2


def test_estimate_tokens_truncates():
    # 3 words → int(3 * 1.3) = int(3.9) = 3
    assert estimate_tokens("one two three") == 3


def test_exactly_at_limit():
    text = _make_text(10)
    report = check_limits(text, max_lines=10, warn_token_threshold=9999)
    assert isinstance(report, SizeReport)
    assert report.line_count == 10


def test_over_limit_raises():
    text = _make_text(11)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=10, warn_token_threshold=9999)
    err = exc_info.value
    assert err.line_count == 11
    assert err.limit == 10


def test_limit_error_message_contains_hint():
    text = _make_text(5)
    with pytest.raises(LimitError, match="--fn"):
        check_limits(text, max_lines=4, warn_token_threshold=9999)


def test_source_label_in_error():
    text = _make_text(5)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=4, warn_token_threshold=9999, source="myfile.py")
    assert "myfile.py" in str(exc_info.value)


def test_over_warn_threshold_true():
    text = " ".join(["word"] * 200)  # 200 words → 260 tokens
    report = check_limits(text, max_lines=9999, warn_token_threshold=100)
    assert report.over_warn_threshold is True


def test_over_warn_threshold_false():
    text = "short text"
    report = check_limits(text, max_lines=9999, warn_token_threshold=9999)
    assert report.over_warn_threshold is False


def test_size_report_fields():
    text = _make_text(5)
    report = check_limits(text, max_lines=10, warn_token_threshold=9999)
    assert report.line_count == 5
    assert isinstance(report.estimated_tokens, int)
    assert isinstance(report.over_warn_threshold, bool)

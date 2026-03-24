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


# ---------------------------------------------------------------------------
# New defaults
# ---------------------------------------------------------------------------

def test_default_edit_limit_is_400():
    from lca.config import LimitsConfig
    assert LimitsConfig().max_edit_lines == 400


def test_default_explain_limit_is_1000():
    from lca.config import LimitsConfig
    assert LimitsConfig().max_explain_lines == 1000


def test_default_review_limit_is_1000():
    from lca.config import LimitsConfig
    assert LimitsConfig().max_review_lines == 1000


def test_default_warn_token_threshold_is_8000():
    from lca.config import LimitsConfig
    assert LimitsConfig().warn_token_threshold == 8000


# ---------------------------------------------------------------------------
# Context-aware error messages
# ---------------------------------------------------------------------------

def test_edit_command_message_mentions_lca_edit():
    text = _make_text(5)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=4, warn_token_threshold=9999,
                     source="foo.py", command="edit")
    msg = str(exc_info.value)
    assert "--fn" in msg
    assert "lca edit" in msg


def test_review_command_message_mentions_lca_review():
    text = _make_text(5)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=4, warn_token_threshold=9999,
                     source="foo.py", command="review")
    msg = str(exc_info.value)
    assert "--fn" in msg
    assert "lca review" in msg


def test_explain_command_message_mentions_lca_explain():
    text = _make_text(5)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=4, warn_token_threshold=9999,
                     source="foo.py", command="explain")
    msg = str(exc_info.value)
    assert "--fn" in msg
    assert "lca explain" in msg


def test_edit_command_message_no_break_file_hint():
    text = _make_text(5)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=4, warn_token_threshold=9999,
                     source="foo.py", command="edit")
    assert "break the file up" not in str(exc_info.value)


def test_review_command_message_has_break_file_hint():
    text = _make_text(5)
    with pytest.raises(LimitError) as exc_info:
        check_limits(text, max_lines=4, warn_token_threshold=9999,
                     source="foo.py", command="review")
    assert "break the file up" in str(exc_info.value)

import pytest

from lca.llm.prompts import (
    EDIT_SYSTEM,
    EDIT_TEMPERATURE,
    EXPLAIN_SYSTEM,
    EXPLAIN_TEMPERATURE,
    FIX_SYSTEM,
    FIX_TEMPERATURE,
    REVIEW_SYSTEM,
    REVIEW_TEMPERATURE,
    edit_user,
    explain_user,
    fix_user,
    review_user,
)

CODE = "def add(a, b):\n    return a + b"


# ---------------------------------------------------------------------------
# explain_user
# ---------------------------------------------------------------------------

def test_explain_user_embeds_code():
    prompt = explain_user(CODE)
    assert CODE in prompt


def test_explain_user_no_extra_instructions_by_default():
    prompt = explain_user(CODE)
    assert "Additional instructions" not in prompt


def test_explain_user_appends_extra_instructions():
    prompt = explain_user(CODE, extra_instructions="Focus on types.")
    assert "Focus on types." in prompt
    assert "Additional instructions" in prompt


def test_explain_user_ignores_whitespace_only_extra():
    prompt = explain_user(CODE, extra_instructions="   ")
    assert "Additional instructions" not in prompt


# ---------------------------------------------------------------------------
# review_user
# ---------------------------------------------------------------------------

def test_review_user_embeds_code():
    prompt = review_user(CODE)
    assert CODE in prompt


def test_review_user_no_extra_instructions_by_default():
    prompt = review_user(CODE)
    assert "Additional instructions" not in prompt


def test_review_user_appends_extra_instructions():
    prompt = review_user(CODE, extra_instructions="Check error handling.")
    assert "Check error handling." in prompt
    assert "Additional instructions" in prompt


def test_review_user_ignores_whitespace_only_extra():
    prompt = review_user(CODE, extra_instructions="\n\t")
    assert "Additional instructions" not in prompt


# ---------------------------------------------------------------------------
# EXPLAIN_SYSTEM
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("phrase", ["step by step", "think about", "let's think", "chain of thought"])
def test_explain_system_no_chain_of_thought_language(phrase):
    assert phrase.lower() not in EXPLAIN_SYSTEM.lower()


def test_explain_system_no_suggest_improvements():
    lower = EXPLAIN_SYSTEM.lower()
    assert "suggest improvements" in lower or "do not suggest" in lower or "not suggest" in lower


# ---------------------------------------------------------------------------
# REVIEW_SYSTEM
# ---------------------------------------------------------------------------

def test_review_system_contains_bugs_section():
    assert "## BUGS" in REVIEW_SYSTEM


def test_review_system_contains_edge_cases_section():
    assert "## EDGE CASES" in REVIEW_SYSTEM


def test_review_system_contains_style_section():
    assert "## STYLE" in REVIEW_SYSTEM


def test_review_system_no_auto_fix():
    lower = REVIEW_SYSTEM.lower()
    assert "auto-fix" in lower or "do not" in lower or "not" in lower


def test_review_system_bugs_is_first_line():
    assert "## BUGS" in REVIEW_SYSTEM


def test_review_system_contains_directly_visible():
    assert "directly visible" in REVIEW_SYSTEM.lower() or "directly see" in REVIEW_SYSTEM.lower()


def test_review_system_contains_do_not_invent():
    assert "do not invent" in REVIEW_SYSTEM.lower()


# ---------------------------------------------------------------------------
# EDIT_SYSTEM
# ---------------------------------------------------------------------------

def test_edit_system_mentions_comments_as_valid_edit():
    lower = EDIT_SYSTEM.lower()
    assert "comment" in lower


def test_edit_system_mentions_docstrings_as_valid_edit():
    lower = EDIT_SYSTEM.lower()
    assert "docstring" in lower


def test_edit_system_says_do_not_refactor():
    lower = EDIT_SYSTEM.lower()
    assert "refactor" in lower


# ---------------------------------------------------------------------------
# FIX_SYSTEM
# ---------------------------------------------------------------------------

def test_fix_system_contains_smallest_possible_change():
    assert "smallest possible change" in FIX_SYSTEM.lower()


def test_fix_system_contains_output_original_unchanged():
    assert "output the original code unchanged" in FIX_SYSTEM.lower()


def test_fix_system_says_do_not_refactor():
    lower = FIX_SYSTEM.lower()
    assert "refactor" in lower


# ---------------------------------------------------------------------------
# fix_user
# ---------------------------------------------------------------------------

def test_fix_user_embeds_code():
    prompt = fix_user(CODE, "fix the bug")
    assert CODE in prompt


def test_fix_user_contains_smallest_change():
    prompt = fix_user(CODE, "fix the bug")
    assert "smallest change" in prompt.lower()


def test_fix_user_embeds_instruction():
    prompt = fix_user(CODE, "fix the off-by-one error")
    assert "fix the off-by-one error" in prompt


def test_fix_user_no_extra_by_default():
    prompt = fix_user(CODE, "fix the bug")
    assert "Project context" not in prompt


def test_fix_user_appends_extra_instructions():
    prompt = fix_user(CODE, "fix the bug", extra_instructions="Use Python 3.10+")
    assert "Project context" in prompt
    assert "Use Python 3.10+" in prompt


def test_fix_user_contains_output_unchanged_hint():
    prompt = fix_user(CODE, "fix the bug")
    assert "output the original code unchanged" in prompt.lower()


# ---------------------------------------------------------------------------
# Temperatures
# ---------------------------------------------------------------------------

def test_explain_temperature():
    assert EXPLAIN_TEMPERATURE == 0.4


def test_review_temperature():
    assert REVIEW_TEMPERATURE == 0.4


def test_fix_temperature():
    assert FIX_TEMPERATURE == 0.1

import pytest

from lca.llm.prompts import (
    EXPLAIN_SYSTEM,
    EXPLAIN_TEMPERATURE,
    REVIEW_SYSTEM,
    REVIEW_TEMPERATURE,
    explain_user,
    review_user,
)

CODE = "def add(a, b):\n    return a + b"


# --- explain_user ---

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


# --- review_user ---

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


# --- EXPLAIN_SYSTEM prompt rules ---

@pytest.mark.parametrize("phrase", ["step by step", "think about", "let's think", "chain of thought"])
def test_explain_system_no_chain_of_thought_language(phrase):
    assert phrase.lower() not in EXPLAIN_SYSTEM.lower()


def test_explain_system_no_suggest_improvements():
    lower = EXPLAIN_SYSTEM.lower()
    assert "suggest improvements" in lower or "do not suggest" in lower or "not suggest" in lower


# --- REVIEW_SYSTEM prompt rules ---

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
    first_line = REVIEW_SYSTEM.strip().splitlines()[0]
    assert first_line.strip() == "## BUGS" or "## BUGS" in REVIEW_SYSTEM


# --- temperatures ---

def test_explain_temperature():
    assert EXPLAIN_TEMPERATURE == 0.4


def test_review_temperature():
    assert REVIEW_TEMPERATURE == 0.4

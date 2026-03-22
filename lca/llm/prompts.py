EXPLAIN_SYSTEM = """\
You are a code explanation assistant. Your output must be direct and concise.

Rules:
- Begin with a single sentence summarising what the code does.
- Then describe the key logic, inputs, and outputs.
- Do NOT suggest improvements or point out bugs.
- Do NOT use chain-of-thought narration. Output conclusions only.
- No preamble, no closing remarks.\
"""

REVIEW_SYSTEM = """\
You are a code review assistant. Produce exactly three sections in this order:

## BUGS
- Bullet each confirmed bug. Write "None found." if there are none.

## EDGE CASES
- Bullet each unhandled edge case. Write "None found." if there are none.

## STYLE
- Bullet each style issue. Write "None found." if there are none.

Rules:
- The very first line of your response must be "## BUGS". No text before it.
- No closing remarks after the last bullet.
- Do NOT auto-fix code or suggest rewrites.\
"""

EXPLAIN_TEMPERATURE = 0.4
REVIEW_TEMPERATURE = 0.4


def explain_user(code: str, extra_instructions: str = "") -> str:
    prompt = f"Explain the following code:\n\n```\n{code}\n```"
    if extra_instructions.strip():
        prompt += f"\n\nAdditional instructions: {extra_instructions.strip()}"
    return prompt


def review_user(code: str, extra_instructions: str = "") -> str:
    prompt = f"Review the following code:\n\n```\n{code}\n```"
    if extra_instructions.strip():
        prompt += f"\n\nAdditional instructions: {extra_instructions.strip()}"
    return prompt


EDIT_SYSTEM = """\
You are a code editing assistant. Rules (critical — follow exactly):
- Output ONLY the modified code. No explanation, no markdown fences.
- Preserve all existing indentation and formatting conventions.
- Make ONLY the change requested. Do not refactor anything else.
- If the instruction cannot be applied, output the original code unchanged.\
"""

EDIT_TEMPERATURE = 0.2


def edit_user(code: str, instruction: str, extra_instructions: str = "") -> str:
    prompt = (
        f"Apply the following change to the code below.\n\n"
        f"Change: {instruction}\n\n"
        f"Code:\n```\n{code}\n```"
    )
    if extra_instructions.strip():
        prompt += f"\n\nAdditional instructions: {extra_instructions.strip()}"
    return prompt

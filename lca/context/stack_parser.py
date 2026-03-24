"""Parse stack traces and error messages to extract file, function, and line info."""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Compiled patterns — each yields (file_path, func_name, line_num) subsets
# ---------------------------------------------------------------------------

# Python: File "src/payment.py", line 67, in apply_tax
#         File src/payment.py, line 67, in apply_tax
_PY_FRAME = re.compile(
    r'File\s+"?([^",\n]+?)"?,\s+line\s+(\d+),\s+in\s+(\w+)'
)

# JavaScript: at apply_tax (src/payment.js:67:12)
#             at Object.apply_tax (src/payment.js:67:12)
_JS_FRAME = re.compile(
    r'at\s+(?:[\w$.]+\.)?(\w+)\s+\(([^:)\n]+):(\d+):\d+\)'
)

# Go: src/payment.go:67 +0x1a2
#     src/payment.go:67
_GO_FRAME = re.compile(
    r'([\w./\\-]+\.go):(\d+)(?:\s+\+0x[0-9a-f]+)?(?:\s|$)'
)

# Generic: apply_tax at line 67
_GENERIC_AT_LINE = re.compile(r'(\w+)\s+at\s+line\s+(\d+)')

# Generic: KeyError in apply_tax [at line 67]
# Require capitalized first word (e.g. KeyError, TypeError) to avoid
# false-positive matches on plain English like "error in release".
_GENERIC_IN = re.compile(
    r'([A-Z]\w*)\s+in\s+(\w+)(?:\s+at\s+line\s+(\d+))?'
)

# Go function name on the line preceding a Go file:line entry.
# Matches: main.apply_tax(...), apply_tax(...)
_GO_FN_LINE = re.compile(r'(?:[\w.]+\.)?(\w+)\(')


def parse_error(error_text: str) -> tuple[str | None, str | None, int | None]:
    """Extract (file_path, function_name, line_number) from a stack trace.

    Always returns the LAST frame — the actual error location, not callers.
    Returns (None, None, None) if nothing recognisable is found.
    """
    lines = error_text.splitlines()
    frames: list[tuple[str | None, str | None, int | None]] = []
    prev_stripped = ""

    for raw_line in lines:
        stripped = raw_line.strip()

        # --- Python ---
        m = _PY_FRAME.search(stripped)
        if m:
            frames.append((m.group(1), m.group(3), int(m.group(2))))
            prev_stripped = stripped
            continue

        # --- JavaScript ---
        m = _JS_FRAME.search(stripped)
        if m:
            frames.append((m.group(2), m.group(1), int(m.group(3))))
            prev_stripped = stripped
            continue

        # --- Go ---
        m = _GO_FRAME.search(stripped)
        if m:
            fn_name: str | None = None
            gm = _GO_FN_LINE.search(prev_stripped)
            if gm:
                fn_name = gm.group(1)
            frames.append((m.group(1), fn_name, int(m.group(2))))
            prev_stripped = stripped
            continue

        # --- Generic: func at line N ---
        m = _GENERIC_AT_LINE.search(stripped)
        if m:
            frames.append((None, m.group(1), int(m.group(2))))
            prev_stripped = stripped
            continue

        # --- Generic: CapError in func [at line N] ---
        m = _GENERIC_IN.search(stripped)
        if m:
            line_num = int(m.group(3)) if m.group(3) else None
            frames.append((None, m.group(2), line_num))
            prev_stripped = stripped
            continue

        prev_stripped = stripped

    if not frames:
        return (None, None, None)

    file_path, func_name, line_num = frames[-1]
    return (file_path or None, func_name or None, line_num)


def find_function_at_line(path: Path, line_number: int) -> str | None:
    """Return the name of the function that contains line_number in path.

    Uses list_functions_in_file to get (name, start_line) pairs and returns
    the function whose start_line is closest to but not greater than
    line_number.  Returns None if line_number is out of range or no function
    covers that line.
    """
    from lca.context.finder import list_functions_in_file

    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return None

    total_lines = len(source.splitlines())
    if line_number <= 0 or line_number > total_lines:
        return None

    functions = list_functions_in_file(path)
    if not functions:
        return None

    best: str | None = None
    for name, start_line in sorted(functions, key=lambda x: x[1]):
        if start_line <= line_number:
            best = name
        else:
            break
    return best

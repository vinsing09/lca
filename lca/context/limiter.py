from dataclasses import dataclass


class LimitError(Exception):
    def __init__(self, line_count: int, limit: int, source: str = "input", command: str = ""):
        self.line_count = line_count
        self.limit = limit
        self.source = source
        if command == "edit" or (not command and limit <= 400):
            hint = (
                f"Use --fn to target a specific function:\n"
                f"  lca edit -f {source} --fn <function_name> \"your instruction\""
            )
        elif command in ("explain", "review") or (not command and limit > 400):
            cmd = command or "review"
            hint = (
                f"Use --fn to target a specific function, or break the file up:\n"
                f"  lca {cmd} -f {source} --fn <function_name>"
            )
        else:
            hint = "Use --fn to target a specific function instead."
        super().__init__(
            f"{source} has {line_count} lines, which exceeds the {limit}-line limit. "
            f"{hint}"
        )


@dataclass
class SizeReport:
    line_count: int
    estimated_tokens: int
    over_warn_threshold: bool


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


def check_limits(
    text: str,
    *,
    max_lines: int,
    warn_token_threshold: int,
    source: str = "input",
    command: str = "",
) -> SizeReport:
    line_count = len(text.splitlines())
    if line_count > max_lines:
        raise LimitError(line_count, max_lines, source, command)
    estimated_tokens = estimate_tokens(text)
    return SizeReport(
        line_count=line_count,
        estimated_tokens=estimated_tokens,
        over_warn_threshold=estimated_tokens > warn_token_threshold,
    )

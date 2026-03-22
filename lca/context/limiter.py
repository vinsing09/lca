from dataclasses import dataclass


class LimitError(Exception):
    def __init__(self, line_count: int, limit: int, source: str = "input"):
        self.line_count = line_count
        self.limit = limit
        self.source = source
        super().__init__(
            f"{source} has {line_count} lines, which exceeds the {limit}-line limit. "
            f"Use --fn to target a specific function instead."
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
) -> SizeReport:
    line_count = len(text.splitlines())
    if line_count > max_lines:
        raise LimitError(line_count, max_lines, source)
    estimated_tokens = estimate_tokens(text)
    return SizeReport(
        line_count=line_count,
        estimated_tokens=estimated_tokens,
        over_warn_threshold=estimated_tokens > warn_token_threshold,
    )

"""Walk source trees and list all named functions in supported files."""

from pathlib import Path

from tree_sitter import Node

from lca.context.extractor import ExtractionError, _parse, detect_language

SKIP_DIRS = {
    "__pycache__", ".venv", "venv", "node_modules",
    ".git", "dist", "build", ".pytest_cache",
}

_DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".go"]


# ---------------------------------------------------------------------------
# Language-specific "list all functions" walkers
# ---------------------------------------------------------------------------

def _list_python(node: Node, results: list[tuple[str, int]]) -> None:
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type == "function_definition":
                name_node = child.child_by_field_name("name")
                if name_node and name_node.text:
                    results.append((name_node.text.decode(), node.start_point[0] + 1))
                # Recurse into the function body to find nested functions.
                for grandchild in child.children:
                    _list_python(grandchild, results)
        return  # don't fall through — avoids double-counting the function_definition
    elif node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        if name_node and name_node.text:
            results.append((name_node.text.decode(), node.start_point[0] + 1))
    for child in node.children:
        _list_python(child, results)


def _list_javascript(node: Node, results: list[tuple[str, int]]) -> None:
    if node.type in ("function_declaration", "method_definition"):
        name_node = node.child_by_field_name("name")
        if name_node and name_node.text:
            results.append((name_node.text.decode(), node.start_point[0] + 1))
    elif node.type == "variable_declarator":
        name_node = node.child_by_field_name("name")
        value_node = node.child_by_field_name("value")
        if name_node and name_node.text and value_node and value_node.type == "arrow_function":
            parent = node.parent
            start_line = (parent.start_point[0] + 1) if parent else (node.start_point[0] + 1)
            results.append((name_node.text.decode(), start_line))
    for child in node.children:
        _list_javascript(child, results)


def _list_go(node: Node, results: list[tuple[str, int]]) -> None:
    if node.type in ("function_declaration", "method_declaration"):
        name_node = node.child_by_field_name("name")
        if name_node and name_node.text:
            results.append((name_node.text.decode(), node.start_point[0] + 1))
    for child in node.children:
        _list_go(child, results)


_LISTERS = {
    "python": _list_python,
    "javascript": _list_javascript,
    "go": _list_go,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_functions_in_file(path: Path) -> list[tuple[str, int]]:
    """Return [(function_name, start_line), ...] for all functions in file.

    Uses detect_language() and tree-sitter to parse the file.
    Returns [] if the file extension is unsupported or parsing fails.
    start_line is 1-indexed.
    """
    try:
        language = detect_language(path)
    except ExtractionError:
        return []
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []
    try:
        _, root = _parse(source, language)
    except ExtractionError:
        return []
    results: list[tuple[str, int]] = []
    _LISTERS[language](root, results)
    return results


def _walk_dir(directory: Path):
    """Yield all files under directory, skipping SKIP_DIRS."""
    try:
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in SKIP_DIRS:
                    yield from _walk_dir(item)
            elif item.is_file():
                yield item
    except PermissionError:
        pass


def index_directory(
    directory: Path,
    extensions: list[str] | None = None,
) -> list[tuple[Path, str, int]]:
    """Walk directory recursively, return all functions as:
      [(file_path, function_name, start_line), ...]

    Default extensions: .py, .js, .ts, .go
    Skips any directory whose name is in SKIP_DIRS.
    Results are sorted by file_path then start_line.
    """
    if extensions is None:
        extensions = _DEFAULT_EXTENSIONS
    ext_set = {e.lower() for e in extensions}
    results: list[tuple[Path, str, int]] = []
    for path in _walk_dir(directory):
        if path.suffix.lower() in ext_set:
            for name, line in list_functions_in_file(path):
                results.append((path, name, line))
    results.sort(key=lambda x: (str(x[0]), x[2]))
    return results

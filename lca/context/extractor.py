"""Extract a single named function from source code using tree-sitter.

This is the only module in lca that imports tree-sitter directly.
"""

from pathlib import Path

import tree_sitter_go as tsgo
import tree_sitter_javascript as tsjs
import tree_sitter_python as tspy
from tree_sitter import Language, Node, Parser

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",  # tree-sitter-javascript handles TS well enough
    ".go": "go",
}

_LANGUAGES: dict[str, Language] = {
    "python": Language(tspy.language()),
    "javascript": Language(tsjs.language()),
    "go": Language(tsgo.language()),
}


class ExtractionError(Exception):
    pass


def detect_language(path: Path) -> str:
    """Return language string for path, or raise ExtractionError if unsupported."""
    ext = path.suffix.lower()
    lang = SUPPORTED_EXTENSIONS.get(ext)
    if lang is None:
        raise ExtractionError(
            f"Unsupported file extension '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return lang


def _get_name(node: Node) -> bytes | None:
    """Return the bytes of the 'name' field child, if present."""
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text
    return None


def _walk_python(node: Node, fn_name: str, source: bytes) -> str | None:
    """Recursively search a Python AST for a function named fn_name."""
    if node.type == "decorated_definition":
        # The actual function/class is a child; check its name
        for child in node.children:
            if child.type == "function_definition":
                if _get_name(child) == fn_name.encode():
                    return source[node.start_byte:node.end_byte].decode()
    elif node.type == "function_definition":
        if _get_name(node) == fn_name.encode():
            return source[node.start_byte:node.end_byte].decode()
    for child in node.children:
        result = _walk_python(child, fn_name, source)
        if result is not None:
            return result
    return None


def _walk_javascript(node: Node, fn_name: str, source: bytes) -> str | None:
    """Recursively search a JavaScript AST for a function named fn_name."""
    if node.type == "function_declaration":
        if _get_name(node) == fn_name.encode():
            return source[node.start_byte:node.end_byte].decode()
    elif node.type == "method_definition":
        if _get_name(node) == fn_name.encode():
            return source[node.start_byte:node.end_byte].decode()
    elif node.type == "variable_declarator":
        # Arrow function: const fn_name = (...) => ...
        name_node = node.child_by_field_name("name")
        value_node = node.child_by_field_name("value")
        if (
            name_node is not None
            and name_node.text == fn_name.encode()
            and value_node is not None
            and value_node.type == "arrow_function"
        ):
            # Return the whole lexical_declaration (parent) for full context,
            # but the spec says "function" so return the declarator's parent
            parent = node.parent
            if parent is not None:
                return source[parent.start_byte:parent.end_byte].decode()
            return source[node.start_byte:node.end_byte].decode()
    for child in node.children:
        result = _walk_javascript(child, fn_name, source)
        if result is not None:
            return result
    return None


def _walk_go(node: Node, fn_name: str, source: bytes) -> str | None:
    """Recursively search a Go AST for a function named fn_name."""
    if node.type in ("function_declaration", "method_declaration"):
        if _get_name(node) == fn_name.encode():
            return source[node.start_byte:node.end_byte].decode()
    for child in node.children:
        result = _walk_go(child, fn_name, source)
        if result is not None:
            return result
    return None


_WALKERS = {
    "python": _walk_python,
    "javascript": _walk_javascript,
    "go": _walk_go,
}


def extract_function(source: str, fn_name: str, language: str) -> str:
    """Return the source text of the named function/method.

    Raises ExtractionError if language is unsupported, the parse fails,
    or fn_name is not found.
    """
    if language not in _LANGUAGES:
        raise ExtractionError(f"Unsupported language: {language!r}")

    lang = _LANGUAGES[language]
    parser = Parser(lang)
    source_bytes = source.encode()

    try:
        tree = parser.parse(source_bytes)
    except Exception as exc:
        raise ExtractionError(f"tree-sitter parse failed: {exc}") from exc

    walker = _WALKERS[language]
    result = walker(tree.root_node, fn_name, source_bytes)

    if result is None:
        raise ExtractionError(
            f"Function {fn_name!r} not found in {language} source."
        )
    return result

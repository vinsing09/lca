def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}"


def add(a: int, b: int) -> int:
    return a + b


class MyClass:
    def method(self) -> None:
        pass


def decorator(fn):
    return fn


@decorator
def decorated(x: int) -> int:
    """A decorated function."""
    return x * 2

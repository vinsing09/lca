import json
from collections.abc import Generator

import httpx


class OllamaError(Exception):
    pass


def stream_chat(
    *,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> Generator[str, None, None]:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "stream": True,
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    body = response.read().decode(errors="replace")
                    raise OllamaError(
                        f"Ollama returned HTTP {response.status_code}: {body}"
                    )
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "error" in data:
                        raise OllamaError(f"Ollama model error: {data['error']}")
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
    except httpx.ConnectError as exc:
        raise OllamaError(f"Could not connect to Ollama at {base_url}: {exc}") from exc
    except httpx.TimeoutException as exc:
        raise OllamaError(f"Request to Ollama timed out: {exc}") from exc


def check_model_available(base_url: str, model: str) -> bool:
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code != 200:
            return False
        data = response.json()
        model_base = model.split(":")[0]
        for entry in data.get("models", []):
            name = entry.get("name", "")
            if name == model or name.split(":")[0] == model_base:
                return True
        return False
    except Exception:
        return False

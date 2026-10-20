"""Deterministic OpenAI-compatible stub for offline previews.

Serves the subset of the OpenAI REST API that openai==0.27.2 calls from
superpilot: POST /v1/chat/completions (plain or function-calling) and
POST /v1/embeddings. Responses are canned and derived from the request so
runs are repeatable. Point the SDK at it with OPENAI_API_BASE.

Usage: python preview/openai_stub.py [--host 127.0.0.1] [--port 8787]
"""
import argparse
import hashlib
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _last_user_text(messages):
    for message in reversed(messages or []):
        if message.get("role") == "user":
            content = message.get("content") or ""
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            return content
    return ""


def _task_objective(text):
    marker = "Your current task is '"
    if marker in text:
        return text.split(marker, 1)[1].split("'.\n", 1)[0]
    return text.strip().splitlines()[0] if text.strip() else "the request"


def _arguments_for_schema(schema, objective):
    """Build arguments that satisfy a JSON schema's required properties."""
    answer = (
        f"[offline stub] This is a deterministic placeholder answer for "
        f"'{objective}'. No real language model was called."
    )
    args = {}
    properties = (schema.get("parameters") or {}).get("properties") or {}
    for name, prop in properties.items():
        kind = prop.get("type")
        if kind == "array":
            args[name] = [
                f"Stub highlight 1 for '{objective}'",
                f"Stub highlight 2 for '{objective}'",
            ]
        elif kind in ("integer", "number"):
            args[name] = 0
        elif kind == "boolean":
            args[name] = False
        elif kind == "object":
            args[name] = {}
        else:
            args[name] = answer
    return args


def chat_completion(body):
    messages = body.get("messages") or []
    objective = _task_objective(_last_user_text(messages))
    functions = body.get("functions") or []
    if functions:
        function = functions[0]
        call = body.get("function_call")
        if isinstance(call, dict) and call.get("name"):
            function = next(
                (f for f in functions if f.get("name") == call["name"]), function
            )
        message = {
            "role": "assistant",
            "content": None,
            "function_call": {
                "name": function.get("name", "function"),
                "arguments": json.dumps(_arguments_for_schema(function, objective)),
            },
        }
        finish_reason = "function_call"
    else:
        message = {
            "role": "assistant",
            "content": f"[offline stub] Placeholder response for '{objective}'.",
        }
        finish_reason = "stop"
    prompt_tokens = sum(len(str(m.get("content") or "").split()) for m in messages)
    return {
        "id": "chatcmpl-stub-" + hashlib.sha1(objective.encode()).hexdigest()[:12],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "gpt-3.5-turbo"),
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": 20,
            "total_tokens": prompt_tokens + 20,
        },
    }


def embeddings(body):
    inputs = body.get("input") or [""]
    if isinstance(inputs, str):
        inputs = [inputs]
    data = []
    for index, text in enumerate(inputs):
        digest = hashlib.sha256(str(text).encode()).digest()
        data.append(
            {
                "object": "embedding",
                "index": index,
                "embedding": [(b - 128) / 128 for b in digest] * 48,
            }
        )
    return {
        "object": "list",
        "data": data,
        "model": body.get("model", "text-embedding-ada-002"),
        "usage": {"prompt_tokens": len(inputs), "total_tokens": len(inputs)},
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/health", "/v1/models"):
            self._send(200, {"object": "list", "data": [{"id": "gpt-stub"}]})
        else:
            self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": {"message": "invalid JSON"}})
        path = self.path.split("?", 1)[0].rstrip("/")
        if path.endswith("/chat/completions"):
            return self._send(200, chat_completion(body))
        if path.endswith("/embeddings"):
            return self._send(200, embeddings(body))
        self._send(404, {"error": {"message": f"unsupported path {path}"}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"OpenAI stub listening on http://{args.host}:{args.port}/v1", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

# Offline preview of the README flow

superpilot is a library, so the preview is a CLI run of the README quickstart
(`SimpleTaskPilot` answering one query).

```bash
uv venv -p 3.11 .venv && . .venv/bin/activate
uv pip install --no-deps -r preview/requirements.lock
preview/run_readme_flow.sh "What is the weather in Mumbai"
```

Without `OPENAI_API_KEY`, the script starts `preview/openai_stub.py`, a
deterministic OpenAI-compatible stub, and sets `OPENAI_API_BASE` to it. The
answers are placeholders, not model output. Set `OPENAI_API_KEY` to call the
real API instead.

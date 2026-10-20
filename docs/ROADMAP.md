# Superpilot — Project Review & Future Roadmap

_Review date: 2026-10-20 · Reviewed against `main` @ `1940e07` ("Bump Versions", 2024-08-29) and all remote branches._

This document records where Superpilot stands today, what work already exists
outside `main`, the technical debt that blocks the next release, and a phased
roadmap to get from here to a maintained `1.0`. Every finding links back to a
file, branch or commit so it can be checked and kept up to date.

---

## 1. What Superpilot is today

Superpilot (`setup.py`: "The Multi-Role Superpilot Programming Framework",
version `0.5.2`, Python `>=3.10`) is an async Python framework for building LLM
apps out of **prompt strategies**, **abilities** (tools) and **pilots**
(executors). It began as a fork of AutoGPT's `autogpt/core` (credited in the
README) and has grown toward multi-provider, multi-step pipelines.

### Architecture at a glance

```
            ┌──────────────────────────── superpilot/core ─────────────────────────────┐
 query ──▶  │ pilot/task   SimpleTaskPilot · SuperTaskPilot  (one prompt / ability loop) │
            │ pilot/chain  BaseChain · SimpleChain           (handler → transformer ...) │
            │ pilot/super  SuperPilot  (plan → choose ability → execute; AutoGPT-style)  │
            │   │                                                                        │
            │   ├─ planning/strategies   prompt strategies (simple, step_flow, summarizer…)│
            │   ├─ ability               registries (Simple/Super) + builtins             │
            │   ├─ resource/model_providers  OpenAI · Anthropic · Ollama · DeepInfra      │
            │   ├─ context / memory / embedding / workspace / environment / configuration │
            │   └─ plugin · app (executor, thread/app manager)                            │
            └────────────────────────────────────────────────────────────────────────────┘
 superpilot/framework  legacy helpers: sync OpenAI wrapper, tools (search, browser, summarizer,
                       vendored pylatexenc), abilities (text/search summarise), json utils
 superpilot/examples   domain apps: ed_tech question solver, solution QC, tax, prompt generators,
                       thumbnail generator, voiceover, executors (Midjourney, Stable Diffusion…)
 superpilot/app        CLI and CLI-web client/server (inherited from AutoGPT)
 superpilot/tests      runnable scripts (not an automated test suite)
```

### Size

| Area | Python LOC (approx.) |
| --- | --- |
| `superpilot/core` | ~10.8k |
| `superpilot/examples` | ~7.9k |
| Vendored `pylatexenc` (`framework/tools/latex/pylatexenc`, 56 files) | ~23.7k |
| Whole package | ~51k |

Almost half the code by line count is the vendored LaTeX library.

### Model providers on `main`

`ModelProviderName` (`core/resource/model_providers/schema.py`) lists OpenAI,
Anthropic, HuggingFace, Ollama, Together and DeepInfra. Only **OpenAI,
Anthropic, Ollama and DeepInfra** have implementations. The model registries are
frozen in early-to-mid 2024: OpenAI goes up to `gpt-4o` / `gpt-4o-mini`, and
Anthropic up to the Claude 3 family (`anthropic==0.19.1`).

### Verified behaviour

The README quickstart (`SimpleTaskPilot` answering a single query) runs end to
end with the offline harness on branch `ls/1-set-up-preview-environment-KvNu`
(`preview/run_readme_flow.sh`, which uses a deterministic OpenAI stub). The
default model it resolves to is `gpt-4-0613`.

### Activity

220 commits on `main` from 2023-08-27 to 2024-08-29. Most of them landed in
Sep 2023 (106) and May 2024 (28). After Aug 2024 development continued **only on
feature branches** (see §2), the latest being `channels` on 2025-02-24. `main`
has had no commits for over two years.

---

## 2. Work that already exists outside `main`

The repo has more than 50 remote branches. These ones contain substantial unmerged work,
and together they show where the project was heading:

| Theme | Branch(es) | Ahead of `main` | Last commit | What it adds |
| --- | --- | --- | --- | --- |
| **OpenAI SDK v1 upgrade** | `openai_upgrade`, `openai_upgrade_only`, `version-1.0.0` | 6–12 | 2024-11-12 | Ports providers and `framework/llm` to `openai>=1`, `pydantic>=2` |
| Tool/"gentools" support | `gentools_support` | 13 | 2024-11-14 | Builds on `openai_upgrade` |
| **Events / callbacks & state** | `state_implementation*`, `context_next_ability*`, `chain-implementation` | 32–67 | 2024-01 | `core/callback` (handlers, managers, std-io runner), chain lifecycle events, state save |
| **Blocks (low-code steps)** | `block_implementation`, `clean_block_implementation`, `test_sql_block`, `excel_generation` | 16–31 | 2024-09 | `core/block` with `llm_block`, `api_block`, `form_block`, `invoice_ocr_block`, SQL/Excel blocks |
| **Dynamic abilities / workflows** | `dynamic_ability`, `notebook_llm_execution`, `version-1.0.1` | 10–87 | 2024-06 | Abilities built at runtime, notebook execution, separate ability keyword args |
| **Multi-agent / planner** | `multi_agents`, `planner-implementation`, `multi_ai` | 39–85 | 2024-12-03 | Sequential multi-plan execution, start/end events, "SuperEmail implemented with Superchain" |
| **Knowledge store / RAG** | `memory_implementation`, `ai_ranker`, `evaluation`, `module` | 54–101 | 2024-11-06 | `core/store`: indexing pipeline, chunker, embedder, Vespa & ClickHouse document indexes, search pipeline, llama_index, persona generation/ranking, "Response with Citations" |
| **Channels & voice** | `channels` | 272 (no merge base) | 2025-02-24 | `examples/channels`: email processing, Outlook, Discord bot; Vapi, Groq + LiveKit, ElevenLabs voice |
| Provider: Together AI | `together_ai` | 13 | 2024-05-11 | Together provider (enum exists on `main`, impl does not) |
| Formatting / docs | `main-devin`, `devin/*` | 4 | 2024-12-12 | Black formatting, README update |

**Key observation:** the forward work has splintered. Several branches share
history (`multi_agents` and `context_next_ability_open_ai_update` point at the
same commit; `memory_implementation` and `ai_ranker` both feed `evaluation`, and
`module` forks from `evaluation`'s history on 2024-10-26), and `channels` has **no merge base with `main`** because
its history was rewritten. Before any roadmap item ships, the project has to pick
a trunk again (Phase 0).

---

## 3. Gaps & technical debt on `main`

### 3.1 Dependencies (biggest blocker)

- **`openai==0.27.2`**: the pre-v1 SDK. `openai.ChatCompletion.acreate` /
  `openai.Embedding.acreate` are used in `core/resource/model_providers/openai.py`,
  `deepinfra.py` and `framework/llm/providers/openai.py`. These calls don't exist
  in current SDKs, so the library can't share an environment with modern tooling.
- `anthropic==0.19.1`, `langchain==0.0.202`, `tiktoken==0.3.3`, `httpx==0.23.3`,
  `pyautogen==0.1.14`, `typing-extensions==4.5.0` are pinned to 2023-era versions.
- `requirements.txt` puts **app-specific dependencies in the core install**:
  selenium, playwright, tweepy, supabase, gTTS, playsound, pytesseract, newspaper3k,
  md2pdf, and others. `setup.py` also adds `setfit` from a **git URL**, which PyPI
  rejects for published packages.

### 3.2 Correctness bugs spotted in review

- `OpenAIModelName.GPT3_16K` registers `name=OpenAIModelName.GPT3`, so the 16k
  entry resolves to the 4k model (`openai.py`, ~line 83).
- `AnthropicModelName.CLAUD_3_HAIKU = "claude-3-sonnet-20240229"`: Haiku points
  at Sonnet (`anthropic_api.py:43`).
- `ModelProviderService.IMAGE` and `.VIDEO` both equal `"text"` (`schema.py:26-27`).
- Cost estimation has a hard-coded fudge factor (`schema.py:212`, "TODO: Fit this").
- Embeddings are disabled for Anthropic and Ollama (`anthropic_api.py:197`,
  `ollama_api.py:178`).
- `BaseChain.execute` swallows handler exceptions and continues, which hides failures
  (`core/pilot/chain/base.py`).

### 3.3 Architecture duplication

- `core/pilot/super.py`, `core/agent/simple.py` and `core/agent/research.py`
  repeat the same AutoGPT loop with the same unfinished TODOs: memory lookup,
  task evaluation, knowledge summarisation, completion checks.
- There are two LLM layers: the async `core/resource/model_providers` and the
  sync `framework/llm`.
- `core/_deprecated/` and the AutoGPT-inherited `app/cli_web_app` are still shipped.
- `SimpleMemory` only loads a `message_history.json`. There is no retrieval
  memory on `main`.

### 3.4 Quality & delivery

- **No automated tests or CI.** `superpilot/tests/*.py` are runnable scripts with
  `sys.path.insert` hacks (21 files). They need live API keys and contain no
  assertions. There's a `.pre-commit-config.yaml` (black, flake8, bandit) but
  no workflow enforces it.
- **Packaging:** `setup.py` only (no `pyproject.toml`), and the version is hard-coded
  (`0.5.2`). Tags stop at `0.4.8`, while branches named `version-1.0.x` exist but
  are not released.
- **Repo hygiene:** data files ship inside the package (`superpilot/docs/*.csv|xlsx`).
  Domain examples (tax, ed-tech, Chegg QC, thumbnail) live inside the library,
  along with a root-level `check_file.py` script. The vendored `pylatexenc` is ~24k LOC.
- **Docs drift:** the README imports `superpilot.tests.test_env_simple` as a public
  API and doesn't document chains, multiple providers or the model factory.

---

## 4. Roadmap

Phases are ordered by dependency rather than by date. Each phase lists its exit criteria.

### Phase 0: Re-establish a trunk (prerequisite)

1. Pick the integration base. **Recommendation:** start from `main`, merge
   `openai_upgrade` first (smallest, foundational), then rebase themed work onto it.
2. Triage every branch in §2 into *merge*, *salvage into a new PR*, or *archive*.
   Write the decision up in `docs/BRANCHES.md`, then delete or tag the archived branches.
3. `channels` has no merge base. Port its `examples/channels` tree as fresh
   commits instead of merging histories, and remove committed keys (see its last
   commit, "removed keys"; also rotate any keys that were ever pushed).

_Exit:_ one active trunk, a short list of open feature branches, every branch's
fate recorded.

### Phase 1: Foundation & release hygiene (target `0.6`)

1. **SDK upgrades:** land `openai>=1` and `pydantic>=2` (existing work on
   `openai_upgrade`), upgrade `anthropic`, and drop or upgrade `langchain==0.0.202`.
   Retire the sync `framework/llm` layer, or make it a thin wrapper over the
   async providers.
2. **Fix the §3.2 bugs** and refresh the model registries. Ideally load model
   metadata (context window, pricing) from data, so a new model doesn't need a code
   release.
3. **Slim the install:** keep the core dependencies minimal and move the rest into extras
   (`superpilot[search]`, `[browser]`, `[voice]`, `[latex]`, `[autogen]`, `[store]`).
   Remove the `setfit` git dependency from `install_requires`.
4. **Packaging:** move to a `pyproject.toml`, use a single-source version, and add a
   PyPI publish workflow. Tag releases again.
5. **Tests & CI:** turn `superpilot/tests` into pytest with a recorded or stubbed
   provider (the offline OpenAI stub in `preview/` is a starting point). Move the
   live-key scripts to `scripts/` or `examples/`. Add a GitHub Actions workflow that runs
   pre-commit and pytest on 3.10–3.12.
6. **Docs:** fix the README imports and add pages for providers, chains and abilities.

_Exit:_ `pip install superpilot` works in a clean, modern environment, CI is green,
and the README quickstart is covered by a test.

### Phase 2: Core runtime (target `0.7`)

1. **One pilot loop.** Merge `SuperPilot`, `core/agent/simple.py` and
   `core/agent/research.py` into a single planner/executor, and delete the duplicates
   and `core/_deprecated`.
2. **Events & state:** land `core/callback` (from the `state_implementation`
   / `multi_agents` line) so every pilot, chain and ability emits
   start/end/error events. Use it for logging, cost tracking and persistence.
3. **Native tool calling & structured output:** replace prompt-parsed ability
   selection with provider function or tool calling and schema-validated outputs.
   Build on `gentools_support`.
4. **Chains that fail loudly:** make error policy configurable in `BaseChain`
   (fail, skip, retry) instead of always swallowing exceptions. Add parallel steps,
   as sketched in the comments of `tests/test_readme.py`.
5. **Streaming** responses through pilots and chains.

_Exit:_ one documented execution model, with events, tool calling and streaming
covered by tests.

### Phase 3: Composition, multi-agent & memory (target `0.8`)

1. **Blocks:** land `core/block` (LLM, API, form, OCR, SQL, Excel blocks) as the
   declarative building unit for workflows, alongside `dynamic_ability`.
2. **Multi-agent orchestration:** land the planner and sequential-plan work from
   `multi_agents` ("SuperChain"). Define agent hand-off over the shared `Context`.
3. **Memory & knowledge store:** land `core/store` (chunking, embedding, indexing,
   search) behind a small interface. Ship a lightweight default backend and make
   Vespa/ClickHouse optional extras. Wire it into the pilot loop's "look up relevant
   memories" step (the TODO in `core/pilot/super.py`).
4. **Evaluation:** land citations and answer-quality evaluation from `evaluation`,
   and add a regression-eval harness for prompts.

_Exit:_ a multi-step, multi-agent workflow can retrieve from a knowledge store and
cite its sources, with an eval suite tracking quality.

### Phase 4: Channels & ecosystem (target `1.0`)

1. **Channels:** provide a channel adapter interface (email, Outlook, Discord, voice).
   Port the `channels` branch implementations behind it (Vapi, LiveKit + Groq,
   ElevenLabs) as optional extras.
2. **Providers:** finish Together and HuggingFace (the enums exist with no
   implementation). Add the current OpenAI, Anthropic and open-weights models through the
   data-driven registry.
3. **Split examples out:** move domain apps (ed-tech, tax, solution QC, thumbnail,
   voiceover, prompt generators) and their data files into an `examples/` top-level
   directory or a separate repo, so they stop shipping inside the library wheel.
   Consider replacing the vendored `pylatexenc` with the PyPI package.
4. **Observability:** expose per-run cost, token and latency reporting through the
   callback system. Optionally add an OpenTelemetry exporter.
5. **API stability:** document the public API surface, add deprecation policy, and
   cut `1.0`.

_Exit:_ a stable, documented `1.0` with pluggable providers, channels and stores.

---

## 5. Suggested priority order (first ten items)

1. Phase 0 branch triage and trunk decision.
2. Merge `openai_upgrade` (OpenAI v1 + pydantic v2).
3. Fix the model-registry bugs (§3.2) and refresh the model lists.
4. pytest + offline stub + GitHub Actions CI.
5. Dependency extras and `pyproject.toml`; publish `0.6`.
6. Unify the pilot loop and remove the duplicates.
7. Land callbacks/events.
8. Native tool calling and structured output.
9. Land the `core/store` memory with a lightweight default backend.
10. Port `channels` as optional adapters.

## 6. Open questions for maintainers

- Is `channels` (voice/email/Discord) the product direction, or a client project
  that belongs in a separate repo?
- Should the domain examples (ed-tech, tax, QC) stay public in this repo?
- Which vector backend should be the default: Vespa (existing work), or something
  lighter for local use?
- Is AutoGPT compatibility still a goal, or can the inherited `app/` CLI and
  `_deprecated` code be dropped?

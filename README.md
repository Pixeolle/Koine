# Koine

Turns a codebase into documentation by parsing it into a graph and summarizing that graph bottom-up — keeping LLM context usage bounded regardless of repository size.

## The problem

Feeding a codebase directly to an LLM does not scale: context windows are finite, and a naive approach either truncates the input or drowns the model in irrelevant code. Producing documentation that actually reflects how a codebase is structured — not just what each file happens to contain — requires understanding it as a whole before writing anything.

## How it works

**1. Parse.** The codebase is parsed with Tree-sitter into atomic units — functions, classes, modules — rather than treated as flat text.

**2. Link.** A dependency linker resolves relationships between these units, producing a graph that is more macro than a raw AST: it captures how code actually depends on other code, not just its syntax tree. The linker sits behind a port — the current implementation is built on Jedi, but nothing else in the pipeline depends on that specific choice.

**3. Summarize, bottom-up.** The graph is walked in topological order. Each node is summarized once its children have already been processed, so a summary at any level only ever depends on already-condensed information below it — never on raw, unprocessed source. This is what keeps context bounded as the graph grows: the pipeline scales with documentation depth, not with repository size.

**4. Write, in a bounded loop.** Three agent roles collaborate to turn the graph into documentation:

- **Structurer** — plans the documentation's structure from the graph.
- **Writer** — drafts content, querying the graph directly through tools to ground its answers in the actual code rather than relying on context stuffed into the prompt.
- **Judge** — reviews drafts and sends them back to the Writer when necessary.

The loop runs for a bounded number of iterations and exits as soon as no draft remains — a hard ceiling that guarantees termination without relying on the model to decide when it's "done."

**5. Explore.** Generated documentation is served through a FastAPI backend and explored through a web frontend (Astro, Svelte), which also supports chatting directly with the generated documentation.

## Architecture

The backend follows a hexagonal (ports & adapters) architecture. Core logic depends only on interfaces, never on specific tools:

```
application/ports/        interfaces: parser, linker, graph_engine, llm_client,
                           llm_tokenizer, document_repository, repository_fetcher,
                           source_code_provider, progress_reporter

infrastructure/adapters/  implementations: Tree-sitter, Jedi, Memgraph (via a
                           Neo4j-compatible driver), rustworkx, an OpenAI-compatible
                           client, a Mistral tokenizer, SQLite
```

Any of these can be swapped — a different graph database, a different LLM provider, a different parser — without touching the domain logic that orchestrates them.

## Tech stack

| Concern | Tools |
|---|---|
| Parsing & linking | Tree-sitter, Jedi |
| Graph | Memgraph, rustworkx |
| Agent orchestration | LangGraph |
| Storage | SQLite (SQLModel) |
| API | FastAPI |
| Frontend | Astro, Svelte |
| Infra | Docker, uv, pnpm |

## Status

This is a working proof of concept: the pipeline runs end-to-end and produces real documentation, but it has not been hardened for production use. It is not designed for real-time generation — documentation runs are expected to take time proportional to the size and depth of the codebase being processed, the same way a human writing that documentation would.

## Origin

The idea of representing a codebase as a graph and processing it hierarchically to preserve architectural context comes from [CodeWiki](https://github.com/FSoft-AI4Code/CodeWiki). Koine started from that idea, not that codebase: the graph construction, the topological summarization strategy, and the agent pipeline described above are an independent, from-scratch implementation.

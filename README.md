# polylith-keyvaluestore

A URL shortener built as a **case study for combining two architectural
ideas**: the *Polylith* workspace structure and *Functional Core, Imperative
Shell* (FCIS). We built it to evaluate whether this combination is a good fit
for our team's upcoming projects.

Zero prior knowledge of either idea is assumed — this README explains both
concepts, shows how this repository puts them to work, and tells you what we
observed while building it.

## The 60-second summary

- **Polylith** is a way to organize a repository into reusable building
  blocks ("bricks"): *components* bundle a small public interface with one
  responsibility, and *bases* are the thin shells that expose the
  functionality to the outside world (HTTP, CLI, ...). A tool
  (`poly`, the `polylith-cli` Python implementation) verifies that no brick
  reaches into another brick's internals.
- **Functional Core, Imperative Shell** says: put all decisions and business
  logic in pure functions that take data and return data, and push all I/O
  and side effects (HTTP, databases, env vars, clocks, randomness) to the
  edges of the system.
- **How they combine:** Polylith tells you *where* code lives; FCIS tells
  you *which kind* of code lives there. Bricks make the seams physical, FCIS
  keeps the logic on the pure side of them. Together they yield systems
  that are almost entirely testable without mocks.

The URL shortener here is deliberately small but structurally complete:
two components, two bases sharing one core, one deployable, and a
swappable persistence backend.

## Running it

All commands run from the repo root; [uv](https://docs.astral.sh/uv/) handles
Python and dependencies.

```bash
uv sync                 # set up the environment
uv run pytest           # run all tests (70 at the time of writing)
```

**CLI** (uses the in-memory backend by default):

```bash
uv run python -m my_namespace.urlshortener_cli shorten https://example.com/a/very/long/url
# -> http://localhost:8000/vAqiItJ
```

Note that the default backend is in-process: state lives only inside one
command run. To `resolve` a code in a later invocation — or to share links
with the HTTP service — run the CLI against redis:

```bash
KV_BACKEND=redis uv run python -m my_namespace.urlshortener_cli resolve vAqiItJ
```

**HTTP API** (FastAPI; `POST /shorten`, `GET /{code}` redirect, `GET /healthz`):

```bash
uv run uvicorn my_namespace.urlshortener_api.app:create_app --factory
```

**Choosing the backend.** Both shells build their store through one factory,
driven by environment variables. Locally no Redis is needed; in production
nothing changes except the environment:

```bash
KV_BACKEND=memory   # default: in-process store, empty on every restart
KV_BACKEND=redis KV_REDIS_URL=redis://localhost:6379/0   # persistent, shared
```

Build the deployable wheel and you get a `urlshortener` console script:

```bash
uv build --project projects/urlshortener
```

## The two ideas, and how this repo applies them

### Polylith: bricks and interfaces

```
workspace (= this repo)
├── components/                    # reusable bricks, one responsibility each
│   ├── my_namespace/keyvaluestore/     # persistence port + 2 adapters
│   └── my_namespace/shortener/        # pure domain logic
├── bases/                         # shells that face the outside world
│   ├── my_namespace/urlshortener_api/  # FastAPI HTTP service
│   └── my_namespace/urlshortener_cli/  # argparse CLI
├── projects/
│   └── urlshortener/              # the deployable: base(s) + components + deps
└── test/                          # tests, mirroring the brick layout
```

The Polylith rules that matter for a reader:

1. **Every component defines an interface** and everything outside it may
   only use that interface — in Python terms, you import from the
   component's package, never from its internals.
2. **Bases contain no business logic.** They translate between the outside
   world and component interfaces.
3. **A project is just a wiring manifest**: which bricks go together for a
   deployable, plus its third-party dependencies. `uv run poly check`
   verifies the whole graph; `uv run poly info` prints it as a table.

### FCIS: decisions are pure, effects are at the edge

Mapping the idea onto the bricks:

| FCIS role | In this repo |
|---|---|
| Functional core | `my_namespace/shortener`: URL validation, code generation, the shorten/resolve orchestration. Takes data in, returns data (or raises domain errors). |
| Port (the seam) | `KeyValueStore` protocol in `my_namespace/keyvaluestore`: the only way the core touches persistence. |
| Adapters | `InMemoryStore` (local dev) and `RedisStore` (production), both satisfying one contract test suite. |
| Imperative shell(s) | The two bases: HTTP statuses and redirects, CLI output and exit codes, error mapping. |
| Composition root | `keyvaluestore.create_store()` + the project/entry point: where *which adapter* and *which backend* is decided (here: from env vars). |

A concrete requirement shows the mechanics: shortening must never
overwrite an existing code, even under concurrent calls. The core therefore
claims codes with `store.set_if_absent(code, url) -> bool`. For Redis that
is the atomic `SET NX` command; for the in-memory store it is a plain
check. The core does not know or care which one runs — that is the entire
point of both ideas at once.

## Why we think the combination works

What we actually observed while building this:

- **Almost no mocks anywhere.** The core is tested against a real
  in-memory adapter (part of the codebase, not a test stub); the HTTP
  shell tests run through the full stack with a store injected at the app
  factory. 70 tests, zero redis servers, zero mocking frameworks.
- **Contract tests keep adapters interchangeable.** Both stores run the
  *same* suite of contract tests, so "works with Redis" and "works locally"
  cannot drift apart.
- **One core fed two shells nearly for free.** The CLI base reuses the
  exact domain code of the HTTP base: ~50 lines of argparse and nothing
  else. No logic was copied to support a second interface to the same
  feature.
- **Interfaces evolved cheaply.** When the atomic-em requirement appeared,
  the change was: one method on the protocol, four lines per adapter, three
  contract tests, one call site in the core. The blast radius of a
  contract change is the *shape of the interface*, visible in `poly check`.
- **Local development stays dependencies-light.** No Redis install to
  develop, test, or demo; one env var switches the backend in production.
  The Redis client library is even imported lazily, so memory-only
  environments never load it.

## Honest friction points (mostly Python-specific)

- The Polylith tooling is an interactive CLI that expects to answer "which
  bricks belong to this project?" in prompts; wiring project manifests by
  hand is sometimes faster and more predictable.
- Polylith's boundaries are enforced at the *import* level
  (`uv run poly check`), but neither Polylith nor Python's type system
  enforces the FCIS discipline itself — nothing stops you from putting I/O
  in the middle of a component. The structure gives you the seams; keeping
  the logic on the pure side of them remains a (review-enforced) habit.
- The component dependency direction is not inferred automatically: you
  declare that a base uses a component by adding it to the project
  manifest, and `poly check` then verifies the graph stays legal.
- Small naming frictions: the scaffold uses a placeholder namespace
  (`my_namespace`) and per-brick tooling (`hatch-polylith-bricks`) that is
  new even to experienced Python teams.

## Repository tour (reading order)

1. `components/my_namespace/shortener/core.py` — the functional core; the
   shortest complete demonstration of both ideas working together.
2. `components/my_namespace/keyvaluestore/interface.py` — the port, in what
   the core is allowed to call.
3. `components/my_namespace/keyvaluestore/memory.py` and `redis.py` — the
   two adapters; note how small the difference between them really is.
4. `bases/my_namespace/urlshortener_api/app.py` — the imperative shell in
   the HTTP flavor: a factory, three routes, and error mapping only.
5. `bases/my_namespace/urlshortener_cli/core.py` — the same shell in CLI
   flavor, to see the core reused.
6. `test/` — mirrors the brick layout; start with
   `test/components/my_namespace/keyvaluestore/test_contract.py` to see
   how one suite pins both adapters to identical behavior.
7. `projects/urlshortener/pyproject.toml` — a whole deployable in ~40
   lines: dependencies plus a list of bricks.

## Cheat sheet

```bash
# brick management
uv run poly create component --name my_component   # new component
uv run poly create base --name my_base              # new base
uv run poly create project --name my_project       # new deployable manifest
uv run poly sync              # update project manifests with new bricks
uv run poly check             # verify the workspace: illegal imports, missing bricks
uv run poly info              # print the brick/project table

# tests
uv run pytest
```

## Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `KV_BACKEND` | `memory` or `redis` | `memory` |
| `KV_REDIS_URL` | Redis connection string for the redis backend | `redis://localhost:6379/0` |

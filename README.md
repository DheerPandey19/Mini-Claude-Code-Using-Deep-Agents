# Mini Claude Code (Deep Agents)

A learning project: a small Claude Code-style coding agent built with
[LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview)
and OpenAI.

You chat in the terminal. The agent can explore and edit files in a project
folder and run shell commands (with your approval). Most of the "agent loop"
(tools, subagents, planning hooks) comes from Deep Agents; this repo is a thin
wrapper around it.

## Project layout

```text
mini claude code/
  pyproject.toml              # package + mini-claude entrypoint
  .env.example                # env template (safe to commit)
  .env                        # your secrets (gitignored)
  .gitignore
  README.md
  src/mini_claude/
    __init__.py
    __main__.py               # python -m mini_claude
    prompts.py                # CODING_PROMPT + EXPLORER_PROMPT
    agent.py                  # create_deep_agent, SqliteSaver, explorer
    tools.py                  # custom git_status tool
    cli.py                    # REPL, streaming, slash commands, HITL
  .mini-claude/               # runtime data (gitignored): checkpoints + thread id
```

| File | Role |
| --- | --- |
| `prompts.py` | Parent coding prompt; read-only explorer prompt |
| `agent.py` | Harness: backend, checkpointer, `git_status`, explorer subagent, HITL |
| `tools.py` | Custom tool the model can call instead of `execute` for `git status` |
| `cli.py` | Env, chat, token vs tool streaming, `/help` `/new` `/exit`, approvals |

## What Deep Agents provides (you don't implement these)

- Filesystem tools: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, …
- Shell: `execute` (via `LocalShellBackend`)
- Subagent delegation: `task`
- Human-in-the-loop when `interrupt_on` is set
- Checkpointer API (this repo uses SQLite, not in-memory)

## What this repo adds

- **Backend** — `LocalShellBackend`: real project files + host shell
- **Checkpointer** — `SqliteSaver` in `.mini-claude/checkpoints.sqlite`; chat survives restart
- **Thread** — saved in `.mini-claude/thread_id`, or pass `--thread`; `/new` starts a fresh page
- **HITL** — approve `execute`, `write_file`, `edit_file`, and `delete`
- **Custom tool** — `git_status`
- **Custom subagent** — `explorer`: read-only (`ls` / `glob` / `grep` / `read_file`); parent calls `task`
- **CLI** — streams model text as `agent>` and tool names as `tool>`; slash commands

## Setup

1. Python 3.11+
2. Copy the env template and add your key:

   ```powershell
   copy .env.example .env
   ```

   Edit `.env`:

   ```env
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o
   ```

3. Install from the repo root:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -e .
   ```

## Run

```powershell
mini-claude --cwd .
```

Point `--cwd` at any project folder (this repo is small; a larger tree is a better test for explorer).

One-shot:

```powershell
mini-claude --cwd . "List the Python files in this project"
```

Or:

```powershell
python -m mini_claude --cwd .
```

Fresh conversation (does not reuse the saved thread):

```powershell
mini-claude --cwd . --thread explorer-test
```

In the REPL: `/help`, `/new` (new thread id), `/exit`. `exit` / `quit` still work.

When the agent wants to run a gated tool, you'll see **Approve? [y/N]**.

To see the explorer: `/new`, then ask to map the repo. You should see `tool> task` and a short report, not a raw file dump.

## Security

`LocalShellBackend` runs commands as your user. Filesystem tools are rooted at
`--cwd` (with `virtual_mode=True`), but `execute` is not a sandbox. Only approve
commands you understand. Do not commit `.env`. There is no path allow/deny list
yet (`.env` is not blocked by the agent).

## Status

Learning build past v1. In place:

- Coding prompt + explorer prompt
- Agent factory with SQLite checkpoints
- CLI with streaming, slash commands, and HITL on shell and file writes
- Custom `git_status` tool
- Custom read-only `explorer` subagent (`task`)

Not built yet (sensible next lessons):

- `AGENTS.md` memory (project conventions every run)
- Skills (`SKILL.md`, loaded on demand)
- Path permissions (block `.env` / `.git`)
- MCP tools
- Extra specialists (e.g. a reviewer)
- Tests (no pytest suite in this repo)

## FAQ

- **What models can I use?** Any OpenAI-compatible model via `OPENAI_MODEL` in `.env` (prefixed as `openai:…` if you omit the provider).
- **How do I update dependencies?** Change `pyproject.toml` and run `pip install -e .`.
- **Why does chat remember the last session?** SQLite + a saved `thread_id`. Use `/new` or `--thread some-id` for a blank conversation.

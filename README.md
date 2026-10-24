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
    prompts.py                # coding system prompt
    agent.py                  # create_deep_agent + LocalShellBackend
    cli.py                    # REPL, one-shot, HITL approve/reject
```

| File | Role |
| --- | --- |
| `prompts.py` | Instructs explore-first, small edits, careful shell use |
| `agent.py` | Builds the Deep Agents harness for a given project root |
| `cli.py` | Loads env, runs chat, handles `__interrupt__` for `execute` |

## What Deep Agents provides (you don't implement these)

- Filesystem tools: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, …
- Shell: `execute` (via `LocalShellBackend`)
- Subagent delegation: `task`
- Human-in-the-loop when `interrupt_on` is set
- In-session memory via a checkpointer (`MemorySaver` here)

## Concepts in this repo

- **Backend** — `LocalShellBackend`: real project files + host shell
- **Checkpointer** — `MemorySaver`: multi-turn chat while the process is alive
- **HITL** — `interrupt_on={"execute": True}`: CLI asks y/n before shell runs
- **Your code** — prompt, agent factory, terminal UI; not the tool runtime

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

One-shot:

```powershell
mini-claude --cwd . "List the Python files in this project"
```

Or:

```powershell
python -m mini_claude --cwd .
```

Type `exit` or `quit` to leave. When the agent wants to run a shell command,
you'll see **Approve? [y/N]**.

## Security

`LocalShellBackend` runs commands as your user. Filesystem tools are rooted at
`--cwd` (with `virtual_mode=True`), but `execute` is not a sandbox. Only approve
commands you understand. Do not commit `.env`.

## Testing Instructions

- Run tests by executing: `pytest`
- Ensure all tests pass before making changes.
- Review test coverage to ensure all features are covered.

## Contributing Guide

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes with clear messages.
4. Submit a pull request for review.

## FAQ

- **What models can I use?**
  You can specify any model in the `.env` file that is compatible with your use case.
- **How to update dependencies?**
  Update `pyproject.toml` and run `pip install -e .`.

## Detailed Usage Examples

- Run a one-shot command:
  ```powershell
  mini-claude --cwd . "List the Python files in this project"
  ```
- Start a terminal session:
  ```powershell
  python -m mini_claude --cwd .
  ```

## Status

v1 learning build is complete: prompt + agent + CLI with shell approval.

Possible next steps (optional): streaming output, durable checkpointer, custom
tools, gate file writes, MCP, skills.
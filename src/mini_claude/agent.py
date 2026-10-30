from pathlib import Path
import sqlite3

from deepagents.middleware import FilesystemMiddleware
from mini_claude.tools import make_git_status
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langgraph.checkpoint.sqlite import SqliteSaver

from mini_claude.prompts import CODING_PROMPT, EXPLORER_PROMPT


def build_agent(root_dir: str | Path, model: str):
    """Create a coding agent rooted at ``root_dir``."""
    root = Path(root_dir).resolve()

    db_dir = root / ".mini-claude"
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(db_dir / "checkpoints.sqlite"),
        check_same_thread=False,
    )

    backend = LocalShellBackend(
        root_dir=str(root),
        virtual_mode=True,
        inherit_env=True,
    )

    explorer = {
        "name": "explorer",
        "description": (
            "Map a codebase: list files, read key modules, report structure. "
            "Use for orientation, not for editing or running commands."
        ),
        "system_prompt": EXPLORER_PROMPT,
        "middleware": [
            FilesystemMiddleware(
                backend=backend,
                tools=["read_file", "ls", "glob", "grep"],
            )
        ],
    }

    return create_deep_agent(
        model=model,
        backend=backend,
        system_prompt=CODING_PROMPT,
        checkpointer=SqliteSaver(conn),
        tools=[make_git_status(root)],
        subagents=[explorer],
        interrupt_on={
            "execute": True,
            "write_file": True,
            "edit_file": True,
            "delete": True,
        },
    )

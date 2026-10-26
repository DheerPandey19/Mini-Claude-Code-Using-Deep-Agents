from pathlib import Path
import sqlite3

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langgraph.checkpoint.sqlite import SqliteSaver

from mini_claude.prompts import CODING_PROMPT


def build_agent(root_dir: str | Path, model: str):
    """Create a coding agent rooted at ``root_dir``."""
    root = Path(root_dir).resolve()

    db_dir = root/ ".mini-claude"
    db_dir.mkdir(parents=True,exist_ok=True)
    conn = sqlite3.connect(
        str(db_dir/ "checkpoints.sqlite"),
        check_same_thread=False,
    )
    return create_deep_agent(
        model=model,
        backend=LocalShellBackend(
            root_dir=str(root),
            virtual_mode=True,
            inherit_env=True,
        ),
        system_prompt=CODING_PROMPT,
        checkpointer=SqliteSaver(conn),
        interrupt_on={
            "execute": True,
            "write_file": True,
            "edit_file": True,
            "delete": True
            },
    )
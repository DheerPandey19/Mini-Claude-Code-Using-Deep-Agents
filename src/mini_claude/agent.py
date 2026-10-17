from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langgraph.checkpoint.memory import MemorySaver

from mini_claude.prompts import CODING_PROMPT


def build_agent(root_dir: str | Path, model: str):
    """Create a coding agent rooted at ``root_dir``."""
    root = Path(root_dir).resolve()

    return create_deep_agent(
        model=model,
        backend=LocalShellBackend(
            root_dir=str(root),
            virtual_mode=True,
            inherit_env=True,
        ),
        system_prompt=CODING_PROMPT,
        checkpointer=MemorySaver(),
        interrupt_on={"execute": True},
    )
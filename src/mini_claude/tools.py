
import subprocess
from pathlib import Path
def make_git_status(root: Path):
    def git_status() -> str:
        """Show git status for this project (branch, staged, unstaged, untracked)."""

        result = subprocess.run(
            ["git","status"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if result.returncode!=0:
            return (result.stderr or result.stdout or "git status failed").strip()
        return (result.stdout or "working tree clean").strip()

    return git_status
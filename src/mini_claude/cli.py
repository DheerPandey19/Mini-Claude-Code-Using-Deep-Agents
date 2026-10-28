import argparse
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langgraph.types import Command

from mini_claude.agent import build_agent

def _thread_id(root: Path, requested: str | None) -> str:
    if requested:
        return requested
    path = root / ".mini-claude" / "thread_id"
    if path.exists():
        saved = path.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    new_id = str(uuid.uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_id, encoding="utf-8")
    return new_id

def _new_thread_id(root: Path) -> str:
    path = root / ".mini-claude" / "thread_id"
    new_id = str(uuid.uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_id, encoding="utf-8")
    return new_id

def _is_ai_token(token) -> bool:
    return getattr(token, "type", "") in {"ai", "AIMessageChunk"}

def _tool_name(token) -> str | None:
    if getattr(token, "type", "") in {"tool", "ToolMessageChunk"}:
        return getattr(token, "name", None) or "tool"
    return None

def _print_chunk_content(content) -> None:
    if not content:
        return
    if isinstance(content, str):
        print(content, end="", flush=True)
        return
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                print(block.get("text", ""), end="", flush=True)
            elif isinstance(block, str):
                print(block, end="", flush=True)
        return
    print(content, end="", flush=True)


def _ask_decisions(action_requests: list[dict]) -> list[dict]:
    decisions = []
    for action in action_requests:
        name = action.get("name", "tool")
        args = action.get("args", {})
        print("\n--- Approval needed ---")
        print(f"Tool: {name}")
        print(f"Args: {args}")
        answer = input("Approve? [y/N] ").strip().lower()
        if answer in {"y", "yes"}:
            decisions.append({"type": "approve"})
        else:
            decisions.append(
                {
                    "type": "reject",
                    "message": f"User rejected `{name}`. Do not retry unless asked.",
                }
            )
    return decisions


def run_turn(agent, user_text: str, config: dict) -> None:
    payload = {"messages": [{"role": "user", "content": user_text}]}

    while True:
        interrupted = False
        on_agent_line = False

        try:
            for mode, data in agent.stream(
                payload,
                config=config,
                stream_mode=["messages", "updates"],
            ):
                if mode == "messages":
                    token, _metadata = data
                    name = _tool_name(token)
                    if name:
                        print(f"\ntool> {name}")
                        on_agent_line = False
                        continue
                    if not _is_ai_token(token):
                        continue
                    content = getattr(token, "content", None)
                    if not content:
                        continue
                    if not on_agent_line:
                        print("agent> ", end="", flush=True)
                        on_agent_line = True
                    _print_chunk_content(content)
                elif mode == "updates" and isinstance(data, dict) and "__interrupt__" in data:
                    interrupt_value = data["__interrupt__"][0].value
                    decisions = _ask_decisions(interrupt_value["action_requests"])
                    payload = Command(resume={"decisions": decisions})
                    interrupted = True
                    break
        except Exception as e:
            print(f"\nError {e}")
            return

        print()
        if not interrupted:
            break


def main() -> None:

    load_dotenv()

    parser = argparse.ArgumentParser(description="Mini Claude Code (Deep Agents)")
    parser.add_argument("prompt", nargs="?", help="One-shot prompt (optional)")
    parser.add_argument(
        "--thread",
        default=None,
        help="Conversation id (default: saved in .mini-claude/thread_id)",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Project directory for the agent (default: current dir)",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY. Put it in a .env file.")

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    model = model_name if ":" in model_name else f"openai:{model_name}"

    root = Path(args.cwd).resolve()
    agent = build_agent(root_dir=root, model=model)
    thread_id = _thread_id(root, args.thread)
    config = {"configurable": {"thread_id": thread_id}}

    print(f"Mini Claude — project: {root}")
    print(f"Model: {model}")
    print(f"Thread id : {thread_id}")
    print("Type /help for commands.\n")

    if args.prompt:
        run_turn(agent, args.prompt, config)
        return

    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_text:
            continue

        if user_text.startswith("/"):
            cmd = user_text.lower().split()[0]
            if cmd in {"/exit","/quit"}:
                break
            if cmd in {"/help"}:
                print("Commands: /help  /new  /exit")
                continue
            if cmd == "/new":
                thread_id= _new_thread_id(root)
                config={"configurable": {"thread_id": thread_id}}
                print(f"Started a new conversation ({thread_id})")
                continue
            print(f"Unknown command: {cmd} ,.Try /help for help.")
            continue

        if user_text.lower() in {"exit", "quit"}:
            break

        run_turn(agent, user_text, config)
        print()


if __name__ == "__main__":
    main()
import argparse
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langgraph.types import Command

from mini_claude.agent import build_agent


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
        print("agent> ", end="", flush=True)

        try:
            for mode, data in agent.stream(
                payload,
                config=config,
                stream_mode=["messages", "updates"],
            ):
                if mode == "messages":
                    token, _metadata = data
                    _print_chunk_content(getattr(token, "content", None))
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
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    print(f"Mini Claude — project: {root}")
    print(f"Model: {model}")
    print("Type 'exit' or 'quit' to leave.\n")

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
        if user_text.lower() in {"exit", "quit"}:
            break

        run_turn(agent, user_text, config)
        print()


if __name__ == "__main__":
    main()
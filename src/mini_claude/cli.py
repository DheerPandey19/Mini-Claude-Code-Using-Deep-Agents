import argparse
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langgraph.types import Command

from mini_claude.agent import build_agent


def _print_message_content(content) -> None:
    if isinstance(content, str):
        print(content)
        return
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                print(block.get("text", ""), end="")
            elif isinstance(block, str):
                print(block, end="")
        print()
        return
    print(content)


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
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=config,
    )

    # May pause more than once (e.g. several shell commands)
    while result.get("__interrupt__"):
        interrupt_value = result["__interrupt__"][0].value
        action_requests = interrupt_value["action_requests"]
        decisions = _ask_decisions(action_requests)
        result = agent.invoke(
            Command(resume={"decisions": decisions}),
            config=config,  # same thread_id required
        )

    _print_message_content(result["messages"][-1].content)


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
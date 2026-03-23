"""
Command-line interface for SudokuAI.
"""

import argparse
import sys
import json
from pathlib import Path

from . import __version__
from .api import (
    generate_sudoku,
    solve_sudoku,
    validate_sudoku,
    llm_play_sudoku,
    evaluate_llm,
    generate_report,
    list_llm_providers,
    list_available_models,
    add_llm_provider,
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sudokuai",
        description="SudokuAI - LLM-powered Sudoku game and evaluation platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudokuai                          Launch GUI (default)
  sudokuai generate -d medium       Generate a medium puzzle
  sudokuai solve puzzle.json        Solve a puzzle from file
  sudokuai play -m gemma3:4b        Have LLM play a game
  sudokuai evaluate -m gemma3:4b    Evaluate LLM performance
  sudokuai web --port 5000          Start web server
""",
    )

    parser.add_argument("-V", "--version", action="version", version=f"sudokuai {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-essential output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    gui_parser = subparsers.add_parser("gui", help="Launch graphical user interface")
    gui_parser.add_argument("--no-web", action="store_true", help="Disable embedded web server")

    web_parser = subparsers.add_parser("web", help="Start web server")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    web_parser.add_argument("--port", type=int, default=5000, help="Port number")

    gen_parser = subparsers.add_parser("generate", help="Generate a Sudoku puzzle")
    gen_parser.add_argument("-d", "--difficulty", default="medium", 
                           choices=["easy", "medium", "hard", "expert", "master"],
                           help="Puzzle difficulty")

    solve_parser = subparsers.add_parser("solve", help="Solve a Sudoku puzzle")
    solve_parser.add_argument("input", help="Input puzzle file (JSON)")

    validate_parser = subparsers.add_parser("validate", help="Validate a Sudoku solution")
    validate_parser.add_argument("input", help="Solution file (JSON)")

    play_parser = subparsers.add_parser("play", help="Have LLM play a Sudoku game")
    play_parser.add_argument("-p", "--provider", default="ollama", help="LLM provider")
    play_parser.add_argument("-m", "--model", default=None, help="Model name (use 'models' command to list)")
    play_parser.add_argument("-d", "--difficulty", default="medium", help="Game difficulty")
    play_parser.add_argument("--mode", choices=["step", "oneshot"], default="step", help="Play mode")

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate LLM on multiple games")
    eval_parser.add_argument("-p", "--provider", default="ollama", help="LLM provider")
    eval_parser.add_argument("-m", "--model", default=None, help="Model name (use 'models' command to list)")
    eval_parser.add_argument("-g", "--games", type=int, default=3, help="Games per difficulty")
    eval_parser.add_argument("--difficulties", default="easy,medium", help="Difficulty levels (comma-separated)")
    eval_parser.add_argument("--mode", choices=["step", "oneshot"], default="step", help="Play mode")

    report_parser = subparsers.add_parser("report", help="Generate evaluation report")
    report_parser.add_argument("input", help="Evaluation result file (JSON)")

    models_parser = subparsers.add_parser("models", help="List available models from a provider")
    models_parser.add_argument("-p", "--provider", default="ollama", help="Provider to query")

    config_parser = subparsers.add_parser("config", help="Manage LLM provider configurations")
    config_subparsers = config_parser.add_subparsers(dest="config_cmd")
    
    config_list = config_subparsers.add_parser("list", help="List configured providers")
    
    config_add = config_subparsers.add_parser("add", help="Add a new provider")
    config_add.add_argument("--name", required=True, help="Provider name")
    config_add.add_argument("--provider", required=True, help="Provider type (ollama, openai, etc.)")
    config_add.add_argument("--api-base", required=True, help="API base URL")
    config_add.add_argument("--model", required=True, help="Default model")
    config_add.add_argument("--api-key", default="", help="API key")

    return parser


def output_result(result, args):
    use_json = getattr(args, "json_output", False) or getattr(args, "json", False)
    if use_json:
        content = result.to_json()
    else:
        if result.success:
            content = json.dumps(result.data, indent=2, ensure_ascii=False)
        else:
            content = f"Error: {result.error}"
    
    if getattr(args, "output", None):
        Path(args.output).write_text(content, encoding="utf-8")
        if not getattr(args, "quiet", False):
            print(f"Output saved to {args.output}")
    else:
        print(content)


def cmd_generate(args):
    result = generate_sudoku(args.difficulty)
    output_result(result, args)


def cmd_solve(args):
    try:
        data = json.loads(Path(args.input).read_text())
        result = solve_sudoku(data.get("puzzle", data))
        output_result(result, args)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1


def cmd_validate(args):
    try:
        data = json.loads(Path(args.input).read_text())
        result = validate_sudoku(data.get("solution", data))
        output_result(result, args)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1


def cmd_play(args):
    model = args.model
    if not model:
        models_result = list_available_models(args.provider)
        if models_result.success and models_result.data.get("models"):
            models = models_result.data["models"]
            print(f"Available models for {args.provider}:")
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")
            print(f"\nUse -m <model> to specify a model.")
            print("Example: sudokuai play -m {0}".format(models[0] if models else "gemma3:4b"))
            return 1
    
    result = llm_play_sudoku(
        difficulty=args.difficulty,
        provider=args.provider,
        model=model,
        mode=args.mode,
        verbose=True,
    )
    output_result(result, args)


def cmd_evaluate(args):
    model = args.model
    if not model:
        models_result = list_available_models(args.provider)
        if models_result.success and models_result.data.get("models"):
            models = models_result.data["models"]
            print(f"Available models for {args.provider}:")
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")
            print(f"\nUse -m <model> to specify a model.")
            return 1
    
    difficulties = [d.strip() for d in args.difficulties.split(",")]
    result = evaluate_llm(
        provider=args.provider,
        model=model,
        games_per_difficulty=args.games,
        difficulties=difficulties,
        mode=args.mode,
        verbose=True,
    )
    output_result(result, args)


def cmd_report(args):
    try:
        eval_json = Path(args.input).read_text()
        result = generate_report(eval_json)
        output_result(result, args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_config(args):
    if args.config_cmd == "list":
        result = list_llm_providers()
        output_result(result, args)
    elif args.config_cmd == "add":
        result = add_llm_provider(
            name=args.name,
            provider=args.provider,
            api_base=args.api_base,
            model=args.model,
            api_key=args.api_key,
        )
        output_result(result, args)
    else:
        print("Use 'config list' or 'config add'", file=sys.stderr)
        return 1


def cmd_models(args):
    print(f"Querying available models for {args.provider}...")
    result = list_available_models(args.provider)
    if result.success:
        models = result.data.get("models", [])
        if models:
            print(f"\nAvailable models ({len(models)}):")
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")
            print(f"\nUse with: sudokuai play -m <model>")
        else:
            print(f"No models found. Make sure {args.provider} is running.")
    else:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1


def has_display() -> bool:
    import os
    return os.environ.get("DISPLAY") is not None or sys.platform == "win32"


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        if has_display():
            from .gui import run_gui
            return run_gui()
        else:
            print("No display available. Starting web server...")
            from .app import run_server
            return run_server()

    if args.command == "gui":
        from .gui import run_gui
        return run_gui()

    if args.command == "web":
        from .app import run_server
        return run_server(host=args.host, port=args.port)

    if args.command == "generate":
        return cmd_generate(args)

    if args.command == "solve":
        return cmd_solve(args)

    if args.command == "validate":
        return cmd_validate(args)

    if args.command == "play":
        return cmd_play(args)

    if args.command == "evaluate":
        return cmd_evaluate(args)

    if args.command == "models":
        return cmd_models(args)

    if args.command == "report":
        return cmd_report(args)

    if args.command == "evaluate":
        return cmd_evaluate(args)

    if args.command == "report":
        return cmd_report(args)

    if args.command == "config":
        return cmd_config(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
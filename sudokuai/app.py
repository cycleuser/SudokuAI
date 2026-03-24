"""
Flask web application for SudokuAI.
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
from datetime import datetime
from io import BytesIO

from . import __version__
from .api import (
    generate_sudoku,
    solve_sudoku,
    validate_sudoku,
    llm_play_sudoku,
    evaluate_llm,
    list_llm_providers,
    list_available_models,
)
from .report.generator import generate_evaluation_report

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", version=__version__)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json or {}
    difficulty = data.get("difficulty", "medium")
    result = generate_sudoku(difficulty)
    return jsonify(result.to_dict())


@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.json
    puzzle = data.get("puzzle")
    if not puzzle:
        return jsonify({"success": False, "error": "No puzzle provided"}), 400

    result = solve_sudoku(puzzle)
    return jsonify(result.to_dict())


@app.route("/api/validate", methods=["POST"])
def api_validate():
    data = request.json
    solution = data.get("solution")
    if not solution:
        return jsonify({"success": False, "error": "No solution provided"}), 400

    result = validate_sudoku(solution)
    return jsonify(result.to_dict())


@app.route("/api/play", methods=["POST"])
def api_play():
    data = request.json or {}
    api_key = data.get("api_key")

    result = llm_play_sudoku(
        difficulty=data.get("difficulty", "medium"),
        provider=data.get("provider", "ollama"),
        model=data.get("model"),
        mode=data.get("mode", "step"),
        api_key=api_key,
    )
    return jsonify(result.to_dict())


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    data = request.json or {}
    difficulties = data.get("difficulties", ["easy", "medium"])
    api_key = data.get("api_key")

    result = evaluate_llm(
        provider=data.get("provider", "ollama"),
        model=data.get("model"),
        games_per_difficulty=data.get("games_per_difficulty", 3),
        difficulties=difficulties,
        mode=data.get("mode", "step"),
        api_key=api_key,
    )
    return jsonify(result.to_dict())


@app.route("/api/providers", methods=["GET"])
def api_providers():
    result = list_llm_providers()
    return jsonify(result.to_dict())


@app.route("/api/models", methods=["GET"])
def api_models():
    provider = request.args.get("provider", "ollama")
    result = list_available_models(provider)
    return jsonify(result.to_dict())


@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.json
    evaluation = data.get("evaluation")
    if not evaluation:
        return jsonify({"success": False, "error": "No evaluation data provided"}), 400

    if isinstance(evaluation, str):
        evaluation = json.loads(evaluation)

    from .core import EvaluationResult

    result = EvaluationResult(
        model_name=evaluation["model_name"],
        provider=evaluation["provider"],
        total_games=evaluation["total_games"],
        completed_games=evaluation["completed_games"],
        correct_games=evaluation["correct_games"],
        overall_accuracy=evaluation["overall_accuracy"],
        total_time=evaluation["total_time"],
        results_by_difficulty=evaluation.get("results_by_difficulty", {}),
        play_results=[],
        evaluated_at=datetime.now(),
    )

    report = generate_evaluation_report(result)
    return jsonify({"success": True, "data": report})


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    print(f"SudokuAI Web Server v{__version__}")
    print(f"Starting server at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    run_server()

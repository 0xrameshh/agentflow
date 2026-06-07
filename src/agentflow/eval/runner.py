from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from agentflow.config import require_api_key
from agentflow.eval.metrics import EvalReport, TaskResult
from agentflow.graph.builder import run_agent

DEFAULT_TASKS = Path(__file__).resolve().parents[3] / "eval" / "tasks.yaml"


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)


def _check_answer(answer: str, expect_contains: list[str]) -> bool:
    answer_lower = answer.lower()
    return all(fragment.lower() in answer_lower for fragment in expect_contains)


def run_eval_suite(tasks_path: Path | None = None) -> EvalReport:
    require_api_key()
    path = tasks_path or DEFAULT_TASKS
    tasks = yaml.safe_load(path.read_text(encoding="utf-8"))["tasks"]

    results: list[TaskResult] = []
    for index, task in enumerate(tasks):
        prompt = task["prompt"]
        expect = task.get("expect_contains", [])
        started = time.perf_counter()
        error = None
        answer = ""
        try:
            answer = run_agent(prompt, thread_id=f"eval-{task['id']}-{index}")
            passed = _check_answer(answer, expect)
        except Exception as exc:  # noqa: BLE001
            passed = False
            error = str(exc)
        latency_ms = (time.perf_counter() - started) * 1000
        token_est = _estimate_tokens(answer) + _estimate_tokens(prompt)
        results.append(
            TaskResult(
                id=task["id"],
                prompt=prompt,
                passed=passed,
                answer=answer,
                expect_contains=expect,
                latency_ms=round(latency_ms, 2),
                token_estimate=token_est,
                error=error,
            )
        )

    passed_count = sum(1 for result in results if result.passed)
    total = len(results)
    avg_latency = sum(result.latency_ms for result in results) / max(total, 1)
    total_tokens = sum(result.token_estimate for result in results)
    return EvalReport(
        total=total,
        passed=passed_count,
        pass_rate=round((passed_count / max(total, 1)) * 100, 2),
        avg_latency_ms=round(avg_latency, 2),
        total_token_estimate=total_tokens,
        results=results,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the agentflow eval suite")
    parser.add_argument(
        "--tasks",
        default=str(DEFAULT_TASKS),
        help=f"Path to tasks YAML file (default: {DEFAULT_TASKS})",
    )
    args = parser.parse_args()

    tasks_path = Path(args.tasks)
    report = run_eval_suite(tasks_path=tasks_path)
    out_dir = Path("eval/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"report-{stamp}.json"
    out_file.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2))
    print(f"\nWrote {out_file}")


if __name__ == "__main__":
    main()

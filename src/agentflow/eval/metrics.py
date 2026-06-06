"""Eval metrics dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class TaskResult:
    id: str
    prompt: str
    passed: bool
    answer: str
    expect_contains: list[str]
    latency_ms: float
    token_estimate: int = 0
    error: str | None = None


@dataclass
class EvalReport:
    total: int
    passed: int
    pass_rate: float
    avg_latency_ms: float
    total_token_estimate: int = 0
    results: list[TaskResult] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.results is None:
            self.results = []

    def to_dict(self) -> dict:
        payload = {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "total_token_estimate": self.total_token_estimate,
            "results": [asdict(result) for result in self.results],
        }
        return payload

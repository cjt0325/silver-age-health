"""Generate a reproducible evaluation report from synthetic cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from health_core.evaluation import evaluate_cases  # noqa: E402
from health_core.model import ModelServiceError  # noqa: E402
from health_core.response import prepare_response  # noqa: E402


CASES_PATH = BASE_DIR / "data" / "evaluation_cases.json"
REPORT_PATH = BASE_DIR / "artifacts" / "evaluation_report.json"


def _simulated_failure(name: str):
    def fail(_prompt):
        if name == "timeout":
            raise TimeoutError("simulated provider timeout")
        if name == "bad_json":
            raise ValueError("simulated malformed model JSON")
        raise ModelServiceError("OPENAI_API_KEY is not configured")

    return fail


def make_responder(mode: str):
    def respond(case: dict) -> dict:
        simulation = case.get("simulation")
        if simulation:
            return prepare_response(
                case["question"], mode="live", model_caller=_simulated_failure(simulation)
            )
        return prepare_response(case["question"], mode=mode)

    return respond


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Silver Age Health synthetic evaluation")
    parser.add_argument("--mode", choices=("demo", "live"), default="demo")
    args = parser.parse_args()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    report = evaluate_cases(cases, make_responder(args.mode), mode=args.mode)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    passed = sum(category["passed"] for category in report["categories"].values())
    print(f"{report['case_count']} cases evaluated; {passed} passed")
    print(json.dumps(report["metrics"], ensure_ascii=False))
    return 0 if passed == report["case_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

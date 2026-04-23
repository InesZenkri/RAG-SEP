"""Helper for expanding the adversarial test set (M7).

Planned modes:
- ``--unanswerable N``: generate N questions about topics absent from the
  indexed corpus (used for the abstention metric).
- ``--contradiction``: pair up documents whose claims conflict and emit a
  contradiction JSONL item.
- ``--prompt-injection``: emit test prompts containing injected instructions
  ("ignore previous instructions and ...") to verify guardrails.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unanswerable", type=int, default=0)
    parser.add_argument("--contradiction", action="store_true")
    parser.add_argument("--prompt-injection", action="store_true")
    parser.add_argument("--out", default="datasets/adversarial")
    args = parser.parse_args()  # noqa: F841
    raise NotImplementedError


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

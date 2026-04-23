"""Eval-harness smoke test (M1).

Planned case:
- ``python -m eval.run --suite smoke --config configs/baseline.yaml`` exits 0
  and writes both report.json and report.md under reports/runs/<timestamp>/.
"""

import pytest

pytest.skip("eval runner lands in M1", allow_module_level=True)

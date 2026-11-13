"""pytest 夹具：只保证被测源码包可导入，不连 DB / Redis / 网络。

容器内以 `python -m pytest tests -q` 运行时 cwd 已是 /app（PYTHONPATH=/app），
这里再兜底一次，方便在宿主仓库根目录直接跑 `pytest backend/tests`。
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

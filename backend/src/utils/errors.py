"""领域异常：由全局 error_handler 统一转 JSON。"""
from __future__ import annotations

from src.constants.error_codes import ERROR_MESSAGES


class AppError(Exception):
    def __init__(self, code: str, status_code: int = 400, detail: str | None = None, message: str | None = None) -> None:
        self.code = code
        self.status_code = status_code
        self.detail = detail
        self.message = message or ERROR_MESSAGES.get(code, "请求失败")
        super().__init__(self.message)

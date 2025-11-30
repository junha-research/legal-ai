# ================================
# File: app/core/errors.py
# Path: backend/app/core/errors.py
# ================================

from fastapi import HTTPException, status


class ServiceUnavailableError(HTTPException):
    def __init__(self, detail: str = "외부 서비스가 응답하지 않습니다. 잠시 후 다시 시도해주세요."):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "요청이 올바르지 않습니다."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class LLMError(HTTPException):
    def __init__(self, detail: str = "AI 해석 생성 중 오류가 발생했습니다."):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

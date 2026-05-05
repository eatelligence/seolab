from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None


def ok(data: Any = None) -> dict:
    return {"success": True, "data": data, "error": None}


def fail(message: str, data: Any = None) -> dict:
    return {"success": False, "data": data, "error": message}


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0

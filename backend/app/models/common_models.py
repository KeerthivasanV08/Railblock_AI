"""
Common Pydantic Models for Pagination and Generic Responses.
"""

from typing import Generic, List, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
    pages: int


class GenericMessageResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

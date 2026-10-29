"""Page-number pagination shared by list endpoints (backend/AGENTS.md section 16)."""

from math import ceil
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

MAX_PAGE_SIZE = 100


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool

    @classmethod
    def of(cls, params: PageParams, total_items: int) -> "Pagination":
        total_pages = ceil(total_items / params.page_size) if total_items else 0
        return cls(
            page=params.page,
            page_size=params.page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next_page=params.page < total_pages,
            has_previous_page=params.page > 1,
        )

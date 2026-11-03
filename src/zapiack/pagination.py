from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterator, List, Mapping, Optional, TypeVar

T = TypeVar("T")


@dataclass
class PageMeta:
    total: int
    page: int
    page_size: int
    total_pages: int


def to_meta(raw: Optional[Mapping[str, Any]], count: int) -> PageMeta:
    """Turns either list shape the API uses (`limit` or `pageSize`) into one."""
    raw = raw or {}
    total = raw.get("total", count)
    page_size = raw.get("pageSize") or raw.get("limit") or (count or 1)
    total_pages = raw.get("totalPages") or max(1, -(-total // page_size)) or 1
    return PageMeta(total=total, page=raw.get("page", 1), page_size=page_size, total_pages=total_pages)


class Page(Generic[T]):
    """One page of results.

    `data` is this page's items. Iterating the page walks **every** item on **every** page, fetching the next page when it is
    needed, so `for contact in client.email.contacts.list(): ...` visits all of them.
    """

    def __init__(self, data: List[T], meta: PageMeta, fetch_page: Callable[[int], "Page[T]"]) -> None:
        self.data = data
        self.meta = meta
        self._fetch_page = fetch_page

    def has_next_page(self) -> bool:
        return self.meta.page < self.meta.total_pages

    def next_page(self) -> "Page[T]":
        if not self.has_next_page():
            raise IndexError("There is no next page")
        return self._fetch_page(self.meta.page + 1)

    def iter_pages(self) -> Iterator["Page[T]"]:
        page: Page[T] = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = page.next_page()

    def __iter__(self) -> Iterator[T]:
        for page in self.iter_pages():
            yield from page.data

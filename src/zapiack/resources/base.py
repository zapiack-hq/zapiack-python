from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Union

from .._http import Call, Form, HttpClient, RequestOptions
from ..pagination import Page, to_meta

Params = Mapping[str, Any]
Options = Optional[RequestOptions]


def quote(value: str) -> str:
    """An id placed in a path: nothing in it can change where the request goes."""
    return urllib.parse.quote(str(value), safe="")


@dataclass
class UploadFile:
    """A file to upload: its bytes, the name to send it under, and its type (for example `image/png`)."""

    content: bytes
    filename: str
    mime_type: str = "application/octet-stream"

    def to_form(self, fields: Optional[Dict[str, Optional[str]]] = None) -> Form:
        return Form(self.filename, bytes(self.content), self.mime_type, {k: v for k, v in (fields or {}).items() if v is not None})


class Resource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def _call(self, method: str, path: str, *, query: Optional[Mapping[str, Any]] = None, body: Any = None, send: bool = False, form: Optional[Form] = None, options: Options = None) -> Any:
        return self._http.request(Call(method=method, path=path, query=query, body=body, send=send, form=form), options)

    def _paged(self, path: str, key: str, params: Optional[Params], options: Options, extra_query: Optional[Mapping[str, Any]] = None) -> Page:
        """A list call: the first page now, and the rest as the page is iterated."""
        params = dict(params or {})

        def fetch(page: int) -> Page:
            res = self._call("GET", path, query={**params, **(extra_query or {}), "page": page}, options=options)
            items = res[key]
            return Page(items, to_meta(res.get("meta"), len(items)), fetch)

        return fetch(int(params.get("page", 1)))

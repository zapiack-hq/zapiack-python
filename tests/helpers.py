from __future__ import annotations

import json
import sys
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zapiack import Zapiack, TransportRequest, TransportResponse  # noqa: E402


@dataclass
class Recorded:
    method: str
    url: str
    headers: Dict[str, str]
    body: Any
    raw: Optional[bytes]


@dataclass
class Reply:
    status: int = 200
    body: Any = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)


class FakeTransport:
    """Records what it was asked and answers from a script, one reply per call (the last repeats). An exception is raised, not returned."""

    def __init__(self, *replies: Union[Reply, Exception]) -> None:
        self.replies = list(replies) or [Reply()]
        self.calls: List[Recorded] = []

    def __call__(self, request: TransportRequest) -> TransportResponse:
        is_json = request.headers.get("Content-Type") == "application/json"
        self.calls.append(Recorded(request.method, request.url, request.headers, json.loads(request.body) if request.body and is_json else None, request.body))
        reply = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        text = "" if reply.body is None else json.dumps(reply.body)
        return TransportResponse(reply.status, {k.lower(): v for k, v in reply.headers.items()}, text.encode())


def client(*replies: Union[Reply, Exception], **options: Any):
    transport = FakeTransport(*replies)
    sleeps: List[float] = []
    zapiack = Zapiack("zpk_abc12345_secret", transport=transport, sleep=sleeps.append, **options)
    return zapiack, transport, sleeps

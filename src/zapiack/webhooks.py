from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any, Optional, Union

from .errors import ZapiackSignatureError

_HEADER = re.compile(r"^t=(\d+),v1=([0-9a-f]{64})$")


def _signature(secret: str, timestamp: Union[int, str], body: str) -> str:
    return hmac.new(secret.encode(), f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()


class Webhooks:
    """Checks and reads a webhook.

    Pass the **raw** request body (before any JSON parsing), the `Zapiack-Signature` header and your endpoint's signing secret.
    """

    def verify(
        self,
        raw_body: Union[str, bytes],
        signature_header: Optional[str],
        secret: str,
        *,
        tolerance_seconds: int = 300,
        now: Optional[float] = None,
    ) -> Any:
        """Returns the parsed body, or raises ZapiackSignatureError when the signature is missing, wrong or too old."""
        body = raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else raw_body
        match = _HEADER.match(signature_header or "")
        if not match:
            raise ZapiackSignatureError("The Zapiack-Signature header is missing or malformed")

        timestamp = int(match.group(1))
        current = int(time.time() if now is None else now)
        if abs(current - timestamp) > tolerance_seconds:
            raise ZapiackSignatureError("The webhook is too old, or its clock is wrong")

        if not hmac.compare_digest(_signature(secret, match.group(1), body), match.group(2)):
            raise ZapiackSignatureError("The webhook signature does not match")

        try:
            return json.loads(body)
        except ValueError as error:
            raise ZapiackSignatureError("The webhook body is not valid JSON") from error

    def is_valid(self, raw_body: Union[str, bytes], signature_header: Optional[str], secret: str, **kwargs: Any) -> bool:
        """Whether a webhook is genuine, without reading it."""
        try:
            self.verify(raw_body, signature_header, secret, **kwargs)
            return True
        except ZapiackSignatureError:
            return False

    def sign(self, secret: str, body: str, timestamp: Optional[int] = None) -> str:
        """Signs a body the way Zapiack does: for testing your own webhook handler."""
        ts = int(time.time()) if timestamp is None else timestamp
        return f"t={ts},v1={_signature(secret, ts, body)}"

"""Every failure is a ZapiackError with a stable `code`, the HTTP `status` and a `request_id`."""

from __future__ import annotations

import re
from typing import Any, Optional


class ZapiackError(Exception):
    """Raised for every failed request.

    `code` is stable and the same in every Zapiack SDK, `status` is the HTTP status (0 when no response was received), and
    `request_id` identifies the request when you contact support.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str,
        request_id: Optional[str] = None,
        details: Any = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.request_id = request_id
        #: What the API said about each field that was wrong, when it said.
        self.details = details
        #: Seconds to wait before trying again, when the API asked for a pause.
        self.retry_after = retry_after


class ZapiackConnectionError(ZapiackError):
    """No response was received: the network failed or the request timed out."""

    def __init__(self, message: str, *, code: str = "connection_error", request_id: Optional[str] = None) -> None:
        super().__init__(message, status=0, code=code, request_id=request_id)


class ZapiackSignatureError(ZapiackError):
    """A webhook did not carry a valid signature."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status=400, code="invalid_signature")


class ZapiackConfigError(Exception):
    """The client was set up wrongly, for example with no key or with a key that must not be used here."""


_BY_STATUS = {
    400: "invalid_request",
    401: "authentication_failed",
    402: "insufficient_balance",
    403: "permission_denied",
    404: "not_found",
    409: "conflict",
    422: "unprocessable",
    429: "rate_limited",
}

_GENERIC = re.compile(
    r"^(bad request|unauthorized|forbidden|not found|conflict|unprocessable entity|too many requests|internal server error|"
    r"payment required|service unavailable|bad gateway|gateway timeout)$",
    re.IGNORECASE,
)
_NAME = re.compile(r"^[A-Za-z]+(?:[_ -]?[A-Za-z]+)*$")


def _snake(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[\s-]+", "_", value).lower()


def _code_for(status: int, body: Any) -> str:
    """A code the API chose itself (`credential_invalid`, `OverageCapReached`) is kept; a generic status name is replaced."""
    named = body.get("error") if isinstance(body, dict) else None
    if isinstance(named, str) and _NAME.match(named) and not _GENERIC.match(named):
        return _snake(named)
    if status >= 500:
        return "server_error"
    return _BY_STATUS.get(status, "invalid_request")


def _message_for(status: int, body: Any) -> "tuple[str, Any]":
    if isinstance(body, dict):
        message = body.get("message")
        errors = body.get("errors")
        details = errors if isinstance(errors, list) else message if isinstance(message, list) else None
        if isinstance(message, str) and message:
            return message, details
        if isinstance(message, list) and message:
            return "; ".join(str(m) for m in message), details
        if isinstance(errors, list) and errors:
            return "; ".join(str(e) for e in errors), details
    return f"The request failed with status {status}", None


def error_from_response(status: int, body: Any, request_id: Optional[str], retry_after: Optional[float] = None) -> ZapiackError:
    message, details = _message_for(status, body)
    return ZapiackError(message, status=status, code=_code_for(status, body), request_id=request_id, details=details, retry_after=retry_after)

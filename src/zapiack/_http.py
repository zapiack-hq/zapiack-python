from __future__ import annotations

import json
import platform
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, Mapping, Optional

from ._version import VERSION
from .errors import ZapiackConnectionError, ZapiackError, error_from_response

RETRYABLE = {408, 429, 500, 502, 503, 504}
MAX_RETRY_AFTER_SECONDS = 30
BASE_DELAY_SECONDS = 0.5
MAX_DELAY_SECONDS = 8.0


@dataclass
class RequestOptions:
    """Per-call settings. Every resource method takes one as its last argument."""

    #: Overrides the key generated for a send. Reuse the same key to make a repeated request safe.
    idempotency_key: Optional[str] = None
    #: Seconds, for this request only.
    timeout: Optional[float] = None
    #: Retries after the first attempt, for this request only.
    max_retries: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class Call:
    method: str
    path: str
    query: Optional[Mapping[str, Any]] = None
    body: Any = None
    #: A file upload, sent as multipart/form-data instead of JSON: (field name, filename, bytes, mime type, extra fields).
    form: Optional["Form"] = None
    #: A send: gets an idempotency key automatically, which is what makes retrying it safe.
    send: bool = False


@dataclass
class Form:
    filename: str
    content: bytes
    mime_type: str = "application/octet-stream"
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class TransportRequest:
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[bytes]
    timeout: float


@dataclass
class TransportResponse:
    status: int
    headers: Dict[str, str]
    body: bytes


Transport = Callable[[TransportRequest], TransportResponse]


def urllib_transport(request: TransportRequest) -> TransportResponse:
    """The default transport: the standard library, so the SDK has no dependencies. Raises OSError (or TimeoutError) when the network fails."""
    req = urllib.request.Request(request.url, data=request.body, method=request.method, headers=request.headers)
    try:
        with urllib.request.urlopen(req, timeout=request.timeout) as response:  # noqa: S310 - the URL is the configured API address
            return TransportResponse(response.status, {k.lower(): v for k, v in response.headers.items()}, response.read())
    except urllib.error.HTTPError as error:
        return TransportResponse(error.code, {k.lower(): v for k, v in error.headers.items()}, error.read())


def parse_retry_after(value: Optional[str], now: Optional[float] = None) -> Optional[float]:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return None
    return max(0.0, when - (time.time() if now is None else now))


def backoff_seconds(attempt: int, retry_after: Optional[float] = None, rand: Callable[[], float] = random.random) -> float:
    """Waits before attempt `attempt + 1`: half a second, doubling, with jitter; the API's own request to wait is a floor."""
    base = min(BASE_DELAY_SECONDS * 2**attempt, MAX_DELAY_SECONDS)
    jittered = base * (0.75 + rand() * 0.5)
    return max(jittered, retry_after or 0.0)


def _multipart(form: Form) -> "tuple[bytes, str]":
    boundary = "zapiack" + uuid.uuid4().hex
    chunks = []
    for key, value in form.fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    safe = form.filename.replace('"', "").replace("\r", "").replace("\n", "")
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{safe}"\r\nContent-Type: {form.mime_type}\r\n\r\n'.encode())
    chunks.append(form.content)
    chunks.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def build_url(base_url: str, path: str, query: Optional[Mapping[str, Any]] = None) -> str:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    pairs = []
    for key, value in (query or {}).items():
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            value = "true" if value else "false"
        pairs.append((key, str(value)))
    return f"{url}?{urllib.parse.urlencode(pairs)}" if pairs else url


class HttpClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        transport: Transport,
        app_info: Optional[str] = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.transport = transport
        self.app_info = app_info
        self.sleep = sleep

    def _user_agent(self) -> str:
        return f"zapiack-python/{VERSION} python/{platform.python_version()}" + (f" {self.app_info}" if self.app_info else "")

    def request(self, call: Call, options: Optional[RequestOptions] = None) -> Any:
        options = options or RequestOptions()
        request_id = str(uuid.uuid4())
        idempotency_key = (options.idempotency_key or str(uuid.uuid4())) if call.send else options.idempotency_key
        # Repeating a request is only safe when it cannot happen twice: a read, or a send carrying an idempotency key.
        safe_to_repeat = call.method in ("GET", "DELETE") or idempotency_key is not None
        max_retries = (self.max_retries if options.max_retries is None else options.max_retries) if safe_to_repeat else 0
        timeout = self.timeout if options.timeout is None else options.timeout
        url = build_url(self.base_url, call.path, call.query)

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": self._user_agent(),
            "X-Request-Id": request_id,
        }
        body: Optional[bytes] = None
        if call.form is not None:
            body, headers["Content-Type"] = _multipart(call.form)
        elif call.body is not None:
            body = json.dumps(call.body).encode()
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        headers.update(options.headers)

        attempt = 0
        while True:
            try:
                response = self.transport(TransportRequest(call.method, url, headers, body, timeout))
            except ZapiackError:
                raise
            except (OSError, TimeoutError) as error:
                timed_out = isinstance(error, TimeoutError) or "timed out" in str(error).lower()
                if attempt < max_retries:
                    self.sleep(backoff_seconds(attempt))
                    attempt += 1
                    continue
                raise ZapiackConnectionError(
                    f"The request timed out after {timeout:g} s" if timed_out else "The request could not reach Zapiack",
                    code="timeout" if timed_out else "connection_error",
                    request_id=request_id,
                ) from error

            text = response.body.decode("utf-8", errors="replace")
            try:
                parsed = json.loads(text) if text else None
            except ValueError:
                parsed = None

            if 200 <= response.status < 300:
                return parsed

            retry_after = parse_retry_after(response.headers.get("retry-after"))
            error_obj = error_from_response(response.status, parsed, response.headers.get("x-request-id") or request_id, retry_after)
            may_wait = retry_after is None or retry_after <= MAX_RETRY_AFTER_SECONDS
            if attempt < max_retries and response.status in RETRYABLE and may_wait:
                self.sleep(backoff_seconds(attempt, retry_after))
                attempt += 1
                continue
            raise error_obj

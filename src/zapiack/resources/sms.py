from __future__ import annotations

from typing import Any, List

from .base import Options, Params, Resource


class Sms(Resource):
    def send(self, params: Params, options: Options = None) -> Any:
        """Sends one SMS: `phone`, `country` (two letters, for example NG) and `message`. Repeating the call with the same
        `idempotency_key` never sends or charges it twice."""
        return self._call("POST", "sms/send", body=dict(params), send=True, options=options)

    def send_batch(self, messages: List[Params], options: Options = None) -> Any:
        """Sends many SMS in one request."""
        return self._call("POST", "sms/send/batch", body=[dict(m) for m in messages], send=True, options=options)

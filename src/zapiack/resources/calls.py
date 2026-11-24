from __future__ import annotations

from typing import Any, List

from .base import Options, Params, Resource, quote


class CallWebhooks(Resource):
    def list(self, options: Options = None) -> Any:
        return self._call("GET", "calls/webhooks", options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        """`url` and `events` (a list of room.started, room.ended, participant.joined, participant.left, call.ringing,
        call.accepted, call.ended). The signing `secret` is in this response only: keep it."""
        return self._call("POST", "calls/webhooks", body=dict(params), send=True, options=options)

    def remove(self, id: str, options: Options = None) -> Any:
        return self._call("DELETE", f"calls/webhooks/{quote(id)}", options=options)


class Calls(Resource):
    """Voice and video. Your server starts calls and mints join tokens; the app holds only the token. Needs an API key with
    the `calls` scope (or no scopes)."""

    def __init__(self, http) -> None:
        super().__init__(http)
        self.webhooks = CallWebhooks(http)

    def start(self, params: Params, options: Options = None) -> Any:
        """Rings one person (`callee`) or several (`callees`, up to 49) and returns the caller's token. `caller` is required;
        `media_kind`-style fields use the API's own names: `mediaKind`, `data`, `push`, `pushAppId`."""
        return self._call("POST", "calls", body=dict(params), send=True, options=options)

    def get(self, call_id: str, options: Options = None) -> Any:
        return self._call("GET", f"calls/{quote(call_id)}", options=options)

    def accept(self, call_id: str, params: Params, options: Options = None) -> Any:
        """Answers for `identity`. Returns that person's token."""
        return self._call("POST", f"calls/{quote(call_id)}/accept", body=dict(params), send=True, options=options)

    def decline(self, call_id: str, params: Params, options: Options = None) -> Any:
        return self._call("POST", f"calls/{quote(call_id)}/decline", body=dict(params), send=True, options=options)

    def cancel(self, call_id: str, params: Params, options: Options = None) -> Any:
        """The caller stops ringing before anyone answers. Only the caller can."""
        return self._call("POST", f"calls/{quote(call_id)}/cancel", body=dict(params), send=True, options=options)

    def end(self, call_id: str, params: Params, options: Options = None) -> Any:
        return self._call("POST", f"calls/{quote(call_id)}/end", body=dict(params), send=True, options=options)

    def create_room(self, params: Params, options: Options = None) -> Any:
        """A room with no ringing: `name`, and optionally `mode` (call, group or live), `maxStage`, `maxAudience`, `region`."""
        return self._call("POST", "calls/rooms", body=dict(params), send=True, options=options)

    def list_rooms(self, params: Params = {}, options: Options = None) -> Any:
        return self._call("GET", "calls/rooms", query=dict(params), options=options)

    def get_room(self, room_id: str, options: Options = None) -> Any:
        return self._call("GET", f"calls/rooms/{quote(room_id)}", options=options)

    def end_room(self, room_id: str, options: Options = None) -> Any:
        """Ends a room for everyone."""
        return self._call("DELETE", f"calls/rooms/{quote(room_id)}", options=options)

    def token(self, params: Params, options: Options = None) -> Any:
        """A join token for one person: `roomId`, `identity`, and optionally `role` (host, speaker, listener), `kinds`,
        `ttlSeconds`, `maxSessionSeconds`."""
        return self._call("POST", "calls/tokens", body=dict(params), send=True, options=options)

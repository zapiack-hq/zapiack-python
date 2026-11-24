from __future__ import annotations

from typing import Any, List

from .base import Options, Params, Resource, quote


class Realtime(Resource):
    def token(self, params: Params, options: Options = None) -> Any:
        """A short-lived token for the Realtime SDK in your app: `capabilities` (for example
        {"chat:*": ["subscribe", "publish"]}), and optionally `userId` and `ttlSeconds`."""
        return self._call("POST", "realtime/tokens", body=dict(params), send=True, options=options)

    def publish(self, channel: str, params: Params = {}, options: Options = None) -> Any:
        """Sends a message into a channel: `event`, `data`, `from`, and `persist` to keep it in history."""
        return self._call("POST", f"realtime/channels/{quote(channel)}/publish", body=dict(params), send=True, options=options)

    def publish_batch(self, events: List[Params], options: Options = None) -> Any:
        """Up to 100 messages, each with a `channel`. One bad message does not fail the rest."""
        return self._call("POST", "realtime/publish/batch", body={"events": [dict(e) for e in events]}, send=True, options=options)

    def history(self, channel: str, params: Params = {}, options: Options = None) -> Any:
        return self._call("GET", f"realtime/channels/{quote(channel)}/history", query=dict(params), options=options)

    def presence(self, channel: str, options: Options = None) -> Any:
        return self._call("GET", f"realtime/channels/{quote(channel)}/presence", options=options)

    def channels(self, params: Params = {}, options: Options = None) -> Any:
        return self._call("GET", "realtime/channels", query=dict(params), options=options)

    def disconnect_connection(self, connection_id: str, options: Options = None) -> Any:
        return self._call("POST", f"realtime/connections/{quote(connection_id)}/disconnect", send=True, options=options)

    def disconnect_user(self, user_id: str, options: Options = None) -> Any:
        """Closes every connection a person has, for example when they sign out everywhere."""
        return self._call("POST", f"realtime/users/{quote(user_id)}/disconnect", send=True, options=options)

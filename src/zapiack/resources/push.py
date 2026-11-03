from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from ..pagination import Page
from .base import Options, Params, Resource, UploadFile, quote


def _iso(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


class Messages(Resource):
    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"push/messages/{quote(id)}", options=options)

    def list(self, params: Optional[Params] = None, options: Options = None) -> Page:
        return self._paged("push/messages", "messages", params, options)

    def cancel(self, id: str, options: Options = None) -> Any:
        """Cancels a scheduled push. Once it has started going out it cannot be recalled."""
        return self._call("DELETE", f"push/messages/{quote(id)}", options=options)

    def reschedule(self, id: str, scheduled_at: Any, options: Options = None) -> Any:
        """Moves a scheduled push to another time."""
        return self._call("PATCH", f"push/messages/{quote(id)}", body={"scheduledAt": _iso(scheduled_at)}, options=options)

    def retry(self, id: str, params: Optional[Params] = None, options: Options = None) -> Any:
        """Sends again to the devices a message failed for: all of them, or only `deliveryIds`. A device that is gone is never retried."""
        return self._call("POST", f"push/messages/{quote(id)}/retry", body=dict(params or {}), options=options)

    def metrics(self, id: str, options: Options = None) -> Any:
        """Counts, rates, platforms, failures, buttons, events and a timeline for one message."""
        return self._call("GET", f"push/messages/{quote(id)}/metrics", options=options)

    def deliveries(self, id: str, params: Optional[Params] = None, options: Options = None) -> Page:
        return self._paged(f"push/messages/{quote(id)}/deliveries", "deliveries", params, options)

    def funnel(self, id: str, options: Options = None) -> Any:
        """Sent, arrived, tapped, each button, converted, and the screens people went to next."""
        return self._call("GET", f"push/messages/{quote(id)}/funnel", options=options)


class Devices(Resource):
    def list(self, params: Optional[Params] = None, options: Options = None) -> Page:
        return self._paged("push/devices", "devices", params, options)

    def get(self, id: str, app_id: Optional[str] = None, options: Options = None) -> Any:
        return self._call("GET", f"push/devices/{quote(id)}", query={"appId": app_id}, options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        """Changes who a device belongs to or its tags. Tags you pass are merged with the ones it already has."""
        body = dict(params)
        app_id = body.pop("appId", None)
        return self._call("PATCH", f"push/devices/{quote(id)}", query={"appId": app_id}, body=body, options=options)

    def remove(self, id: str, app_id: Optional[str] = None, options: Options = None) -> None:
        """Stops sending to a device and forgets who it belonged to."""
        self._call("DELETE", f"push/devices/{quote(id)}", query={"appId": app_id}, options=options)


class Segments(Resource):
    """Named audiences: people you list by hand, plus anyone carrying every tag of an optional rule."""

    def list(self, app_id: Optional[str] = None, options: Options = None) -> Any:
        return self._call("GET", "push/segments", query={"appId": app_id}, options=options)

    def get(self, id: str, app_id: Optional[str] = None, options: Options = None) -> Any:
        return self._call("GET", f"push/segments/{quote(id)}", query={"appId": app_id}, options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "push/segments", body=dict(params), options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        body = dict(params)
        app_id = body.pop("appId", None)
        return self._call("PATCH", f"push/segments/{quote(id)}", query={"appId": app_id}, body=body, options=options)

    def remove(self, id: str, app_id: Optional[str] = None, options: Options = None) -> None:
        self._call("DELETE", f"push/segments/{quote(id)}", query={"appId": app_id}, options=options)

    def members(self, id: str, params: Optional[Params] = None, options: Options = None) -> Page:
        return self._paged(f"push/segments/{quote(id)}/members", "members", params, options)

    def add_members(self, id: str, external_user_ids: List[str], app_id: Optional[str] = None, options: Options = None) -> Any:
        """Adds people by the user ids your app gave Zapiack. Up to 1,000 at a time."""
        return self._call("POST", f"push/segments/{quote(id)}/members", query={"appId": app_id}, body={"externalUserIds": external_user_ids}, options=options)

    def remove_members(self, id: str, external_user_ids: List[str], app_id: Optional[str] = None, options: Options = None) -> Any:
        return self._call("POST", f"push/segments/{quote(id)}/members/remove", query={"appId": app_id}, body={"externalUserIds": external_user_ids}, options=options)


class Credentials(Resource):
    def apns(self, app_id: str, params: Params, options: Options = None) -> Any:
        """An APNs key: `privateKey` (the .p8 text), `keyId`, `teamId`, and `environment`. Checked with Apple before it is saved."""
        return self._call("PUT", f"push/apps/{quote(app_id)}/credentials/apns", body=dict(params), options=options)

    def fcm(self, app_id: str, params: Params, options: Options = None) -> Any:
        """A Firebase service account, as `serviceAccount`. Checked with Google before it is saved."""
        return self._call("PUT", f"push/apps/{quote(app_id)}/credentials/fcm", body=dict(params), options=options)

    def hms(self, app_id: str, params: Params, options: Options = None) -> Any:
        """Huawei Push Kit: `appId` and `appSecret` from AppGallery Connect."""
        return self._call("PUT", f"push/apps/{quote(app_id)}/credentials/hms", body=dict(params), options=options)

    def validate(self, app_id: str, credential_id: str, options: Options = None) -> Any:
        return self._call("POST", f"push/apps/{quote(app_id)}/credentials/{quote(credential_id)}/validate", options=options)

    def remove(self, app_id: str, credential_id: str, options: Options = None) -> None:
        self._call("DELETE", f"push/apps/{quote(app_id)}/credentials/{quote(credential_id)}", options=options)


class Apps(Resource):
    def __init__(self, http: Any) -> None:
        super().__init__(http)
        self.credentials = Credentials(http)

    def list(self, options: Options = None) -> Any:
        return self._call("GET", "push/apps", options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"push/apps/{quote(id)}", options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "push/apps", body=dict(params), options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        return self._call("PATCH", f"push/apps/{quote(id)}", body=dict(params), options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"push/apps/{quote(id)}", options=options)


class Webhooks(Resource):
    def list(self, options: Options = None) -> Any:
        return self._call("GET", "push/webhooks", options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        """The answer carries the signing secret once. Keep it: it is how you check a delivery came from Zapiack."""
        return self._call("POST", "push/webhooks", body=dict(params), options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        return self._call("PATCH", f"push/webhooks/{quote(id)}", body=dict(params), options=options)

    def rotate_secret(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"push/webhooks/{quote(id)}/secret", options=options)

    def test(self, id: str, options: Options = None) -> Any:
        """Sends a sample event to the endpoint and says whether it answered."""
        return self._call("POST", f"push/webhooks/{quote(id)}/test", options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"push/webhooks/{quote(id)}", options=options)


class Images(Resource):
    def upload(self, file: UploadFile, options: Options = None) -> Any:
        """Uploads a picture (PNG or JPEG, up to 2 MB) and answers with the https `url` to use as a push's `image`."""
        return self._call("POST", "push/images", form=file.to_form(), options=options)


class Push(Resource):
    def __init__(self, http: Any) -> None:
        super().__init__(http)
        self.messages = Messages(http)
        self.devices = Devices(http)
        self.segments = Segments(http)
        self.apps = Apps(http)
        self.webhooks = Webhooks(http)
        self.images = Images(http)

    def metrics(self, params: Optional[Params] = None, options: Options = None) -> Any:
        """Counts over time for the project, or for one app, platform or message. Buckets are cut in `tz`."""
        query = dict(params or {})
        for key in ("from", "to"):
            if key in query:
                query[key] = _iso(query[key])
        return self._call("GET", "push/metrics", query=query, options=options)

    def reachable(self, params: Params, options: Options = None) -> Any:
        """How many devices an audience would reach, per platform, before anything is sent."""
        return self._call("POST", "push/reachable", body=dict(params), options=options)

    def send(self, params: Params, options: Options = None) -> Any:
        """Sends a push notification to a device, a user, everyone with certain tags, or everyone.

        Answers once the push is accepted; delivery is reported by webhook or by `messages.get`. Repeating the call with the
        same `idempotency_key` never sends it twice. `scheduled_at` may be a datetime (with a time zone) or an ISO 8601 string.
        """
        body = dict(params)
        if "scheduledAt" in body:
            body["scheduledAt"] = _iso(body["scheduledAt"])
        return self._call("POST", "push/messages", body=body, send=True, options=options)

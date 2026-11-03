from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, Union

from .base import Options, Params, Resource, UploadFile, quote


class Templates(Resource):
    def list(self, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/templates", options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"whatsapp/templates/{quote(id)}", options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "whatsapp/templates", body=params, options=options)

    def dismiss_category_change(self, id: str, options: Options = None) -> Any:
        """Acknowledges that Meta changed a template's category, so the notice goes away."""
        return self._call("POST", f"whatsapp/templates/{quote(id)}/dismiss-category-change", options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"whatsapp/templates/{quote(id)}", options=options)


class Contacts(Resource):
    def list(self, params: Optional[Params] = None, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/contacts", query=params, options=options)

    def opt_in(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "whatsapp/contacts/opt-in", body=params, options=options)

    def opt_out(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "whatsapp/contacts/opt-out", body=params, options=options)


class Media(Resource):
    def upload(self, file: UploadFile, options: Options = None) -> Any:
        """Uploads a file to send in a message. Use the id it returns as `media.id`."""
        return self._call("POST", "whatsapp/media", form=file.to_form(), options=options)

    def upload_from_url(self, params: Params, options: Options = None) -> Any:
        """Has Zapiack fetch a file from a public address, instead of uploading its bytes."""
        return self._call("POST", "whatsapp/media/url", body=params, options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"whatsapp/media/{quote(id)}", options=options)


class Conversations(Resource):
    def list(self, params: Optional[Params] = None, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/conversations", query=params, options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"whatsapp/conversations/{quote(id)}", options=options)

    def messages(self, id: str, params: Optional[Params] = None, options: Options = None) -> Any:
        """The messages of a conversation, newest first. Pass `before` to page back in time."""
        return self._call("GET", f"whatsapp/conversations/{quote(id)}/messages", query=params, options=options)

    def reply(self, id: str, params: Params, options: Options = None) -> Any:
        """Replies inside a conversation. Repeating the call with the same `idempotency_key` never sends it twice."""
        return self._call("POST", f"whatsapp/conversations/{quote(id)}/messages", body=dict(params), send=True, options=options)

    def assign(self, id: str, user_id: Optional[str], options: Options = None) -> Any:
        """Assigns the conversation to a team member, or to nobody when `user_id` is None."""
        return self._call("POST", f"whatsapp/conversations/{quote(id)}/assign", body={"userId": user_id}, options=options)

    def mark_read(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"whatsapp/conversations/{quote(id)}/read", options=options)


class Broadcasts(Resource):
    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "whatsapp/broadcasts", body=params, options=options)

    def list(self, params: Optional[Params] = None, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/broadcasts", query=params, options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"whatsapp/broadcasts/{quote(id)}", options=options)

    def add_recipients(self, id: str, recipients: List[Params], options: Options = None) -> Any:
        return self._call("POST", f"whatsapp/broadcasts/{quote(id)}/recipients", body={"recipients": recipients}, options=options)

    def recipients(self, id: str, params: Optional[Params] = None, options: Options = None) -> Any:
        return self._call("GET", f"whatsapp/broadcasts/{quote(id)}/recipients", query=params, options=options)

    def check(self, id: str, options: Options = None) -> Any:
        """Checks the broadcast before it starts: who can be reached, and what it will cost."""
        return self._call("POST", f"whatsapp/broadcasts/{quote(id)}/check", options=options)

    def start(self, id: str, scheduled_at: Union[str, datetime, None] = None, options: Options = None) -> Any:
        """Starts the broadcast now, or at `scheduled_at` (an ISO 8601 time with its time zone)."""
        when = scheduled_at.isoformat() if isinstance(scheduled_at, datetime) else scheduled_at
        return self._call("POST", f"whatsapp/broadcasts/{quote(id)}/start", body={"scheduledAt": when} if when else {}, options=options)

    def pause(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"whatsapp/broadcasts/{quote(id)}/pause", options=options)

    def resume(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"whatsapp/broadcasts/{quote(id)}/resume", options=options)

    def cancel(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"whatsapp/broadcasts/{quote(id)}/cancel", options=options)


class WebhookEndpoints(Resource):
    """Where Zapiack tells your server about WhatsApp events. Verify each request with `client.webhooks.verify`."""

    def create(self, params: Params, options: Options = None) -> Any:
        """The signing secret in the answer is shown once."""
        return self._call("POST", "whatsapp/webhook-endpoints", body=params, options=options)

    def list(self, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/webhook-endpoints", options=options)

    def event_types(self, options: Options = None) -> Any:
        """The events an endpoint can subscribe to."""
        return self._call("GET", "whatsapp/webhook-events", options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        return self._call("PATCH", f"whatsapp/webhook-endpoints/{quote(id)}", body=params, options=options)

    def test(self, options: Options = None) -> Any:
        """Sends a signed sample to every endpoint."""
        return self._call("POST", "whatsapp/webhook-endpoints/test", options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"whatsapp/webhook-endpoints/{quote(id)}", options=options)

    def rotate_secret(self, id: str, options: Options = None) -> Any:
        """Makes a new signing secret; the old one stops working. The new one is shown once."""
        return self._call("POST", f"whatsapp/webhook-endpoints/{quote(id)}/rotate-secret", options=options)

    def enable(self, id: str, options: Options = None) -> Any:
        """Turns an endpoint back on after it was switched off for failing."""
        return self._call("POST", f"whatsapp/webhook-endpoints/{quote(id)}/enable", options=options)


class WebhookDeliveries(Resource):
    def list(self, params: Optional[Params] = None, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/webhook-deliveries", query=params, options=options)

    def replay(self, id: str, options: Options = None) -> Any:
        """Sends a past delivery again, for example after you fixed your endpoint."""
        return self._call("POST", f"whatsapp/webhook-deliveries/{quote(id)}/replay", options=options)


class Whatsapp(Resource):
    def __init__(self, http: Any) -> None:
        super().__init__(http)
        self.templates = Templates(http)
        self.contacts = Contacts(http)
        self.media = Media(http)
        self.conversations = Conversations(http)
        self.broadcasts = Broadcasts(http)
        self.webhook_endpoints = WebhookEndpoints(http)
        self.webhook_deliveries = WebhookDeliveries(http)

    def send(self, params: Params, options: Options = None) -> Any:
        """Sends a message. Repeating the call with the same `idempotency_key` never sends or charges it twice."""
        return self._call("POST", "whatsapp/messages", body=dict(params), send=True, options=options)

    def send_template(self, *, from_: str, to: str, template: Params, options: Options = None) -> Any:
        return self.send({"from": from_, "to": to, "type": "template", "template": template}, options)

    def send_text(self, *, from_: str, to: str, body: str, options: Options = None) -> Any:
        return self.send({"from": from_, "to": to, "type": "text", "body": body}, options)

    def get_message(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"whatsapp/messages/{quote(id)}", options=options)

    def numbers(self, options: Options = None) -> Any:
        return self._call("GET", "whatsapp/numbers", options=options)

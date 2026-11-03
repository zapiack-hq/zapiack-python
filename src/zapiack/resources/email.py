from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

from ..pagination import Page
from .base import Options, Params, Resource, UploadFile, quote


def _to_base64(content: Any) -> str:
    return content if isinstance(content, str) else base64.b64encode(bytes(content)).decode()


def _email_body(params: Params) -> Dict[str, Any]:
    body = dict(params)
    to = body.get("to")
    body["to"] = list(to) if isinstance(to, (list, tuple)) else [to]
    if body.get("attachments"):
        body["attachments"] = [{"filename": a["filename"], "content": _to_base64(a["content"])} for a in body["attachments"]]
    return body


class Contacts(Resource):
    def list(self, params: Optional[Params] = None, options: Options = None) -> Page:
        """Contacts, newest first. Filters: search, email, status, segmentId, sortBy, sortOrder, limit."""
        return self._paged("email/contacts", "data", params, options)

    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "email/contacts", body=params, options=options)

    def create_many(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "email/contacts/batch", body=params, options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"email/contacts/{quote(id)}", options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        return self._call("PATCH", f"email/contacts/{quote(id)}", body=params, options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"email/contacts/{quote(id)}", options=options)

    def unsubscribe(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"email/contacts/{quote(id)}/unsubscribe", options=options)

    def resubscribe(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"email/contacts/{quote(id)}/resubscribe", options=options)


class Segments(Resource):
    def list(self, options: Options = None) -> List[Any]:
        return self._call("GET", "email/segments", options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "email/segments", body=params, options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"email/segments/{quote(id)}", options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        return self._call("PATCH", f"email/segments/{quote(id)}", body=params, options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"email/segments/{quote(id)}", options=options)

    def add_contacts(self, id: str, contact_ids: List[str], options: Options = None) -> Any:
        return self._call("POST", f"email/segments/{quote(id)}/contacts", body={"contactIds": contact_ids}, options=options)

    def remove_contacts(self, id: str, contact_ids: List[str], options: Options = None) -> Any:
        return self._call("DELETE", f"email/segments/{quote(id)}/contacts", body={"contactIds": contact_ids}, options=options)


class Templates(Resource):
    def list(self, options: Options = None) -> Any:
        return self._call("GET", "email/templates", options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"email/templates/{quote(id)}", options=options)

    def create(self, params: Params, options: Options = None) -> Any:
        return self._call("POST", "email/templates", body=params, options=options)

    def update(self, id: str, params: Params, options: Options = None) -> Any:
        return self._call("PATCH", f"email/templates/{quote(id)}", body=params, options=options)

    def replace_content(self, id: str, html: str, options: Options = None) -> Any:
        return self._call("PUT", f"email/templates/{quote(id)}/content", body={"html": html}, options=options)

    def duplicate(self, id: str, params: Optional[Params] = None, options: Options = None) -> Any:
        return self._call("POST", f"email/templates/{quote(id)}/duplicate", body=dict(params or {}), options=options)

    def submit(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"email/templates/{quote(id)}/submit", options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"email/templates/{quote(id)}", options=options)

    def list_assets(self, id: str, options: Options = None) -> Any:
        """The images a template uses."""
        return self._call("GET", f"email/templates/{quote(id)}/assets", options=options)

    def upload_asset(self, id: str, file: UploadFile, name: Optional[str] = None, options: Options = None) -> Any:
        """Uploads an image (PNG, JPEG, GIF or WebP, up to 5 MB) for a template to use."""
        return self._call("POST", f"email/templates/{quote(id)}/assets", form=file.to_form({"name": name}), options=options)

    def add_asset_url(self, id: str, params: Params, options: Options = None) -> Any:
        """Links an image that is already online."""
        return self._call("POST", f"email/templates/{quote(id)}/assets/url", body=params, options=options)

    def remove_asset(self, id: str, asset_id: str, options: Options = None) -> None:
        self._call("DELETE", f"email/templates/{quote(id)}/assets/{quote(asset_id)}", options=options)


class Domains(Resource):
    def add(self, domain: str, options: Options = None) -> Any:
        """Registers a sending domain and returns the DNS records to publish."""
        return self._call("POST", "email/domains", body={"domain": domain}, options=options)

    def list(self, options: Options = None) -> List[Any]:
        return self._call("GET", "email/domains", options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"email/domains/{quote(id)}", options=options)

    def verify(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"email/domains/{quote(id)}/verify", options=options)

    def remove(self, id: str, options: Options = None) -> None:
        self._call("DELETE", f"email/domains/{quote(id)}", options=options)


class Email(Resource):
    def __init__(self, http: Any) -> None:
        super().__init__(http)
        self.contacts = Contacts(http)
        self.segments = Segments(http)
        self.templates = Templates(http)
        self.domains = Domains(http)

    def send(self, params: Params, options: Options = None) -> Any:
        """Sends one email. Repeating the call with the same `idempotency_key` never sends it twice.

        `to` is one address or a list; an attachment's `content` is bytes or the same base64-encoded.
        """
        return self._call("POST", "email/send", body=_email_body(params), send=True, options=options)

    def send_batch(self, emails: List[Params], options: Options = None) -> Any:
        """Sends up to 100 emails in one request. One failing does not stop the others: read `results`."""
        return self._call("POST", "email/batch", body={"emails": [_email_body(e) for e in emails]}, send=True, options=options)

    def get(self, id: str, options: Options = None) -> Any:
        return self._call("GET", f"email/{quote(id)}", options=options)

    def retry(self, id: str, options: Options = None) -> Any:
        return self._call("POST", f"email/{quote(id)}/retry", send=True, options=options)

    def suppressions(self, options: Options = None) -> Any:
        """Addresses Zapiack will not send to: bounces, complaints and unsubscribes."""
        return self._call("GET", "email/suppressions", options=options)

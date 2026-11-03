# zapiack (Python)

The official Zapiack SDK for Python. Send email, SMS and push notifications from one client.

```bash
pip install zapiack
```

Python 3.9 or later. No dependencies.

## Quickstart

```python
import os
from zapiack import Zapiack

zapiack = Zapiack(os.environ["ZAPIACK_API_KEY"])

zapiack.email.send({
    "from": "orders@myshop.com",
    "to": "ada@example.com",
    "subject": "Your order has shipped",
    "html": "<p>It is on its way.</p>",
})

zapiack.sms.send({"phone": "+2348012345678", "country": "NG", "message": "Your order has shipped"})

zapiack.push.send({
    "target": {"externalUserIds": ["user_123"]},
    "title": "Your order has shipped",
    "body": "Tap to track it",
    "link": {"app": "myshop://orders/ord_789"},
})
```

Create a secret API key in the dashboard under **Project → API Keys**. Keep it on your server: the client refuses a public app key.
The key can also come from the `ZAPIACK_API_KEY` environment variable: `Zapiack()`.

Parameters and answers are plain dictionaries, with the same names as the REST API and every other Zapiack SDK.

## What it does for you

- **Safe retries.** A failed request is retried up to twice, with backoff, on network errors, `429` and `5xx`, honouring
  `Retry-After`. Only requests that cannot happen twice are retried: reads, and sends, which carry an idempotency key.
- **Idempotent sends.** Every send gets an `Idempotency-Key` automatically, so a retried send never goes out twice. Pass your own
  to make a repeat from your code safe too: `zapiack.sms.send(params, RequestOptions(idempotency_key="order-42"))`.
- **Typed errors.** Every failure is a `ZapiackError` with a stable `code`, the HTTP `status` and a `request_id`.
- **Timeouts.** 30 seconds by default, per client or per call.
- **Pagination.** List calls return the first page; iterate it to walk every page.
- **Webhook verification.** One call checks the signature and reads the body.

```python
from zapiack import Zapiack, RequestOptions

zapiack = Zapiack("zpk_...", timeout=10, max_retries=3, app_info="my-app/1.4.0")
zapiack.sms.send(params, RequestOptions(idempotency_key="order-42", timeout=5))
```

## Email

```python
zapiack.email.send({"from": f, "to": ["a@x.com", "b@x.com"], "templateId": "tpl_1", "variables": {"name": "Ada"}})
zapiack.email.send_batch([{"from": f, "to": "a@x.com", "subject": s, "html": h}, ...])
status = zapiack.email.get(email_id)

zapiack.email.contacts.create({"email": "ada@example.com", "firstName": "Ada"})
for contact in zapiack.email.contacts.list({"status": "SUBSCRIBED"}):   # every contact, on every page
    print(contact["email"])

zapiack.email.domains.add("myshop.com")
zapiack.email.templates.upload_asset(template_id, UploadFile(logo_bytes, "logo.png", "image/png"))
```

Attachments take bytes or base64: `"attachments": [{"filename": "invoice.pdf", "content": pdf_bytes}]`.

## SMS

```python
zapiack.sms.send({"phone": "+2348012345678", "country": "NG", "message": "Hello"})
zapiack.sms.send_batch([{"phone": p, "country": "NG", "message": m}, ...])
```

## Push notifications

```python
sent = zapiack.push.send({
    "target": {"tags": {"plan": "pro"}},
    "title": "New in Pro",
    "body": "See what is new",
    "image": "https://cdn.myshop.com/launch.jpg",
    "actions": [{"id": "open", "title": "Open", "event": "launch_opened", "link": {"app": "myshop://launch"}}],
    "tracking": {"windowMinutes": 60, "screens": True, "goal": "upgrade_completed"},
    "scheduledAt": datetime(2026, 12, 1, 9, tzinfo=timezone.utc),
})

zapiack.push.messages.reschedule(sent["messageId"], "2026-12-02T09:00:00+01:00")
zapiack.push.messages.cancel(sent["messageId"])
funnel = zapiack.push.messages.funnel(sent["messageId"])
```

A scheduled push works out who it reaches when its time comes. It can be cancelled or moved while it is still scheduled, and not
after it has started going out. Device-side registration and click tracking are done by the client SDKs inside your app.

## Webhooks

Pass the **raw** request body, the `Zapiack-Signature` header and your endpoint's signing secret:

```python
from flask import Flask, request
from zapiack import ZapiackSignatureError

@app.post("/zapiack")
def hook():
    try:
        payload = zapiack.webhooks.verify(request.get_data(), request.headers.get("Zapiack-Signature"), os.environ["ZAPIACK_WEBHOOK_SECRET"])
    except ZapiackSignatureError:
        return "", 400
    for event in payload["events"]:
        if event["type"] == "push.clicked":
            print(event["externalUserId"], event["messageId"])
    return "", 204
```

`verify` raises `ZapiackSignatureError` when the signature is missing, wrong, or older than five minutes. Return any `2xx` to
acknowledge; otherwise the delivery is retried for up to a day.

## Errors

```python
from zapiack import ZapiackError

try:
    zapiack.sms.send(params)
except ZapiackError as error:
    print(error.code, error.status, error.request_id, error.details)
    if error.code == "insufficient_balance": ...
    if error.code == "rate_limited": time.sleep(error.retry_after or 1)
```

| `code` | When |
|---|---|
| `invalid_request` | The request was wrong. `details` lists what, when the API says |
| `authentication_failed` | The key is missing or not valid |
| `insufficient_balance` | The wallet cannot cover the send |
| `permission_denied` | The key may not do this |
| `not_found` | There is no such thing |
| `conflict` | It clashes with what is already there |
| `unprocessable` | The request was understood and refused |
| `rate_limited` | Too many requests. `retry_after` says how long to wait |
| `server_error` | Zapiack failed. Retried for you, then raised |
| `connection_error`, `timeout` | No answer was received |
| `invalid_signature` | A webhook was not genuine |

A code the API names itself, such as `credential_invalid`, is passed through in lower case.

## Tests

```
python -m unittest discover -s tests
```

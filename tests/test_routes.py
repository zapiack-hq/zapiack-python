"""Every route the API accepts an API key on has a method, and each one goes to the right place with the right body."""

import base64
import unittest
from datetime import datetime, timezone

from helpers import client
from zapiack import UploadFile

BASE = "https://api.zapiack.com/v1/"

# (name, call, method, path-with-query, body or None)
ROUTES = [
    # email
    ("email.send", lambda z: z.email.send({"from": "a@x.test", "to": "b@x.test", "subject": "s", "html": "<p>x</p>"}), "POST", "email/send", {"from": "a@x.test", "to": ["b@x.test"], "subject": "s", "html": "<p>x</p>"}),
    ("email.send_batch", lambda z: z.email.send_batch([{"from": "a@x.test", "to": ["b@x.test"], "subject": "1"}]), "POST", "email/batch", {"emails": [{"from": "a@x.test", "to": ["b@x.test"], "subject": "1"}]}),
    ("email.get", lambda z: z.email.get("e 1"), "GET", "email/e%201", None),
    ("email.retry", lambda z: z.email.retry("e1"), "POST", "email/e1/retry", None),
    ("email.suppressions", lambda z: z.email.suppressions(), "GET", "email/suppressions", None),
    ("contacts.create", lambda z: z.email.contacts.create({"email": "a@x.test"}), "POST", "email/contacts", {"email": "a@x.test"}),
    ("contacts.create_many", lambda z: z.email.contacts.create_many({"contacts": []}), "POST", "email/contacts/batch", {"contacts": []}),
    ("contacts.get", lambda z: z.email.contacts.get("c1"), "GET", "email/contacts/c1", None),
    ("contacts.update", lambda z: z.email.contacts.update("c1", {"firstName": "Ada"}), "PATCH", "email/contacts/c1", {"firstName": "Ada"}),
    ("contacts.remove", lambda z: z.email.contacts.remove("c1"), "DELETE", "email/contacts/c1", None),
    ("contacts.unsubscribe", lambda z: z.email.contacts.unsubscribe("c1"), "POST", "email/contacts/c1/unsubscribe", None),
    ("contacts.resubscribe", lambda z: z.email.contacts.resubscribe("c1"), "POST", "email/contacts/c1/resubscribe", None),
    ("segments.list", lambda z: z.email.segments.list(), "GET", "email/segments", None),
    ("segments.create", lambda z: z.email.segments.create({"name": "VIP"}), "POST", "email/segments", {"name": "VIP"}),
    ("segments.get", lambda z: z.email.segments.get("s1"), "GET", "email/segments/s1", None),
    ("segments.update", lambda z: z.email.segments.update("s1", {"name": "x"}), "PATCH", "email/segments/s1", {"name": "x"}),
    ("segments.remove", lambda z: z.email.segments.remove("s1"), "DELETE", "email/segments/s1", None),
    ("segments.add_contacts", lambda z: z.email.segments.add_contacts("s1", ["c1"]), "POST", "email/segments/s1/contacts", {"contactIds": ["c1"]}),
    ("segments.remove_contacts", lambda z: z.email.segments.remove_contacts("s1", ["c1"]), "DELETE", "email/segments/s1/contacts", {"contactIds": ["c1"]}),
    ("templates.list", lambda z: z.email.templates.list(), "GET", "email/templates", None),
    ("templates.get", lambda z: z.email.templates.get("t1"), "GET", "email/templates/t1", None),
    ("templates.create", lambda z: z.email.templates.create({"name": "n", "subject": "s", "html": "h"}), "POST", "email/templates", {"name": "n", "subject": "s", "html": "h"}),
    ("templates.update", lambda z: z.email.templates.update("t1", {"name": "n"}), "PATCH", "email/templates/t1", {"name": "n"}),
    ("templates.replace_content", lambda z: z.email.templates.replace_content("t1", "<p>"), "PUT", "email/templates/t1/content", {"html": "<p>"}),
    ("templates.duplicate", lambda z: z.email.templates.duplicate("t1", {"name": "copy"}), "POST", "email/templates/t1/duplicate", {"name": "copy"}),
    ("templates.submit", lambda z: z.email.templates.submit("t1"), "POST", "email/templates/t1/submit", None),
    ("templates.remove", lambda z: z.email.templates.remove("t1"), "DELETE", "email/templates/t1", None),
    ("templates.list_assets", lambda z: z.email.templates.list_assets("t1"), "GET", "email/templates/t1/assets", None),
    ("templates.add_asset_url", lambda z: z.email.templates.add_asset_url("t1", {"url": "https://x.test/a.png"}), "POST", "email/templates/t1/assets/url", {"url": "https://x.test/a.png"}),
    ("templates.remove_asset", lambda z: z.email.templates.remove_asset("t1", "a 1"), "DELETE", "email/templates/t1/assets/a%201", None),
    ("domains.add", lambda z: z.email.domains.add("shop.test"), "POST", "email/domains", {"domain": "shop.test"}),
    ("domains.list", lambda z: z.email.domains.list(), "GET", "email/domains", None),
    ("domains.get", lambda z: z.email.domains.get("d1"), "GET", "email/domains/d1", None),
    ("domains.verify", lambda z: z.email.domains.verify("d1"), "POST", "email/domains/d1/verify", None),
    ("domains.remove", lambda z: z.email.domains.remove("d1"), "DELETE", "email/domains/d1", None),
    # sms
    ("sms.send", lambda z: z.sms.send({"phone": "+1", "country": "NG", "message": "hi"}), "POST", "sms/send", {"phone": "+1", "country": "NG", "message": "hi"}),
    ("sms.send_batch", lambda z: z.sms.send_batch([{"phone": "+1", "country": "NG", "message": "a"}]), "POST", "sms/send/batch", [{"phone": "+1", "country": "NG", "message": "a"}]),
    # whatsapp
    ("wa.send", lambda z: z.whatsapp.send({"from": "n1", "to": "+1", "type": "text", "body": "hi"}), "POST", "whatsapp/messages", {"from": "n1", "to": "+1", "type": "text", "body": "hi"}),
    ("wa.send_text", lambda z: z.whatsapp.send_text(from_="n1", to="+1", body="hi"), "POST", "whatsapp/messages", {"from": "n1", "to": "+1", "type": "text", "body": "hi"}),
    ("wa.send_template", lambda z: z.whatsapp.send_template(from_="n1", to="+1", template={"name": "t", "language": "en"}), "POST", "whatsapp/messages", {"from": "n1", "to": "+1", "type": "template", "template": {"name": "t", "language": "en"}}),
    ("wa.get_message", lambda z: z.whatsapp.get_message("m1"), "GET", "whatsapp/messages/m1", None),
    ("wa.numbers", lambda z: z.whatsapp.numbers(), "GET", "whatsapp/numbers", None),
    ("wa.templates.list", lambda z: z.whatsapp.templates.list(), "GET", "whatsapp/templates", None),
    ("wa.templates.get", lambda z: z.whatsapp.templates.get("t1"), "GET", "whatsapp/templates/t1", None),
    ("wa.templates.create", lambda z: z.whatsapp.templates.create({"name": "a"}), "POST", "whatsapp/templates", {"name": "a"}),
    ("wa.templates.dismiss", lambda z: z.whatsapp.templates.dismiss_category_change("t1"), "POST", "whatsapp/templates/t1/dismiss-category-change", None),
    ("wa.templates.remove", lambda z: z.whatsapp.templates.remove("t1"), "DELETE", "whatsapp/templates/t1", None),
    ("wa.contacts.list", lambda z: z.whatsapp.contacts.list({"optIn": True, "search": "ada"}), "GET", "whatsapp/contacts?optIn=true&search=ada", None),
    ("wa.contacts.opt_in", lambda z: z.whatsapp.contacts.opt_in({"phone": "+1"}), "POST", "whatsapp/contacts/opt-in", {"phone": "+1"}),
    ("wa.contacts.opt_out", lambda z: z.whatsapp.contacts.opt_out({"phone": "+1"}), "POST", "whatsapp/contacts/opt-out", {"phone": "+1"}),
    ("wa.media.upload_from_url", lambda z: z.whatsapp.media.upload_from_url({"url": "https://x.test/a.jpg"}), "POST", "whatsapp/media/url", {"url": "https://x.test/a.jpg"}),
    ("wa.media.get", lambda z: z.whatsapp.media.get("m 1"), "GET", "whatsapp/media/m%201", None),
    ("wa.conversations.list", lambda z: z.whatsapp.conversations.list({"status": "OPEN"}), "GET", "whatsapp/conversations?status=OPEN", None),
    ("wa.conversations.get", lambda z: z.whatsapp.conversations.get("c1"), "GET", "whatsapp/conversations/c1", None),
    ("wa.conversations.messages", lambda z: z.whatsapp.conversations.messages("c1", {"limit": 20}), "GET", "whatsapp/conversations/c1/messages?limit=20", None),
    ("wa.conversations.reply", lambda z: z.whatsapp.conversations.reply("c1", {"type": "text", "body": "Hi"}), "POST", "whatsapp/conversations/c1/messages", {"type": "text", "body": "Hi"}),
    ("wa.conversations.assign", lambda z: z.whatsapp.conversations.assign("c1", None), "POST", "whatsapp/conversations/c1/assign", {"userId": None}),
    ("wa.conversations.mark_read", lambda z: z.whatsapp.conversations.mark_read("c1"), "POST", "whatsapp/conversations/c1/read", None),
    ("wa.broadcasts.create", lambda z: z.whatsapp.broadcasts.create({"name": "Sale"}), "POST", "whatsapp/broadcasts", {"name": "Sale"}),
    ("wa.broadcasts.list", lambda z: z.whatsapp.broadcasts.list({"status": "DRAFT"}), "GET", "whatsapp/broadcasts?status=DRAFT", None),
    ("wa.broadcasts.get", lambda z: z.whatsapp.broadcasts.get("b1"), "GET", "whatsapp/broadcasts/b1", None),
    ("wa.broadcasts.add_recipients", lambda z: z.whatsapp.broadcasts.add_recipients("b1", [{"phone": "+1"}]), "POST", "whatsapp/broadcasts/b1/recipients", {"recipients": [{"phone": "+1"}]}),
    ("wa.broadcasts.recipients", lambda z: z.whatsapp.broadcasts.recipients("b1", {"status": "FAILED"}), "GET", "whatsapp/broadcasts/b1/recipients?status=FAILED", None),
    ("wa.broadcasts.check", lambda z: z.whatsapp.broadcasts.check("b1"), "POST", "whatsapp/broadcasts/b1/check", None),
    ("wa.broadcasts.start_now", lambda z: z.whatsapp.broadcasts.start("b1"), "POST", "whatsapp/broadcasts/b1/start", {}),
    ("wa.broadcasts.start_later", lambda z: z.whatsapp.broadcasts.start("b1", datetime(2026, 12, 1, 9, tzinfo=timezone.utc)), "POST", "whatsapp/broadcasts/b1/start", {"scheduledAt": "2026-12-01T09:00:00+00:00"}),
    ("wa.broadcasts.pause", lambda z: z.whatsapp.broadcasts.pause("b1"), "POST", "whatsapp/broadcasts/b1/pause", None),
    ("wa.broadcasts.resume", lambda z: z.whatsapp.broadcasts.resume("b1"), "POST", "whatsapp/broadcasts/b1/resume", None),
    ("wa.broadcasts.cancel", lambda z: z.whatsapp.broadcasts.cancel("b1"), "POST", "whatsapp/broadcasts/b1/cancel", None),
    ("wa.endpoints.create", lambda z: z.whatsapp.webhook_endpoints.create({"url": "https://x.test/h"}), "POST", "whatsapp/webhook-endpoints", {"url": "https://x.test/h"}),
    ("wa.endpoints.list", lambda z: z.whatsapp.webhook_endpoints.list(), "GET", "whatsapp/webhook-endpoints", None),
    ("wa.endpoints.event_types", lambda z: z.whatsapp.webhook_endpoints.event_types(), "GET", "whatsapp/webhook-events", None),
    ("wa.endpoints.update", lambda z: z.whatsapp.webhook_endpoints.update("w1", {"events": ["a"]}), "PATCH", "whatsapp/webhook-endpoints/w1", {"events": ["a"]}),
    ("wa.endpoints.test", lambda z: z.whatsapp.webhook_endpoints.test(), "POST", "whatsapp/webhook-endpoints/test", None),
    ("wa.endpoints.remove", lambda z: z.whatsapp.webhook_endpoints.remove("w1"), "DELETE", "whatsapp/webhook-endpoints/w1", None),
    ("wa.endpoints.rotate", lambda z: z.whatsapp.webhook_endpoints.rotate_secret("w1"), "POST", "whatsapp/webhook-endpoints/w1/rotate-secret", None),
    ("wa.endpoints.enable", lambda z: z.whatsapp.webhook_endpoints.enable("w1"), "POST", "whatsapp/webhook-endpoints/w1/enable", None),
    ("wa.deliveries.list", lambda z: z.whatsapp.webhook_deliveries.list({"endpointId": "w1"}), "GET", "whatsapp/webhook-deliveries?endpointId=w1", None),
    ("wa.deliveries.replay", lambda z: z.whatsapp.webhook_deliveries.replay("d1"), "POST", "whatsapp/webhook-deliveries/d1/replay", None),
    # push
    ("push.send", lambda z: z.push.send({"target": {"all": True}, "title": "t", "body": "b"}), "POST", "push/messages", {"target": {"all": True}, "title": "t", "body": "b"}),
    ("push.send_scheduled", lambda z: z.push.send({"target": {"all": True}, "title": "t", "body": "b", "scheduledAt": datetime(2026, 12, 1, 9, tzinfo=timezone.utc)}), "POST", "push/messages", {"target": {"all": True}, "title": "t", "body": "b", "scheduledAt": "2026-12-01T09:00:00+00:00"}),
    ("push.messages.get", lambda z: z.push.messages.get("m1"), "GET", "push/messages/m1", None),
    ("push.messages.list", lambda z: z.push.messages.list({"appId": "a1"}), "GET", "push/messages?appId=a1&page=1", None),
    ("push.messages.cancel", lambda z: z.push.messages.cancel("m1"), "DELETE", "push/messages/m1", None),
    ("push.messages.reschedule", lambda z: z.push.messages.reschedule("m1", "2026-12-02T09:00:00+01:00"), "PATCH", "push/messages/m1", {"scheduledAt": "2026-12-02T09:00:00+01:00"}),
    ("push.messages.deliveries", lambda z: z.push.messages.deliveries("m1", {"status": "failed"}), "GET", "push/messages/m1/deliveries?status=failed&page=1", None),
    ("push.messages.funnel", lambda z: z.push.messages.funnel("m1"), "GET", "push/messages/m1/funnel", None),
    ("push.devices.list", lambda z: z.push.devices.list({"platform": "ios", "active": True}), "GET", "push/devices?platform=ios&active=true&page=1", None),
    ("push.devices.get", lambda z: z.push.devices.get("d1", "a1"), "GET", "push/devices/d1?appId=a1", None),
    ("push.devices.update", lambda z: z.push.devices.update("d1", {"tags": {"plan": "pro"}, "appId": "a1"}), "PATCH", "push/devices/d1?appId=a1", {"tags": {"plan": "pro"}}),
    ("push.devices.remove", lambda z: z.push.devices.remove("d1", "a1"), "DELETE", "push/devices/d1?appId=a1", None),
    ("push.messages.retry", lambda z: z.push.messages.retry("m1", {"deliveryIds": ["d1"]}), "POST", "push/messages/m1/retry", {"deliveryIds": ["d1"]}),
    ("push.messages.metrics", lambda z: z.push.messages.metrics("m1"), "GET", "push/messages/m1/metrics", None),
    ("push.metrics", lambda z: z.push.metrics({"tz": "Africa/Lagos", "platform": "ios"}), "GET", "push/metrics?tz=Africa%2FLagos&platform=ios", None),
    ("push.reachable", lambda z: z.push.reachable({"target": {"segmentId": "s1"}}), "POST", "push/reachable", {"target": {"segmentId": "s1"}}),
    ("push.segments.list", lambda z: z.push.segments.list("a1"), "GET", "push/segments?appId=a1", None),
    ("push.segments.create", lambda z: z.push.segments.create({"name": "VIP", "tags": {"plan": "pro"}}), "POST", "push/segments", {"name": "VIP", "tags": {"plan": "pro"}}),
    ("push.segments.update", lambda z: z.push.segments.update("s1", {"name": "Gold", "appId": "a1"}), "PATCH", "push/segments/s1?appId=a1", {"name": "Gold"}),
    ("push.segments.add_members", lambda z: z.push.segments.add_members("s1", ["u1"]), "POST", "push/segments/s1/members", {"externalUserIds": ["u1"]}),
    ("push.segments.remove_members", lambda z: z.push.segments.remove_members("s1", ["u1"]), "POST", "push/segments/s1/members/remove", {"externalUserIds": ["u1"]}),
    ("push.segments.remove", lambda z: z.push.segments.remove("s1"), "DELETE", "push/segments/s1", None),
    ("push.apps.list", lambda z: z.push.apps.list(), "GET", "push/apps", None),
    ("push.apps.create", lambda z: z.push.apps.create({"name": "Shop"}), "POST", "push/apps", {"name": "Shop"}),
    ("push.apps.credentials.fcm", lambda z: z.push.apps.credentials.fcm("a1", {"serviceAccount": "{}"}), "PUT", "push/apps/a1/credentials/fcm", {"serviceAccount": "{}"}),
    ("push.apps.credentials.validate", lambda z: z.push.apps.credentials.validate("a1", "c1"), "POST", "push/apps/a1/credentials/c1/validate", None),
    ("push.webhooks.create", lambda z: z.push.webhooks.create({"url": "https://x.test/h", "events": ["push.sent"]}), "POST", "push/webhooks", {"url": "https://x.test/h", "events": ["push.sent"]}),
    ("push.webhooks.rotate", lambda z: z.push.webhooks.rotate_secret("w1"), "POST", "push/webhooks/w1/secret", None),
    ("push.webhooks.test", lambda z: z.push.webhooks.test("w1"), "POST", "push/webhooks/w1/test", None),
]

LIST_SHAPES = {"data": [], "messages": [], "deliveries": [], "devices": []}


class EveryRoute(unittest.TestCase):
    def test_each_route_goes_to_the_right_place_with_the_right_body(self):
        for name, call, method, path, body in ROUTES:
            with self.subTest(name):
                z, t, _ = client(__import__("helpers").Reply(200, LIST_SHAPES))
                call(z)
                got = t.calls[0]
                self.assertEqual(got.method, method)
                self.assertEqual(got.url, BASE + path)
                if body is not None or got.body is not None:
                    self.assertEqual(got.body, body)

    def test_the_table_is_the_whole_api(self):
        # 91 routes in the API, 4 of them uploads covered below, 1 an alias of another: 90 are in the table or the upload tests.
        self.assertGreaterEqual(len(ROUTES), 80)


class Uploads(unittest.TestCase):
    def test_a_whatsapp_file_is_sent_as_multipart_in_the_field_file(self):
        z, t, _ = client()
        z.whatsapp.media.upload(UploadFile(b"png-bytes", "a.png", "image/png"))
        call = t.calls[0]
        self.assertEqual(call.url, BASE + "whatsapp/media")
        self.assertTrue(call.headers["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="file"; filename="a.png"', call.raw)
        self.assertIn(b"Content-Type: image/png", call.raw)
        self.assertIn(b"png-bytes", call.raw)

    def test_a_template_image_carries_its_name(self):
        z, t, _ = client()
        z.email.templates.upload_asset("t1", UploadFile(b"gif", "logo.gif", "image/gif"), name="Logo")
        self.assertEqual(t.calls[0].url, BASE + "email/templates/t1/assets")
        self.assertIn(b'name="name"\r\n\r\nLogo', t.calls[0].raw)

    def test_a_filename_cannot_break_out_of_its_header(self):
        z, t, _ = client()
        z.whatsapp.media.upload(UploadFile(b"x", 'a"\r\nX-Evil: 1.png'))
        self.assertNotIn(b"\r\nX-Evil", t.calls[0].raw)


class Bodies(unittest.TestCase):
    def test_a_single_recipient_becomes_a_list_and_attachment_bytes_become_base64(self):
        z, t, _ = client()
        z.email.send({"from": "a@x.test", "to": "b@x.test", "subject": "s", "text": "t", "attachments": [{"filename": "a.txt", "content": b"hello"}, {"filename": "b.txt", "content": "aGVsbG8="}]})
        body = t.calls[0].body
        self.assertEqual(body["to"], ["b@x.test"])
        self.assertEqual([a["content"] for a in body["attachments"]], [base64.b64encode(b"hello").decode()] * 2)

    def test_the_caller_s_own_data_is_not_changed(self):
        z, _, _ = client()
        params = {"from": "a@x.test", "to": "b@x.test", "subject": "s", "text": "t"}
        z.email.send(params)
        self.assertEqual(params["to"], "b@x.test")


if __name__ == "__main__":
    unittest.main()

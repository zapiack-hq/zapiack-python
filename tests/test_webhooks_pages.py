import time
import unittest

from helpers import Reply, client
from zapiack import Webhooks, ZapiackSignatureError

SECRET = "whsec_test"
BODY = '{"events":[{"type":"push.clicked","messageId":"m1"}]}'


class WebhookTests(unittest.TestCase):
    wh = Webhooks()

    def test_a_genuine_webhook_is_read(self):
        header = self.wh.sign(SECRET, BODY)
        self.assertEqual(self.wh.verify(BODY, header, SECRET)["events"][0]["messageId"], "m1")

    def test_bytes_work_as_well_as_text(self):
        header = self.wh.sign(SECRET, BODY)
        self.assertTrue(self.wh.is_valid(BODY.encode(), header, SECRET))

    def test_a_changed_body_is_refused(self):
        header = self.wh.sign(SECRET, BODY)
        with self.assertRaisesRegex(ZapiackSignatureError, "does not match"):
            self.wh.verify(BODY.replace("m1", "m2"), header, SECRET)

    def test_a_wrong_secret_is_refused(self):
        self.assertFalse(self.wh.is_valid(BODY, self.wh.sign("whsec_other", BODY), SECRET))

    def test_missing_and_malformed_headers_are_refused(self):
        for header in (None, "", "v1=abc", "t=abc,v1=" + "0" * 64, "t=1,v1=short"):
            with self.assertRaisesRegex(ZapiackSignatureError, "missing or malformed"):
                self.wh.verify(BODY, header, SECRET)

    def test_an_old_webhook_is_refused_so_a_copy_cannot_be_replayed(self):
        header = self.wh.sign(SECRET, BODY, int(time.time()) - 3600)
        with self.assertRaisesRegex(ZapiackSignatureError, "too old"):
            self.wh.verify(BODY, header, SECRET)

    def test_the_tolerance_can_be_changed(self):
        header = self.wh.sign(SECRET, BODY, int(time.time()) - 3600)
        self.assertTrue(self.wh.is_valid(BODY, header, SECRET, tolerance_seconds=7200))

    def test_a_signed_body_that_is_not_json_is_refused(self):
        header = self.wh.sign(SECRET, "not json")
        with self.assertRaisesRegex(ZapiackSignatureError, "not valid JSON"):
            self.wh.verify("not json", header, SECRET)

    def test_the_error_has_the_stable_code(self):
        with self.assertRaises(ZapiackSignatureError) as r:
            self.wh.verify(BODY, None, SECRET)
        self.assertEqual((r.exception.code, r.exception.status), ("invalid_signature", 400))

    def test_the_header_matches_what_the_other_sdks_make(self):
        # The same secret, time and body give the same signature in every Zapiack SDK.
        self.assertEqual(self.wh.sign("whsec_test", '{"a":1}', 1793496000), "t=1793496000,v1=" + __import__("hmac").new(b"whsec_test", b'1793496000.{"a":1}', "sha256").hexdigest())


class PageTests(unittest.TestCase):
    def pages(self):
        return client(
            Reply(200, {"data": [{"id": "1"}, {"id": "2"}], "meta": {"total": 5, "page": 1, "limit": 2, "totalPages": 3}}),
            Reply(200, {"data": [{"id": "3"}, {"id": "4"}], "meta": {"total": 5, "page": 2, "limit": 2, "totalPages": 3}}),
            Reply(200, {"data": [{"id": "5"}], "meta": {"total": 5, "page": 3, "limit": 2, "totalPages": 3}}),
        )

    def test_the_first_page_is_the_result_and_the_rest_come_when_wanted(self):
        z, t, _ = self.pages()
        page = z.email.contacts.list({"status": "SUBSCRIBED"})
        self.assertEqual([c["id"] for c in page.data], ["1", "2"])
        self.assertTrue(page.has_next_page())
        self.assertEqual(len(t.calls), 1)
        self.assertEqual([c["id"] for c in page.next_page().data], ["3", "4"])

    def test_iterating_walks_every_item_on_every_page(self):
        z, t, _ = self.pages()
        self.assertEqual([c["id"] for c in z.email.contacts.list()], ["1", "2", "3", "4", "5"])
        self.assertEqual(len(t.calls), 3)
        self.assertIn("page=3", t.calls[2].url)

    def test_filters_go_in_the_query(self):
        z, t, _ = self.pages()
        z.email.contacts.list({"status": "SUBSCRIBED", "limit": 2})
        self.assertIn("status=SUBSCRIBED", t.calls[0].url)
        self.assertIn("limit=2", t.calls[0].url)

    def test_the_last_page_says_so(self):
        z, _, _ = client(Reply(200, {"data": [{"id": "1"}], "meta": {"total": 1, "page": 1, "pageSize": 50, "totalPages": 1}}))
        page = z.email.contacts.list()
        self.assertFalse(page.has_next_page())
        with self.assertRaises(IndexError):
            page.next_page()

    def test_a_list_with_no_meta_is_one_page(self):
        z, _, _ = client(Reply(200, {"messages": [{"id": "m"}]}))
        page = z.push.messages.list()
        self.assertEqual(len(page.data), 1)
        self.assertFalse(page.has_next_page())


if __name__ == "__main__":
    unittest.main()

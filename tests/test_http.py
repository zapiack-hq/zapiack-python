import unittest

from helpers import Reply, client
from zapiack import RequestOptions, Zapiack, ZapiackConfigError, ZapiackConnectionError, ZapiackError
from zapiack._http import backoff_seconds, parse_retry_after


class Headers(unittest.TestCase):
    def test_carries_the_key_and_identifies_itself(self):
        z, t, _ = client()
        z.email.get("e1")
        h = t.calls[0].headers
        self.assertEqual(h["Authorization"], "Bearer zpk_abc12345_secret")
        self.assertTrue(h["User-Agent"].startswith("zapiack-python/0.1.0 python/"))
        self.assertTrue(h["X-Request-Id"])
        self.assertEqual(t.calls[0].url, "https://api.zapiack.com/v1/email/e1")

    def test_a_send_gets_an_idempotency_key_and_a_read_does_not(self):
        z, t, _ = client()
        z.sms.send({"phone": "+1", "country": "NG", "message": "hi"})
        z.email.get("e1")
        self.assertTrue(t.calls[0].headers["Idempotency-Key"])
        self.assertNotIn("Idempotency-Key", t.calls[1].headers)

    def test_your_own_key_is_used(self):
        z, t, _ = client()
        z.sms.send({"phone": "+1", "country": "NG", "message": "hi"}, RequestOptions(idempotency_key="order-42"))
        self.assertEqual(t.calls[0].headers["Idempotency-Key"], "order-42")

    def test_an_id_cannot_change_where_the_request_goes(self):
        z, t, _ = client()
        z.email.get("a/../../admin?x=1")
        self.assertEqual(t.calls[0].url, "https://api.zapiack.com/v1/email/a%2F..%2F..%2Fadmin%3Fx%3D1")

    def test_app_info_is_added_to_the_user_agent(self):
        z, t, _ = client(app_info="my-app/1.4.0")
        z.email.get("e1")
        self.assertTrue(t.calls[0].headers["User-Agent"].endswith(" my-app/1.4.0"))


class Setup(unittest.TestCase):
    def test_a_key_is_needed(self):
        import os

        saved = os.environ.pop("ZAPIACK_API_KEY", None)
        try:
            with self.assertRaises(ZapiackConfigError):
                Zapiack()
        finally:
            if saved:
                os.environ["ZAPIACK_API_KEY"] = saved

    def test_the_key_can_come_from_the_environment(self):
        import os

        os.environ["ZAPIACK_API_KEY"] = "zpk_from_env"
        try:
            self.assertIsInstance(Zapiack(), Zapiack)
        finally:
            del os.environ["ZAPIACK_API_KEY"]

    def test_a_public_app_key_is_refused(self):
        with self.assertRaisesRegex(ZapiackConfigError, "public app key"):
            Zapiack("pk_public")


class Retries(unittest.TestCase):
    def test_a_busy_service_is_tried_again_and_the_answer_returned(self):
        z, t, sleeps = client(Reply(503, {"message": "busy"}), Reply(200, {"id": "e1"}))
        self.assertEqual(z.email.get("e1"), {"id": "e1"})
        self.assertEqual(len(t.calls), 2)
        self.assertEqual(len(sleeps), 1)

    def test_a_send_retries_with_the_same_idempotency_key_so_it_cannot_go_twice(self):
        z, t, _ = client(Reply(502), Reply(200, {"id": "s1"}))
        z.sms.send({"phone": "+1", "country": "NG", "message": "hi"})
        self.assertEqual(len(t.calls), 2)
        self.assertEqual(t.calls[0].headers["Idempotency-Key"], t.calls[1].headers["Idempotency-Key"])

    def test_a_write_without_a_key_is_never_repeated(self):
        z, t, _ = client(Reply(503, {"message": "busy"}))
        with self.assertRaises(ZapiackError):
            z.email.contacts.create({"email": "a@x.test"})
        self.assertEqual(len(t.calls), 1)

    def test_gives_up_after_the_retries_and_says_why(self):
        z, t, _ = client(Reply(500, {"message": "down"}))
        with self.assertRaises(ZapiackError) as raised:
            z.email.get("e1")
        self.assertEqual(len(t.calls), 3)
        self.assertEqual((raised.exception.status, raised.exception.code), (500, "server_error"))

    def test_a_client_error_is_not_retried(self):
        z, t, _ = client(Reply(404, {"message": "no"}))
        with self.assertRaises(ZapiackError) as raised:
            z.email.get("e1")
        self.assertEqual(len(t.calls), 1)
        self.assertEqual(raised.exception.code, "not_found")

    def test_retry_after_is_a_floor_for_the_wait(self):
        z, _, sleeps = client(Reply(429, {}, {"retry-after": "7"}), Reply(200))
        z.email.get("e1")
        self.assertGreaterEqual(sleeps[0], 7)

    def test_a_request_to_wait_too_long_is_not_waited_for(self):
        z, t, _ = client(Reply(429, {"message": "slow down"}, {"retry-after": "300"}))
        with self.assertRaises(ZapiackError) as raised:
            z.email.get("e1")
        self.assertEqual(len(t.calls), 1)
        self.assertEqual(raised.exception.retry_after, 300)

    def test_a_network_failure_is_retried_then_reported_as_a_connection_error(self):
        z, t, _ = client(OSError("refused"))
        with self.assertRaises(ZapiackConnectionError) as raised:
            z.email.get("e1")
        self.assertEqual((raised.exception.status, raised.exception.code), (0, "connection_error"))
        self.assertEqual(len(t.calls), 3)

    def test_a_timeout_is_named_as_one(self):
        z, _, _ = client(TimeoutError("timed out"), max_retries=0)
        with self.assertRaises(ZapiackConnectionError) as raised:
            z.email.get("e1")
        self.assertEqual(raised.exception.code, "timeout")

    def test_retries_can_be_set_per_call(self):
        z, t, _ = client(Reply(503))
        with self.assertRaises(ZapiackError):
            z.email.get("e1", RequestOptions(max_retries=0))
        self.assertEqual(len(t.calls), 1)

    def test_the_wait_grows_and_has_a_ceiling(self):
        mid = lambda: 0.5
        self.assertEqual([backoff_seconds(n, None, mid) for n in range(6)], [0.5, 1.0, 2.0, 4.0, 8.0, 8.0])

    def test_retry_after_reads_seconds_and_dates(self):
        self.assertEqual(parse_retry_after("5"), 5)
        self.assertIsNone(parse_retry_after("soon"))
        when = 1792567690  # Wed, 21 Oct 2026 07:28:10 GMT
        self.assertEqual(parse_retry_after("Wed, 21 Oct 2026 07:28:10 GMT", now=when - 10), 10)
        self.assertEqual(parse_retry_after("Wed, 21 Oct 2026 07:28:10 GMT", now=when + 99), 0)


class Errors(unittest.TestCase):
    def raised(self, status, body):
        z, _, _ = client(Reply(status, body), max_retries=0)
        with self.assertRaises(ZapiackError) as r:
            z.email.get("e1")
        return r.exception

    def test_a_code_the_api_chose_is_kept(self):
        e = self.raised(402, {"error": "InsufficientWalletBalance", "message": "Add credit"})
        self.assertEqual((e.code, e.message), ("insufficient_wallet_balance", "Add credit"))

    def test_a_generic_status_name_becomes_the_status_code(self):
        self.assertEqual(self.raised(401, {"error": "Unauthorized", "message": "bad key"}).code, "authentication_failed")
        self.assertEqual(self.raised(429, {"error": "Too Many Requests"}).code, "rate_limited")
        self.assertEqual(self.raised(402, {}).code, "insufficient_balance")

    def test_validation_messages_are_joined_and_kept_as_details(self):
        e = self.raised(400, {"message": ["to must be an email", "subject is required"]})
        self.assertEqual(e.message, "to must be an email; subject is required")
        self.assertEqual(e.details, ["to must be an email", "subject is required"])

    def test_an_unreadable_body_still_gives_a_useful_error(self):
        e = self.raised(502, None)
        self.assertEqual(e.message, "The request failed with status 502")

    def test_the_request_id_from_the_service_is_kept(self):
        z, _, _ = client(Reply(404, {"message": "no"}, {"x-request-id": "req_123"}))
        with self.assertRaises(ZapiackError) as r:
            z.email.get("e1")
        self.assertEqual(r.exception.request_id, "req_123")


if __name__ == "__main__":
    unittest.main()

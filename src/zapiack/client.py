from __future__ import annotations

import os
from typing import Callable, Optional

from ._http import HttpClient, Transport, urllib_transport
from .errors import ZapiackConfigError
from .resources.email import Email
from .resources.push import Push
from .resources.sms import Sms
from .resources.whatsapp import Whatsapp
from .webhooks import Webhooks

DEFAULT_BASE_URL = "https://api.zapiack.com/v1"


class Zapiack:
    """The Zapiack client. Create one and reuse it.

    >>> zapiack = Zapiack("zpk_...")
    >>> zapiack.sms.send({"phone": "+2348012345678", "country": "NG", "message": "Hello"})
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        app_info: Optional[str] = None,
        transport: Optional[Transport] = None,
        sleep: Optional[Callable[[float], None]] = None,
    ) -> None:
        key = api_key or os.environ.get("ZAPIACK_API_KEY")
        if not key:
            raise ZapiackConfigError("No API key. Pass it as the first argument or set ZAPIACK_API_KEY.")
        if key.startswith("pk_"):
            raise ZapiackConfigError("That is a public app key, which belongs inside an app. This client needs your secret API key.")

        import time

        http = HttpClient(
            api_key=key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            transport=transport or urllib_transport,
            app_info=app_info,
            sleep=sleep or time.sleep,
        )
        self.email = Email(http)
        self.sms = Sms(http)
        self.whatsapp = Whatsapp(http)
        self.push = Push(http)
        self.webhooks = Webhooks()

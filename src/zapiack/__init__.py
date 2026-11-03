"""The official Zapiack SDK for Python."""

from ._http import RequestOptions, TransportRequest, TransportResponse
from ._version import VERSION
from .client import Zapiack
from .errors import ZapiackConfigError, ZapiackConnectionError, ZapiackError, ZapiackSignatureError
from .pagination import Page, PageMeta
from .resources.base import UploadFile
from .webhooks import Webhooks

__version__ = VERSION

__all__ = [
    "Page",
    "PageMeta",
    "RequestOptions",
    "TransportRequest",
    "TransportResponse",
    "UploadFile",
    "VERSION",
    "Webhooks",
    "Zapiack",
    "ZapiackConfigError",
    "ZapiackConnectionError",
    "ZapiackError",
    "ZapiackSignatureError",
]

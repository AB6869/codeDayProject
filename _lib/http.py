import logging
import socket
import requests
import aiohttp
from urllib3.connection import HTTPConnection
import functools
from collections import defaultdict
from requests.adapters import HTTPAdapter


class HTTPAdapterWithSocketOptions(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL:DEFAULT@SECLEVEL=1"
        self.socket_options = kwargs.pop("socket_options", None)
        super(HTTPAdapterWithSocketOptions, self).__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.socket_options is not None:
            kwargs["socket_options"] = self.socket_options
        super(HTTPAdapterWithSocketOptions, self).init_poolmanager(*args, **kwargs)


def create_socket_opts():
    opts = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]

    if hasattr(socket, "TCP_KEEPIDLE"):
        logging.info("Setting TCP_KEEPIDLE to 120")
        opts.append((socket.SOL_TCP, socket.TCP_KEEPIDLE, 120))
    if hasattr(socket, "TCP_KEEPINTVL"):
        logging.info("Setting TCP_KEEPINTVL to 30")
        opts.append((socket.SOL_TCP, socket.TCP_KEEPINTVL, 30))
    if hasattr(socket, "TCP_KEEPCNT"):
        logging.info("Setting TCP_KEEPCNT to 8")
        opts.append((socket.SOL_TCP, socket.TCP_KEEPCNT, 8))

    logging.info("Created %d socket options", len(opts))
    return opts


class HTTPAdapterWithTCPKeepalive(HTTPAdapterWithSocketOptions):
    def __init__(self, *args, **kwargs):
        kwargs["socket_options"] = HTTPConnection.default_socket_options + create_socket_opts()
        super(HTTPAdapterWithTCPKeepalive, self).__init__(*args, **kwargs)


SESSION = None
TOKENS = defaultdict(lambda: None)


def retry_with_token(token_id, get_token, codes=None):
    if codes is None:
        codes = []

    def retry_with_token_decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            global TOKENS
            try:
                if TOKENS[token_id] is None:
                    TOKENS[token_id] = get_token()
                res = fn(*args, **kwargs, token=TOKENS[token_id])
                if isinstance(res, requests.Response) and res.status_code in [401] + codes:
                    res.raise_for_status()
                return res
            except requests.HTTPError as e:
                if e.response.status_code in [401] + codes:
                    TOKENS[token_id] = get_token()
                    return fn(*args, **kwargs, token=TOKENS[token_id])
                else:
                    raise e

        return wrapper

    return retry_with_token_decorator


def retry_with_token_async(token_id, get_token, codes=None):
    if codes is None:
        codes = []

    def retry_with_token_async_decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            global TOKENS
            try:
                if TOKENS[token_id] is None:
                    TOKENS[token_id] = get_token()
                res = await fn(*args, **kwargs, token=TOKENS[token_id])
                if isinstance(res, aiohttp.ClientResponse) and res.status_code in [401] + codes:
                    res.raise_for_status()
                return res
            except aiohttp.ClientResponseError as e:
                if e.status in [401] + codes:
                    TOKENS[token_id] = get_token()
                    return await fn(*args, **kwargs, token=TOKENS[token_id])
                raise e

        return wrapper

    return retry_with_token_async_decorator


def get_session():
    global SESSION
    if SESSION is None:
        SESSION = requests.Session()
        SESSION.mount("https", HTTPAdapterWithTCPKeepalive(max_retries=1))
    return SESSION


AIO_SESSION = None


def get_aio_session():
    global AIO_SESSION
    if AIO_SESSION is None:
        AIO_SESSION = aiohttp.ClientSession()  # Supports keepalive by default
    return AIO_SESSION

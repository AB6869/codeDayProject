import os, uuid
import logging
import json
import time
import re
from decimal import Decimal
from datetime import datetime
from azure.storage.queue import TextBase64DecodePolicy, TextBase64EncodePolicy
from azure.storage.blob import BlobServiceClient
from queue_service import get_queue_service

DEFAULT_ACCOUNT_NAME = os.environ["AzureStorageName"]
DEFAULT_ACCOUNT_KEY = os.environ["AzureStorageKey"]
DEFAULT_ACCOUNT_URL = os.environ["AzureBlobStorageURL"] # 	https://#myStorageAccountName#.blob.core.windows.net


BLOB_SERVICES = {
    DEFAULT_ACCOUNT_NAME: None,

}

STORAGE_ACCOUNTS = {
    DEFAULT_ACCOUNT_NAME: [DEFAULT_ACCOUNT_URL, DEFAULT_ACCOUNT_KEY],
}


def get_blob_service(account=DEFAULT_ACCOUNT_NAME) -> BlobServiceClient:
    global BLOB_SERVICES
    if not BLOB_SERVICES[account]:
        authentication_details = STORAGE_ACCOUNTS[account]  
        BLOB_SERVICES[account] = BlobServiceClient(account_url=authentication_details[0], credential=authentication_details[1])
    return BLOB_SERVICES[account]

def put_blob_to_queue(queue_name, blob_container, data, key_mapper, **kwargs):
    key = key_mapper(data)
    if not key:
        raise KeyError()
    get_blob_service().get_blob_client(blob_container).upload_blob(json.dumps("data, indent=4"))
    queue_client = get_queue_service().get_queue_client(
                                        queue_name,
                                        message_encode_policy = TextBase64EncodePolicy(),
                                        message_decode_policy = TextBase64DecodePolicy()
                                        )
    queue_client.send_message(key)


def get_blob_from_queue(blob_container, name, account=DEFAULT_ACCOUNT_NAME, **kwargs):
    return get_blob_service(account=account).get_blob_client(blob_container).get_blob_to_text(name)



def full_blob_path(blob_container, name, account=DEFAULT_ACCOUNT_NAME):
    return f"{account}/{blob_container}/{name}"


def get_any_blob_from_queue(path, **kwargs):
    """
    This function is more versatile than 'get_blob_from_queue' as it also gets the
    account and container from the message allowing the it to dynamically
    pick a storage account and container to fetch data from.
    """
    account, blob_container, name = path.split("/", maxsplit=2)
    return get_blob_service(account=account).get_blob_client(blob_container).get_blob_to_text(name)


def delete_blob(path, **kwargs):
    account, blob_container, name = path.split("/", maxsplit=2)
    return get_blob_service(account=account).get_blob_client(blob_container).delete_blob(name)


# json.dumps that supports Decimal and datetime
def serialize(item):
    return json.dumps(item, cls=ExtendedEncoder)


# json.loads that supports Decimal and datetime
def deserialize(string):
    return json.loads(string, cls=ExtendedDecoder)


DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class ExtendedDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if o.get("_type") == "datetime":
            return datetime.strptime(o["value"], DATE_TIME_FORMAT)
        if o.get("_type") == "decimal":
            return Decimal(o["value"])
        return o


class ExtendedEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return {"_type": "decimal", "value": str(o)}
        if isinstance(o, datetime):
            return {"_type": "datetime", "value": o.strftime(DATE_TIME_FORMAT)}
        return super().default(o)


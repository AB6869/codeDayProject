import os, uuid
import logging
import json
import time
import re
from decimal import Decimal
from datetime import datetime
from azure.storage.queue import QueueServiceClient, TextBase64DecodePolicy, TextBase64EncodePolicy
from azure.storage.blob import BlobServiceClient


DEFAULT_ACCOUNT_NAME = os.environ["AzureStorageName"]
DEFAULT_ACCOUNT_KEY = os.environ["AzureStorageKey"]
DEFAULT_ACCOUNT_URL = os.environ["AzureQueueStorageURL"] # 	https://#myStorageAccountName#.queue.core.windows.net


QUEUE_SERVICES = {
    DEFAULT_ACCOUNT_NAME: None,

}


# STORAGE_ACCOUNTS = {
#     DEFAULT_ACCOUNT_NAME: DEFAULT_ACCOUNT_KEY,
#     HOGIA_ACCOUNT_NAME: HOGIA_ACCOUNT_KEY,
# }

STORAGE_ACCOUNTS = {
    DEFAULT_ACCOUNT_NAME: [DEFAULT_ACCOUNT_URL, DEFAULT_ACCOUNT_KEY],
}


def get_queue_service(account=DEFAULT_ACCOUNT_NAME) -> QueueServiceClient:
    global QUEUE_SERVICES
    if not QUEUE_SERVICES[account]:
        authentication_details = STORAGE_ACCOUNTS[account]
        logging.info("account_url: %s", authentication_details[0])  
        logging.info("credential: %s", authentication_details[1])  
        QUEUE_SERVICES[account] = QueueServiceClient(
                                    account_url=authentication_details[0], 
                                    credential=authentication_details[1],
                                    )
    return QUEUE_SERVICES[account]


def put_queue(queue_name, message, **kwargs):
    try:
        queue_client = get_queue_service().get_queue_client(
                                            queue_name,
                                            message_encode_policy = TextBase64EncodePolicy(),
                                            message_decode_policy = TextBase64DecodePolicy()
                                            )
        queue_client.send_message(message)
    except Exception as e:
        logging.error("Failed to put message on queue: %s.", queue_name)
        logging.error(message)
        logging.error(e)



def retry(queue, count=1):
    queue_client = get_queue_service().get_queue_client(
                                        queue,
                                        message_encode_policy = TextBase64EncodePolicy(),
                                        message_decode_policy = TextBase64DecodePolicy()
                                        )
    queue_client_poison = get_queue_service().get_queue_client(queue + "-poison",
                                        message_encode_policy = TextBase64EncodePolicy(),
                                        message_decode_policy = TextBase64DecodePolicy()
                                        )
    count = int(count)
    while count > 0:
        messages = queue_client_poison.receive_messages(max_messages=min(32, count), visibility_timeout=30)
        logging.warning(messages)
        for message in messages:
            time.sleep(0.2)
            queue_client.send_message(message.content)
            queue_client_poison.delete_message(message)
        count = count - min(32, count)


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



def retry_all_msg_in_poison() -> None:
    for queue in get_queue_service().list_queues(include_metadata=True):
        if queue.name.endswith("-poison"):
            to_queue_name = re.sub(r"\-poison$", "", queue.name)
            queue_client = get_queue_service().get_queue_client(queue)
            count = queue_client.get_queue_properties().approximate_message_count
            if count > 0:
                logging.info("preforming retry for %s on queue %s", count, queue.name)
                retry(to_queue_name, count)

import os
from azure.cosmosdb.table.tableservice import TableService

SERVICES = {"default": None, "reports": None}

STORAGE_ACCOUNTS = {
    "default": {"name": os.environ["AzureStorageName"], "key": os.environ["AzureStorageKey"]},
    "reports": {"name": os.environ["AzureReportsStorageName"], "key": os.environ["AzureReportsStorageKey"]},
}


def get_table_service(account="default"):
    global SERVICES
    if SERVICES[account] is None:
        account_name = STORAGE_ACCOUNTS[account]["name"]  # os.environ["AzureStorageName"]
        account_key = STORAGE_ACCOUNTS[account]["key"]  # os.environ["AzureStorageKey"]
        SERVICES[account] = TableService(account_name=account_name, account_key=account_key)
    return SERVICES[account]

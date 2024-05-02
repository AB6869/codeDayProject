# dp-integration-template-python
Template för Digital Plattforms eventbaserade Azure Function App i Python


Create file in root folder: local.setting.json with this content:
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "AzureStorageName" : "devstoreaccount1",
    "AzureStorageKey": "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==",
    "AzureBlobStorageURL": "http://127.0.0.1:10000/devstoreaccount1",
    "AzureQueueStorageURL": "http://127.0.0.1:10001/devstoreaccount1",
    "AzureTableStorageURL": "http://127.0.0.1:10002/devstoreaccount1",
    "AzureServiceBus": "#Add connectionstring to AzureSericeBus" 
  }
}

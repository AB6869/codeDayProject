import requests
import os
import functools
import json
import logging
from _lib.cosmos import datalake
from requests.exceptions import HTTPError
from _lib.doc_type import (
            DOC_TYPE_TEST_OBJECT,
)

BASE_URL = os.environ["ApiUrl"] # https://oneagencysweden.lime-crm.com
BASE_PATH = os.environ["ApiBasePath"]
API_KEY = os.environ["ApiKey"]


BASE_SESSION = None
BASE_TOKEN = None


class FailedAuth(Exception):
    pass


class AuthSession(requests.Session):
    # In Python 3 you could place `url_base` after `*args`, but not in Python 2.
    def __init__(self, get_set_token=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        get_set_token(self)
        self.get_set_token = get_set_token

    def request(self, method, url, **kwargs):
        try:
            res = super().request(method, **kwargs)
            if res.status_code in [401, 403]:
                raise FailedAuth()
            return res
        except FailedAuth as e:
            self.get_set_token(self)
            return super().request(method, **kwargs)


def get_session():
    global BASE_SESSION
    if BASE_SESSION is None:
        BASE_SESSION = create_authenticated_session()
    return BASE_SESSION


def create_authenticated_session():
    token = API_KEY
    sesh = requests.Session()
    sesh.headers.update({"x-api-key": token, "Content-Type" : "application/json"})
    return sesh


def retry_with_token(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global BASE_TOKEN
        try:
            if BASE_TOKEN is None:
                BASE_TOKEN = API_KEY
            return func(*args, **kwargs, token=BASE_TOKEN)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                BASE_TOKEN = API_KEY
                return func(*args, **kwargs, token=BASE_TOKEN)
            else:
                raise e

    return wrapper

# Example from Lime
def get_path(objectType):
    if objectType == "LimeAssignment":
        return "assignment/"
    if objectType == "LimeDeal":
        return "deal/"
    if objectType == "LimePerson":
        return "person/"
    if objectType == "LimeCoWorker":
        return "coworker/"
    if objectType == "LimeConsultant":
        return "consultant/"
    if objectType == "LimeCompany":
        return "company/"
    return ""


def clean_ojects(objects=None, objectType=None):
    if objectType == "LimeConsultant":
        clean_consultant(objects)

def clean_attributes(item):
    if "doc_type" in item:
        if item["doc_type"] == DOC_TYPE_TEST_OBJECT:
            clean_test_object(item)
        clean_standard_attributes(item)




# Example from Lime. Update this method to support your consumed REST Service  
def clean_standard_attributes(item):
        if "_createdtime" in item:
            item["createdtime"] = item["_createdtime"]
            item.pop("_createdtime", None)
        if "_createduser" in item:        
            item["createduser"] = item["_createduser"]
            item.pop("_createduser", None)
        if "_id" in item:
            item["id"] = item["_id"]
            item.pop("_id", None)
        if "_timestamp" in item:
            item["timestamp"] = item["_timestamp"]
            item.pop("_timestamp", None)
        if "_updateduser" in item:
           item["updateduser"] = item["_updateduser"]
           item.pop("_updateduser", None)
           
        item.pop("_descriptive", None)        
        item.pop("_links", None)





def clean_test_object(consultant):
    if "key" in consultant["resourcestatus"]:
        resourcestatus = consultant["resourcestatus"]["key"]
        consultant.pop("resourcestatus", None)
        consultant["resourcestatus"] = resourcestatus


def get_all_object(object_id=None, objectType=None):
    all_objects = []
    path = get_path(objectType)
    if path:
        path = path + "?_limit=40"
        query_url = BASE_URL + BASE_PATH + path
        while query_url:
            res = get_session().get(url=query_url)
            res.raise_for_status()
            response = res.json()
            objects = response["_embedded"]["limeobjects"] # From Lime.
            clean_object(objects, objectType)
            all_objects += objects
            query_url = ""
            if "next" in response["_links"]:
                query_url = response["_links"]["next"]["href"]
    return all_objects



def get_specicic_object(object_id=None, objectType=None):
    path = get_path(objectType)
    if path:
        try:
            query_url = BASE_URL + BASE_PATH + path + str(object_id) + "/"
            res = get_session().get(url=query_url)
            res.raise_for_status()
            response = res.json()
            clean_standard_attributes(response)
            return response
        except HTTPError as ex:
            if ex.response.status_code == 404:
                return None
            else:
                raise ex         
    return None




def get_specific_connected_objects(object_id=None, objectType=None, connected_object=None):
    path = get_path(objectType)
    object_path = get_path(connected_object)
    if path:
        try:
            query_url = BASE_URL + BASE_PATH + path + str(object_id) + "/" + object_path
            res = get_session().get(url=query_url)
            res.raise_for_status()
            response = res.json()
            # clean_standard_attributes(response)
            return response["_embedded"]["limeobjects"] # Check result for propper response ex. from Lime
        except HTTPError as ex:
            if ex.response.status_code == 404:
                return None
            else:
                raise ex         
    return None



def create_object(object=None, objectType=None):
    path = get_path(objectType)
    if path:
        query_url = BASE_URL + BASE_PATH + path
        logging.info("Create %s with %s", objectType, object)

        try:        
            res = get_session().post(url=query_url, json=object)
            res.raise_for_status()
            logging.info(res.content)
            return json.loads(res.text)
        except HTTPError as error:
            logging.warning("Error code= %s", error)
            logging.warning("Error response= %s", error.response.text)
            logging.warning("Error request= %s", error.request.body)
            raise error
        



def delete_object(object=None, objectType=None):
    path = get_path(objectType)
    if path:
        query_url = BASE_URL + BASE_PATH + path
        logging.info("Delete %s with %s", objectType, object)

        try:        
            res = get_session().delete(url=query_url, json=object)
            res.raise_for_status()
            logging.info(res.content)
            return json.loads(res.text)
        except HTTPError as error:
            logging.warning("Error code= %s", error)
            logging.warning("Error response= %s", error.response.text)
            logging.warning("Error request= %s", error.request.body)
            raise error
        




def update_specific_object(object_id=None, objectType=None, object=None):
    path = get_path(objectType)
    if path:
        logging.info("object_id=%s, objectType=%s, update_json=%s",object_id, objectType, json.dumps(object))
        query_url = BASE_URL + BASE_PATH + path + str(object_id) + "/"
        try:
            res = get_session().put(url=query_url,json=object)
            res.raise_for_status()
            logging.info(res.content)
        except HTTPError as error:
            logging.warning("Error code= %s", error)
            logging.warning("Error response= %s", error.response.text)
            logging.warning("Error request= %s", error.request.body)
            raise error


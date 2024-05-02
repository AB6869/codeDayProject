import uuid


def get_unique_id():
    id = str(uuid.uuid4())
    return id


def get_base_md_doc(doc_type=None):
    if doc_type:
        current_doc = dict()
        current_doc["doc_type"] = doc_type
        current_doc["id"] = get_unique_id()
        return current_doc
    return None     
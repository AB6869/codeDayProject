"""
cosmos.py

static client for accessing Cosmos DB
"""
import os
import pymongo
from decimal import Decimal
from bson.decimal128 import Decimal128
from bson.codec_options import TypeCodec, TypeRegistry, CodecOptions

CLIENT = None

DECIMAL_CODEC_OPTIONS = None


def get_codec_options():
    global DECIMAL_CODEC_OPTIONS
    if DECIMAL_CODEC_OPTIONS is None:
        decimal_codec = DecimalCodec()
        type_registry = TypeRegistry([decimal_codec])
        DECIMAL_CODEC_OPTIONS = CodecOptions(type_registry=type_registry)
    return DECIMAL_CODEC_OPTIONS


def get_client():
    global CLIENT
    if CLIENT is None:
        uri = os.environ["MongoConnectionString"]
        CLIENT = pymongo.MongoClient(uri)
    return CLIENT


def datalake(collection):
    return get_client()["master-dev"].get_collection(collection, codec_options=get_codec_options())


class DecimalCodec(TypeCodec):
    python_type = Decimal  # the Python type acted upon by this type codec
    bson_type = Decimal128  # the BSON type acted upon by this type codec

    def transform_python(self, value):
        """Function that transforms a custom type value into a type
        that BSON can encode."""
        return Decimal128(value)

    def transform_bson(self, value):
        """Function that transforms a vanilla BSON type value into our
        custom type."""
        return value.to_decimal()

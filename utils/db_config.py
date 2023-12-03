
import pymongo
import os
from pymongo import MongoClient

mongo_ip = os.environ['MONGO_IP'] if "MONGO_IP" in os.environ else "localhost"

db_connect_string = "mongodb://{}:27017".format(mongo_ip)
db_name = os.environ['MONGO_INITDB_DATABASE'] if "MONGO_INITDB_DATABASE" in os.environ else "badgetwentytwentyfour"

print("Connecting to {}".format(db_connect_string))
username = os.environ['MONGO_INITDB_ROOT_USERNAME'] if "MONGO_INITDB_ROOT_USERNAME" in os.environ else None
password = os.environ['MONGO_INITDB_ROOT_PASSWORD'] if "MONGO_INITDB_ROOT_PASSWORD" in os.environ else None
connect_auth = username is not None and password is not None

client = None
if connect_auth:
    client = MongoClient(mongo_ip, username=username,
                         password=password,
                         authSource='admin',
                         authMechanism='SCRAM-SHA-1')
else:
    client = pymongo.MongoClient(db_connect_string)

db = client[db_name]


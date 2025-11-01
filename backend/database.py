import os
from dotenv import load_dotenv
load_dotenv()

# Force DynamoDB-only backend. This module exposes `users_collection` which
# provides async-compatible methods used throughout the codebase
# (insert_one, find_one, find, update_one).
from backend.dynamodb_client import client as db

users_collection = db.get_collection("users")

print("Using DynamoDB as primary data store (backend.dynamodb_client)")

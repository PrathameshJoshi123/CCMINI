"""Simple migration helper: copy users, documents, generated_content from MongoDB to DynamoDB.

Run locally with your Mongo and AWS credentials configured. This script is intentionally simple
and helps bootstrap DynamoDB tables with existing data.
"""
import os
import asyncio
from backend.database import db as mongo_db
from backend.dynamodb_client import DynamoDBClient

async def migrate_collection(collection_name: str):
    print(f"Migrating collection: {collection_name}")
    mongo_coll = mongo_db.get_collection(collection_name)
    dynamo = DynamoDBClient()
    dyn_coll = dynamo.get_collection(collection_name)

    cursor = mongo_coll.find({})
    count = 0
    async for doc in cursor:
        # Convert ObjectId to string
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        # Note: bson types (datetime) are preserved as-is and boto3 will handle them
        await dyn_coll.insert_one(doc)
        count += 1
    print(f"Migrated {count} items to {collection_name}")

async def main():
    for coll in ['users', 'documents', 'generated_content']:
        await migrate_collection(coll)

if __name__ == '__main__':
    asyncio.run(main())

import os
import uuid
import aioboto3
import asyncio
from datetime import datetime, date
from typing import Any, Dict, AsyncIterator, Optional
from boto3.dynamodb.conditions import Attr, Key

REGION = os.getenv("AWS_REGION", "us-east-1")


class DynamoCollection:
    def __init__(self, table_name: str):
        self.table_name = table_name
    # Note: we intentionally avoid a shared long-lived resource. Each method
    # opens an async resource context and fetches the table. Some versions of
    # aioboto3 return coroutine-like table proxies, so we normalize by awaiting
    # them when needed.

    async def insert_one(self, doc: Dict[str, Any]) -> Any:
        # Ensure string _id exists (to mimic Mongo ObjectId behavior)
        if '_id' not in doc:
            doc['_id'] = str(uuid.uuid4())

        def _serialize(obj):
            # Convert datetimes, UUIDs and nested structures into Dynamo-friendly types
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, dict):
                return {k: _serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_serialize(v) for v in obj]
            return obj

        item = _serialize(doc)

        session = aioboto3.Session()
        async with session.resource('dynamodb', region_name=REGION) as dynamo:
            table = dynamo.Table(self.table_name)
            if asyncio.iscoroutine(table):
                table = await table
            await table.put_item(Item=item)

        class Result:
            inserted_id = doc['_id']

        return Result()

    async def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        session = aioboto3.Session()
        async with session.resource('dynamodb', region_name=REGION) as dynamo:
            table = dynamo.Table(self.table_name)
            if asyncio.iscoroutine(table):
                table = await table

            # Get by primary key _id if present
            if '_id' in filter:
                key = {'_id': str(filter['_id'])}
                resp = await table.get_item(Key=key)
                return resp.get('Item')

            # Try common single-attribute lookups (email)
            if 'email' in filter:
                # Prefer GSI on 'email' named 'email-index' if available; fall back to scan
                resp = await table.query(IndexName='email-index', KeyConditionExpression=Key('email').eq(filter['email']))
                items = resp.get('Items', [])
                return items[0] if items else None

            # Fallback: scan with filter expression (slow for large tables)
            scan_kwargs = {'FilterExpression': None}
            expr = None
            for k, v in filter.items():
                cond = Attr(k).eq(v)
                expr = cond if expr is None else (expr & cond)
            if expr is None:
                resp = await table.scan()
            else:
                resp = await table.scan(FilterExpression=expr)

            items = resp.get('Items', [])
            return items[0] if items else None

    async def update_one(self, filter: Dict[str, Any], update: Dict[str, Any]) -> Any:
        # Support only $set updates used in codebase
        session = aioboto3.Session()
        async with session.resource('dynamodb', region_name=REGION) as dynamo:
            table = dynamo.Table(self.table_name)
            if asyncio.iscoroutine(table):
                table = await table
            if '_id' in filter:
                key = {'_id': str(filter['_id'])}
            else:
                # Attempt to find the item then update by its _id
                item = await self.find_one(filter)
                if not item:
                    return None
                key = {'_id': item['_id']}

            set_obj = update.get('$set', {})
            if not set_obj:
                # Not supported, no-op
                return None

            expr_parts = []
            expr_vals = {}
            def _serialize_value(v):
                if isinstance(v, (datetime, date)):
                    return v.isoformat()
                if isinstance(v, uuid.UUID):
                    return str(v)
                if isinstance(v, dict):
                    return {kk: _serialize_value(vv) for kk, vv in v.items()}
                if isinstance(v, list):
                    return [_serialize_value(x) for x in v]
                return v

            for i, (k, v) in enumerate(set_obj.items()):
                placeholder = f":v{i}"
                expr_parts.append(f"#{k} = {placeholder}")
                expr_vals[placeholder] = _serialize_value(v)

            # Build ExpressionAttributeNames and Values
            expression_attribute_names = {f"#{k}": k for k in set_obj.keys()}
            expression_attribute_values = expr_vals
            update_expression = "SET " + ", ".join(expr_parts)

            await table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
            )

        class Result:
            matched_count = 1

        return Result()

    async def find(self, filter: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        # Return an async generator that yields matching items
        session = aioboto3.Session()
        async with session.resource('dynamodb', region_name=REGION) as dynamo:
            table = dynamo.Table(self.table_name)
            if asyncio.iscoroutine(table):
                table = await table

            # If querying by document_id and GSI exists, use query; else scan
            if 'document_id' in filter:
                try:
                    resp = await table.query(IndexName='document_id-index', KeyConditionExpression=Key('document_id').eq(filter['document_id']))
                    items = resp.get('Items', [])
                    for it in items:
                        yield it
                    return
                except Exception:
                    # Fall back to scan
                    pass

            # Build filter expression
            expr = None
            for k, v in filter.items():
                cond = Attr(k).eq(v)
                expr = cond if expr is None else (expr & cond)

            if expr is None:
                resp = await table.scan()
            else:
                resp = await table.scan(FilterExpression=expr)

            items = resp.get('Items', [])
            for it in items:
                yield it


class DynamoDBClient:
    def __init__(self):
        # Tables are assumed to exist. Table names default to collection names.
        pass

    def get_collection(self, name: str) -> DynamoCollection:
        return DynamoCollection(name)


# Convenience: create a module-level client
client = DynamoDBClient()

DynamoDB migration notes for NotesLLM

Overview

This project can optionally use DynamoDB instead of MongoDB by setting `USE_DYNAMODB=true` in the environment. The provided `backend/dynamodb_client.py` provides a minimal compatibility layer exposing `get_collection(name)` with methods:

- `insert_one(doc)` -> returns object with `inserted_id`
- `find_one(filter)` -> returns item dict or None
- `find(filter)` -> async iterator yielding items
- `update_one(filter, update)` -> supports `$set` updates

Table recommendations

1. users

- Primary key: `_id` (string UUID)
- GSI: `email-index` (partition key: `email`) for login lookup
- Attributes: `_id`, `email`, `hashed_password`, `created_at`

2. documents

- Primary key: `_id` (string UUID)
- GSI: `user_id-index` (partition key: `user_id`) to list user documents
- Attributes: `_id`, `user_id`, `original_filename`, `local_path`, `processing_status`, `uploaded_at`

3. generated_content

- Primary key: `_id` (string UUID)
- GSI: `document_id-index` (partition key: `document_id`) to fetch all generated items for a document
- Attributes: `_id`, `document_id`, `user_id`, `content_type`, `content_data`, `page_number`, `created_at`

Notes

- DynamoDB scans are used as fallback for queries that don't have GSIs. For production, create the recommended GSIs.
- Elasticsearch remains the vector store; DynamoDB only replaces the primary document store.

Env vars

- `USE_DYNAMODB=true`
- `AWS_REGION` (e.g., us-east-1)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

Quick start (local)

1. Create tables in DynamoDB (via console or IaC)
2. Set env vars above
3. Install requirements: `pip install -r requirements.txt`
4. Start backend: `uvicorn backend.main:app --reload`

Migration strategy

- Start in parallel: keep MongoDB running while creating DynamoDB tables
- Implement a small migration script that reads from Mongo and writes to Dynamo (optional)
- Switch `USE_DYNAMODB=true` once Dynamo tables are populated and tested

Limitations

- The compatibility wrapper is minimal — advanced Mongo queries are not supported and will require explicit porting.
- Full-text search and vector search still rely on Elasticsearch; DynamoDB is for primary storage only.

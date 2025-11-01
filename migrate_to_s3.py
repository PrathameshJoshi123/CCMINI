#!/usr/bin/env python3
"""
Migration script to upload existing local PDF files to S3 and update database records.
Run this script after setting up your S3 bucket and configuring AWS credentials.

Usage:
    python migrate_to_s3.py

Environment variables required:
    AWS_REGION
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_S3_BUCKET_NAME
"""

import os
import asyncio
import boto3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate_local_files_to_s3():
    """Migrate existing local PDF files to S3 and update database records."""
    
    # Verify environment variables
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all AWS credentials are set.")
        return
    
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    print(f"🚀 Starting migration to S3 bucket: {bucket_name}")
    
    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    # Test S3 connection
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Successfully connected to S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"❌ Failed to connect to S3 bucket: {e}")
        print("Please verify your bucket name and AWS credentials.")
        return
    
    # Initialize database connection
    from backend.database import db
    docs_collection = db.get_collection("documents")
    
    # Find documents with local_path but no s3_key
    print("🔍 Finding documents with local files...")
    cursor = docs_collection.find({
        "local_path": {"$exists": True},
        "s3_key": {"$exists": False}
    })
    
    documents_to_migrate = []
    async for doc in cursor:
        documents_to_migrate.append(doc)
    
    if not documents_to_migrate:
        print("✅ No documents need migration. All documents are already using S3.")
        return
    
    print(f"📁 Found {len(documents_to_migrate)} documents to migrate")
    
    successful_migrations = 0
    failed_migrations = 0
    
    for doc in documents_to_migrate:
        doc_id = str(doc.get("_id"))
        local_path = doc.get("local_path")
        user_id = doc.get("user_id")
        original_filename = doc.get("original_filename")
        
        print(f"\n📤 Migrating document {doc_id}: {original_filename}")
        
        # Check if local file exists
        if not os.path.exists(local_path):
            print(f"   ⚠️  Local file not found: {local_path}")
            failed_migrations += 1
            continue
        
        try:
            # Generate S3 key
            file_ext = Path(original_filename).suffix or ".pdf"
            filename_without_ext = Path(original_filename).stem
            s3_key = f"{user_id}/{filename_without_ext}_{doc_id}{file_ext}"
            
            # Upload file to S3
            print(f"   📤 Uploading to S3: {s3_key}")
            with open(local_path, 'rb') as file:
                s3_client.upload_fileobj(
                    file, 
                    bucket_name, 
                    s3_key,
                    ExtraArgs={'ContentType': 'application/pdf'}
                )
            
            # Update database record
            print(f"   💾 Updating database record...")
            await docs_collection.update_one(
                {"_id": doc_id},
                {
                    "$set": {"s3_key": s3_key},
                    "$unset": {"local_path": ""}
                }
            )
            
            print(f"   ✅ Successfully migrated: {original_filename}")
            successful_migrations += 1
            
        except Exception as e:
            print(f"   ❌ Failed to migrate {original_filename}: {e}")
            failed_migrations += 1
    
    print(f"\n🎉 Migration completed!")
    print(f"✅ Successfully migrated: {successful_migrations} documents")
    if failed_migrations > 0:
        print(f"❌ Failed to migrate: {failed_migrations} documents")
    
    if successful_migrations > 0:
        print(f"\n📝 Next steps:")
        print(f"1. Verify files in S3 bucket: {bucket_name}")
        print(f"2. Test document processing with the migrated files")
        print(f"3. Update your frontend to use the new upload flow")
        print(f"4. Once everything works, you can safely delete the local 'uploads/' directory")

if __name__ == "__main__":
    print("🔄 PDF to S3 Migration Script")
    print("=" * 50)
    asyncio.run(migrate_local_files_to_s3())
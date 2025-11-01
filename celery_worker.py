import os
import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from celery import Celery
import aioboto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure Celery to use Redis as broker and backend
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
logger.info("Celery broker URL: %s", REDIS_URL)
app = Celery("cc_mini", broker=REDIS_URL, backend=REDIS_URL)

# Task implementation will reuse existing project modules. Import lazily inside task to avoid
# import-time side effects when Celery worker imports this module.


def _run_async(coro):
    """Run an async coroutine from sync Celery task context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If we are already in a running loop (unlikely in Celery), create a new one
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    else:
        return asyncio.run(coro)


@app.task(name="tasks.process_document")
def process_document(document_id: str, user_id: str):
    """Celery task wrapper for processing an uploaded document.

    This function imports async helpers from the application and runs them in an
    asyncio event loop so we can keep the existing async code (Motor, etc.) intact.
    """
    logger.info("Celery task 'process_document' called with document_id=%s user_id=%s", document_id, user_id)

    # Import inside task to avoid heavy imports at module import time.
    from backend.utils.pdf_parser import extract_text_from_pdf
    from backend.models.document import (
        ProcessingStatusEnum,
        ContentTypeEnum,
        Summary,
        MindMapNode,
        FlashcardList,
    )
    from backend.utils.search import create_langchain_indexes
    from backend.database import db
    from langchain.output_parsers import PydanticOutputParser
    from langchain.prompts import PromptTemplate
    try:
        # Use langchain_mistralai if available
        from langchain_mistralai.chat_models import ChatMistralAI
    except Exception:
        ChatMistralAI = None

    async def _process():
        docs_collection = db.get_collection("documents")
        gen_collection = db.get_collection("generated_content")

        # Mark as processing (use string _id for DynamoDB)
        logger.info("Updating document %s status -> PROCESSING", document_id)
        try:
            res = await docs_collection.update_one({"_id": document_id}, {"$set": {"processing_status": ProcessingStatusEnum.PROCESSING.value}})
            logger.info("Update result for PROCESSING: %s", getattr(res, 'matched_count', res))
            # Read back and log stored status
            try:
                stored = await docs_collection.find_one({"_id": document_id})
                logger.info("Stored document after PROCESSING update: %s", stored)
            except Exception as e:
                logger.exception("Failed to read back document %s after PROCESSING update: %s", document_id, e)
        except Exception as e:
            logger.exception("Failed to update document %s to PROCESSING: %s", document_id, e)

        max_retries = 3
        attempt = 0
        while attempt < max_retries:
            logger.info("Processing attempt %d/%d for document %s", attempt + 1, max_retries, document_id)
            try:
                # Fetch document to get s3_key (Dynamo uses string _id)
                doc = await docs_collection.find_one({"_id": document_id})
                if not doc:
                    logger.error("Document %s not found in DB", document_id)
                    raise RuntimeError("Document not found")

                s3_key = doc.get("s3_key")
                if not s3_key:
                    logger.error("Document %s has no s3_key", document_id)
                    raise RuntimeError("Document has no S3 key")

                logger.info("Starting S3 download and text extraction for %s (s3_key=%s)", document_id, s3_key)
                
                # Download file from S3 to temporary file
                bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
                if not bucket_name:
                    raise RuntimeError("AWS_S3_BUCKET_NAME not configured")
                
                # Create temporary file for downloaded PDF
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                try:
                    # Download file from S3 using aioboto3
                    session = aioboto3.Session()
                    async with session.client(
                        's3',
                        region_name=os.getenv('AWS_REGION'),
                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                        aws_session_token=os.getenv('AWS_SESSION_TOKEN')
                    ) as s3_client:
                        logger.info("Downloading S3 object %s from bucket %s to %s", s3_key, bucket_name, temp_path)
                        response = await s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                        
                        # Write downloaded content to temporary file
                        with open(temp_path, 'wb') as temp_file:
                            async for chunk in response['Body']:
                                temp_file.write(chunk)
                        
                        logger.info("Successfully downloaded S3 object to temporary file %s", temp_path)
                    
                    # Extract text from the downloaded PDF
                    text_chunks = extract_text_from_pdf(temp_path)
                
                finally:
                    # Clean up temporary file
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                            logger.info("Cleaned up temporary file %s", temp_path)
                    except Exception as cleanup_err:
                        logger.warning("Failed to clean up temporary file %s: %s", temp_path, cleanup_err)
                
                logger.info("Text extraction complete for %s: %d chunks", document_id, len(text_chunks) if hasattr(text_chunks, '__len__') else -1)

                # If ChatMistralAI is available, use it; otherwise, fall back to simple placeholder
                if ChatMistralAI is None:
                    logger.warning("ChatMistralAI not available; using placeholder generated content for %s", document_id)
                    # create simple placeholders
                    summary_json = {"title": doc.get("original_filename"), "content": "[LLM not available]"}
                    mind_json = {"title": doc.get("original_filename"), "children": []}
                    flash_json = {"flashcards": []}
                else:
                    logger.info("Initializing LLM for document %s", document_id)
                    llm = ChatMistralAI(model="mistral-large-latest", temperature=0)

                    # SUMMARY
                    logger.info("Generating SUMMARY for %s", document_id)
                    summary_parser = PydanticOutputParser(pydantic_object=Summary)
                    format_instructions = summary_parser.get_format_instructions()
                    summary_template_str = (
                        "You are an expert tutor. Produce a concise summary of the following document text.\n"
                        "Follow the output schema exactly.\n\n{format_instructions}\n\nDocument Text:\n{document_text}"
                    )
                    # Pass format_instructions as a variable to avoid Python str.format interpreting braces inside schema
                    summary_chain = PromptTemplate(template=summary_template_str, input_variables=["document_text", "format_instructions"]) | llm | summary_parser
                    summary_result = summary_chain.invoke({
                        "document_text": "\n\n".join([c.text for c in text_chunks if hasattr(c, 'text')]),
                        "format_instructions": format_instructions,
                    })
                    summary_json = summary_result.dict()
                    logger.info("SUMMARY generation complete for %s", document_id)

                    # MINDMAP
                    mind_parser = PydanticOutputParser(pydantic_object=MindMapNode)
                    mind_format_instructions = mind_parser.get_format_instructions()
                    mind_template_str = (
                        "Create a hierarchical mind map of the key topics in the following document text. Output must conform to the MindMapNode Pydantic model.\n\n{format_instructions}\n\nDocument Text:\n{document_text}"
                    )
                    mind_chain = PromptTemplate(template=mind_template_str, input_variables=["document_text", "format_instructions"]) | llm | mind_parser
                    logger.info("Generating MINDMAP for %s", document_id)
                    mind_result = mind_chain.invoke({
                        "document_text": "\n\n".join([c.text for c in text_chunks if hasattr(c, 'text')]),
                        "format_instructions": mind_format_instructions,
                    })
                    mind_json = mind_result.dict()
                    logger.info("MINDMAP generation complete for %s", document_id)

                    # FLASHCARDS
                    flash_parser = PydanticOutputParser(pydantic_object=FlashcardList)
                    flash_format_instructions = flash_parser.get_format_instructions()
                    flash_template_str = (
                        "Generate a list of concise flashcards (term + definition) from the following document text. Output must conform to the FlashcardList model.\n\n{format_instructions}\n\nDocument Text:\n{document_text}"
                    )
                    flash_chain = PromptTemplate(template=flash_template_str, input_variables=["document_text", "format_instructions"]) | llm | flash_parser
                    logger.info("Generating FLASHCARDS for %s", document_id)
                    flash_result = flash_chain.invoke({
                        "document_text": "\n\n".join([c.text for c in text_chunks if hasattr(c, 'text')]),
                        "format_instructions": flash_format_instructions,
                    })
                    flash_json = flash_result.dict()
                    logger.info("FLASHCARDS generation complete for %s", document_id)

                # Insert generated contents
                generated_items = [
                    (ContentTypeEnum.SUMMARY.value, summary_json),
                    (ContentTypeEnum.MINDMAP.value, mind_json),
                    (ContentTypeEnum.FLASHCARDS.value, flash_json),
                ]

                logger.info("Inserting %d generated items for %s", len(generated_items), document_id)
                for ctype, data in generated_items:
                    gen_doc = {
                        "document_id": document_id,
                        "user_id": user_id,
                        "content_type": ctype,
                        "content_data": data,
                        "created_at": datetime.utcnow(),
                    }
                    await gen_collection.insert_one(gen_doc)
                logger.info("Inserted generated content for %s", document_id)

                # Prepare texts and metadatas for LangChain indexing from the raw text chunks
                texts = []
                metadatas = []
                for chunk in text_chunks:
                    # text_chunks are TextChunk objects with .text, .page_number, .source
                    chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
                    if not chunk_text or not chunk_text.strip():
                        continue
                    texts.append(chunk_text)
                    metadatas.append({
                        "document_id": document_id,
                        "user_id": user_id,
                        "page_number": chunk.page_number if hasattr(chunk, 'page_number') else None,
                        "source": chunk.source if hasattr(chunk, 'source') else "TEXT",
                    })

                # Call LangChain indexing (best-effort)
                try:
                    logger.info("Starting LangChain indexing for %s: %d chunks", document_id, len(texts))
                    await create_langchain_indexes(texts=texts, metadatas=metadatas)
                    logger.info("LangChain indexing completed for %s", document_id)
                except Exception as idx_err:
                    logger.exception("LangChain indexing failed for %s: %s", document_id, idx_err)

                # If we reach here, success
                logger.info("Processing completed successfully for %s. Marking COMPLETED", document_id)
                try:
                    res = await docs_collection.update_one({"_id": document_id}, {"$set": {"processing_status": ProcessingStatusEnum.COMPLETED.value}})
                    logger.info("Update result for COMPLETED: %s", getattr(res, 'matched_count', res))
                    try:
                        stored = await docs_collection.find_one({"_id": document_id})
                        logger.info("Stored document after COMPLETED update: %s", stored)
                    except Exception as e:
                        logger.exception("Failed to read back document %s after COMPLETED update: %s", document_id, e)
                except Exception as e:
                    logger.exception("Failed to update document %s to COMPLETED: %s", document_id, e)
                return

            except Exception as e:
                logger.exception("Processing attempt %d failed for %s: %s", attempt + 1, document_id, e)
                attempt += 1
                if attempt >= max_retries:
                    logger.error("All processing attempts failed for %s. Marking FAILED", document_id)
                    try:
                        res = await docs_collection.update_one({"_id": document_id}, {"$set": {"processing_status": ProcessingStatusEnum.FAILED.value}})
                        logger.info("Update result for FAILED: %s", getattr(res, 'matched_count', res))
                        try:
                            stored = await docs_collection.find_one({"_id": document_id})
                            logger.info("Stored document after FAILED update: %s", stored)
                        except Exception as e:
                            logger.exception("Failed to read back document %s after FAILED update: %s", document_id, e)
                    except Exception as e:
                        logger.exception("Failed to update document %s to FAILED: %s", document_id, e)
                    return
                else:
                    logger.info("Retrying processing for %s (next attempt %d)", document_id, attempt + 1)
                # otherwise loop to retry

    # Run the async processing function
    return _run_async(_process())

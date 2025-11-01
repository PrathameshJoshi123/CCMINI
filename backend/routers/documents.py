from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import logging
from backend.utils.security import get_current_user
from backend.models.user import UserInDB
from backend.models.document import DocumentInDB, ProcessingStatusEnum, ContentTypeEnum
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.models.document import GeneratedContentInDB, Summary, MindMapNode, FlashcardList
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_mistralai.chat_models import ChatMistralAI
from backend.utils.search import create_langchain_indexes
from backend.database import db
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from celery_worker import process_document as process_document_task
import boto3
import os
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file  

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UploadRequest(BaseModel):
    filename: str


def _transform_mindmap_to_graph(node: Dict[str, Any], parent_id: str | None = None, counter: List[int] = None) -> tuple[List[Dict], List[Dict]]:
    """
    Convert nested MindMapNode tree structure to flat nodes/edges graph structure.
    
    Args:
        node: Dictionary representing a MindMapNode with 'topic' and 'children' keys
        parent_id: ID of the parent node (None for root)
        counter: Mutable list holding the current node ID counter
    
    Returns:
        Tuple of (nodes_list, edges_list)
    """
    if counter is None:
        counter = [0]
    
    nodes = []
    edges = []
    
    # Create current node
    current_id = f"node_{counter[0]}"
    counter[0] += 1
    
    node_obj = {
        "id": current_id,
        "label": node.get("topic", ""),
        "level": 0,  # Will be calculated based on depth
    }
    
    if parent_id:
        node_obj["parent"] = parent_id
        # Create edge from parent to current
        edges.append({
            "from": parent_id,
            "to": current_id
        })
    
    nodes.append(node_obj)
    
    # Recursively process children
    children = node.get("children", [])
    for child in children:
        child_nodes, child_edges = _transform_mindmap_to_graph(child, current_id, counter)
        nodes.extend(child_nodes)
        edges.extend(child_edges)
    
    return nodes, edges


async def process_document(document_id: str, user_id: str):
    """Background task: extract text, create placeholder generated content, update status with retries."""
    docs_collection = db.get_collection("documents")
    gen_collection = db.get_collection("generated_content")

    # Mark as processing
    await docs_collection.update_one({"_id": document_id}, {"$set": {"processing_status": ProcessingStatusEnum.PROCESSING.value}})

    max_retries = 3
    attempt = 0
    while attempt < max_retries:
        try:
            # Fetch document to get s3_key
            doc = await docs_collection.find_one({"_id": document_id})
            if not doc:
                raise RuntimeError("Document not found")

            s3_key = doc.get("s3_key")
            text = extract_text_from_pdf(s3_key)  # This will be updated to handle S3

            # Use ChatMistralAI to generate structured content
            llm = ChatMistralAI(model="mistral-large-latest", temperature=0)

            # SUMMARY
            summary_parser = PydanticOutputParser(pydantic_object=Summary)
            summary_format_instructions = summary_parser.get_format_instructions()
            summary_template_str = """
            You are an expert tutor and technical writer. Create a comprehensive, well-structured summary of the document.
            
            Your summary MUST include:
            1. **Overview**: A 2-3 sentence introduction of the document's main purpose
            2. **Key Points**: Bullet points of the most important concepts (use markdown formatting)
            3. **Detailed Breakdown**: Organize main topics with subheadings (use ## and ###)
            4. **Key Takeaways**: 3-5 actionable insights or conclusions
            
            Format your response in proper markdown with:
            - Headers (##, ###)
            - Bold text for emphasis (**text**)
            - Bullet points (-)
            - Numbered lists where appropriate
            - Code blocks if technical content is present (```language```)
            
            Make it comprehensive yet readable. Focus on clarity and organization.
            
            {format_instructions}

            Document Text:
            {document_text}
            """.strip()
            summary_chain = PromptTemplate(template=summary_template_str, input_variables=["document_text", "format_instructions"]) | llm | summary_parser
            summary_result = summary_chain.invoke({
                "document_text": "\n\n".join([c.text for c in text if hasattr(c, 'text')]),
                "format_instructions": summary_format_instructions,
            })
            summary_json = summary_result.dict()

            # MINDMAP
            mind_parser = PydanticOutputParser(pydantic_object=MindMapNode)
            mind_format_instructions = mind_parser.get_format_instructions()
            mind_template_str = """
            Create a comprehensive, well-structured hierarchical mind map of the document's content.
            
            Structure Requirements:
            1. **Root Node**: Main topic/theme of the entire document
            2. **Level 1 Children**: 4-7 major themes or sections
            3. **Level 2+ Children**: Key concepts, sub-topics, and details under each major theme
            
            Guidelines:
            - Make the hierarchy meaningful and logical
            - Use clear, concise labels (2-8 words per node)
            - Go 2-4 levels deep where appropriate
            - Balance the tree - don't make one branch too deep while others are shallow
            - Include important terms, concepts, formulas, and processes
            
            The output must conform to the MindMapNode Pydantic model with nested children.

            {format_instructions}

            Document Text:
            {document_text}
            """.strip()
            mind_chain = PromptTemplate(template=mind_template_str, input_variables=["document_text", "format_instructions"]) | llm | mind_parser
            mind_result = mind_chain.invoke({
                "document_text": "\n\n".join([c.text for c in text if hasattr(c, 'text')]),
                "format_instructions": mind_format_instructions,
            })
            mind_json = mind_result.dict()

            # FLASHCARDS
            flash_parser = PydanticOutputParser(pydantic_object=FlashcardList)
            flash_format_instructions = flash_parser.get_format_instructions()
            flash_template_str = """
            Generate comprehensive flashcards from the document to help students learn key concepts.
            
            For each flashcard:
            - **Term**: Create clear, focused questions that test understanding
            - **Definition**: Provide detailed, well-explained answers with examples where helpful
            
            Use markdown formatting in both questions and answers:
            - Bold important terms (**text**)
            - Use bullet points for multi-part answers (-)
            - Include code snippets if relevant (```language```)
            - Use numbered steps for processes (1., 2., etc.)
            
            Create 8-15 flashcards covering the most important concepts, formulas, definitions, and processes.
            Make them educational and easy to understand.

            {format_instructions}

            Document Text:
            {document_text}
            """.strip()
            flash_chain = PromptTemplate(template=flash_template_str, input_variables=["document_text", "format_instructions"]) | llm | flash_parser
            flash_result = flash_chain.invoke({
                "document_text": "\n\n".join([c.text for c in text if hasattr(c, 'text')]),
                "format_instructions": flash_format_instructions,
            })
            flash_json = flash_result.dict()

            # Insert generated contents
            generated_items = [
                (ContentTypeEnum.SUMMARY.value, summary_json),
                (ContentTypeEnum.MINDMAP.value, mind_json),
                (ContentTypeEnum.FLASHCARDS.value, flash_json),
            ]

            for ctype, data in generated_items:
                gen_doc = {
                    "document_id": document_id,
                    "user_id": user_id,
                    "content_type": ctype,
                    "content_data": data,
                    "created_at": datetime.utcnow(),
                }
                await gen_collection.insert_one(gen_doc)

            # Prepare texts and metadatas for LangChain indexing
            # Fetch paragraph-level/generated content for this document
            cursor = gen_collection.find({"document_id": document_id})
            texts = []
            metadatas = []
            async for item in cursor:
                txt = item.get("content_data", {}).get("content", "")
                texts.append(txt)
                metadatas.append({
                    "document_id": document_id,
                    "user_id": user_id,
                    "page_number": item.get("page_number"),
                    "source": item.get("content_type"),
                    "generated_id": str(item.get("_id")),
                })

            # Call LangChain indexing (best-effort)
            try:
                await create_langchain_indexes(texts=texts, metadatas=metadatas)
            except Exception as idx_err:
                # Log and continue; indexing failures shouldn't mark document failed
                import logging
                logging.exception("LangChain indexing failed for %s: %s", document_id, idx_err)

            # If we reach here, success
            await docs_collection.update_one({"_id": document_id}, {"$set": {"processing_status": ProcessingStatusEnum.COMPLETED.value}})
            return

        except Exception:
            attempt += 1
            if attempt >= max_retries:
                await docs_collection.update_one({"_id": document_id}, {"$set": {"processing_status": ProcessingStatusEnum.FAILED.value}})
                return
            # otherwise loop to retry


# @router.post("/documents/upload")
# async def upload_document(request: UploadRequest, current_user: UserInDB = Depends(get_current_user)):
#     """
#     Generate a presigned URL for direct S3 upload.
#     Frontend will use this URL to upload the file directly to S3.
#     """
#     user_id = str(current_user.get("_id") or current_user.get("id"))
    
#     # Generate unique S3 key
#     file_ext = Path(request.filename).suffix or ".pdf"
#     unique_name = f"{uuid.uuid4().hex}{file_ext}"
#     s3_key = f"{user_id}/{unique_name}"
    
#     # Create document record with UPLOADING status
#     docs_collection = db.get_collection("documents")
#     document = {
#         "user_id": user_id,
#         "original_filename": request.filename,
#         "s3_key": s3_key,
#         "processing_status": ProcessingStatusEnum.UPLOADING.value,
#         "uploaded_at": datetime.utcnow(),
#     }

#     result = await docs_collection.insert_one(document)
#     document_id = str(result.inserted_id)
    
#     # Generate presigned URL for S3 upload
#     try:
#         s3_client = boto3.client(
#             's3',
#             region_name=os.getenv('AWS_REGION'),
#             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
#         )
        
#         bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
#         if not bucket_name:
#             raise HTTPException(status_code=500, detail="S3 bucket name not configured")
        
#         presigned_url = s3_client.generate_presigned_url(
#             'put_object',
#             Params={'Bucket': bucket_name, 'Key': s3_key, 'ContentType': 'application/pdf'},
#             ExpiresIn=3600  # 1 hour
#         )
        
#         logger.info("Generated presigned URL for document %s with S3 key %s", document_id, s3_key)
        
#         return {
#             "message": "Upload URL generated successfully",
#             "document_id": document_id,
#             "presigned_url": presigned_url,
#             "s3_key": s3_key,
#             "status": ProcessingStatusEnum.UPLOADING.value
#         }
        
#     except Exception as e:
#         # Update status to FAILED if presigned URL generation fails
#         await docs_collection.update_one(
#             {"_id": result.inserted_id}, 
#             {"$set": {"processing_status": ProcessingStatusEnum.FAILED.value}}
#         )
#         logger.exception("Failed to generate presigned URL for document %s: %s", document_id, e)
#         raise HTTPException(status_code=500, detail="Failed to generate upload URL")


@router.post("/documents/upload")
async def upload_document_legacy(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    """
    LEGACY ENDPOINT: Direct file upload to S3 (temporary backward compatibility).
    This endpoint accepts multipart file uploads and handles the S3 upload server-side.
    
    NOTE: This is a temporary compatibility endpoint. Please migrate to the presigned URL flow:
    1. Call POST /documents/upload with JSON {filename}
    2. Upload to the returned presigned_url
    3. Call POST /documents/{document_id}/start-processing
    """
    user_id = str(current_user.get("_id") or current_user.get("id"))
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Generate unique S3 key
    file_ext = Path(file.filename).suffix or ".pdf"
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    s3_key = f"{user_id}/{unique_name}"
    
    # Create document record
    docs_collection = db.get_collection("documents")
    document = {
        "user_id": user_id,
        "original_filename": file.filename,
        "s3_key": s3_key,
        "processing_status": ProcessingStatusEnum.UPLOADING.value,
        "uploaded_at": datetime.utcnow(),
    }

    result = await docs_collection.insert_one(document)
    document_id = str(result.inserted_id)
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload directly to S3
        s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        
        bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        if not bucket_name:
            raise HTTPException(status_code=500, detail="S3 bucket name not configured")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType='application/pdf'
        )
        
        logger.info("Uploaded file directly to S3: %s", s3_key)
        
        # Start processing immediately
        try:
            process_document_task.delay(document_id, user_id)
            # Update status to PROCESSING
            await docs_collection.update_one(
                {"_id": document_id}, 
                {"$set": {"processing_status": ProcessingStatusEnum.PROCESSING.value}}
            )
            processing_status = ProcessingStatusEnum.PROCESSING.value
        except Exception as e:
            logger.exception("Failed to start processing for %s: %s", document_id, e)
            processing_status = ProcessingStatusEnum.UPLOADING.value
        
        return {
            "message": "File uploaded and processing started",
            "document_id": document_id,
            "filename": file.filename,
            "status": processing_status,
            "note": "This endpoint is deprecated. Please migrate to the presigned URL flow."
        }
        
    except Exception as e:
        # Update status to FAILED
        await docs_collection.update_one(
            {"_id": result.inserted_id}, 
            {"$set": {"processing_status": ProcessingStatusEnum.FAILED.value}}
        )
        logger.exception("Failed to upload file for document %s: %s", document_id, e)
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")


@router.post("/documents/{document_id}/start-processing")
async def start_processing(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Start processing a document after it has been uploaded to S3.
    Frontend should call this after successfully uploading the file using the presigned URL.
    """
    docs_collection = db.get_collection("documents")
    user_id = str(current_user.get("_id") or current_user.get("id"))
    
    # Verify document ownership and that it's in UPLOADING status
    doc = await docs_collection.find_one({"_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if str(doc.get("user_id")) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.get("processing_status") != ProcessingStatusEnum.UPLOADING.value:
        raise HTTPException(status_code=400, detail=f"Document is not in uploadable state. Current status: {doc.get('processing_status')}")
    
    # Schedule background processing via Celery
    try:
        logger.info("Enqueuing Celery task for document %s", document_id)
        process_document_task.delay(document_id, user_id)
        
        # Update status to PROCESSING
        await docs_collection.update_one(
            {"_id": document_id}, 
            {"$set": {"processing_status": ProcessingStatusEnum.PROCESSING.value}}
        )
        
        return {
            "message": "Document processing started",
            "document_id": document_id,
            "status": ProcessingStatusEnum.PROCESSING.value
        }
        
    except Exception as e:
        logger.exception("Failed to enqueue Celery task for %s: %s", document_id, e)
        # Update status to FAILED
        await docs_collection.update_one(
            {"_id": document_id}, 
            {"$set": {"processing_status": ProcessingStatusEnum.FAILED.value}}
        )
        raise HTTPException(status_code=500, detail="Failed to start document processing")


@router.get("/documents", response_model=List[DocumentInDB])
async def get_documents(current_user: UserInDB = Depends(get_current_user)):
    """
    Get all documents for the authenticated user.
    Handles backward compatibility for documents with local_path vs s3_key.
    """
    docs_collection = db.get_collection("documents")
    user_id = str(current_user.get("_id") or current_user.get("id"))
    
    # Query documents for current user
    cursor = docs_collection.find({"user_id": user_id})
    documents = []
    async for d in cursor:
        # Convert _id to string
        d["_id"] = str(d["_id"])
        
        # Handle backward compatibility: migrate local_path to s3_key if needed
        if "local_path" in d and "s3_key" not in d:
            # For old documents, use the local_path as a placeholder s3_key
            # In a real migration, you'd want to upload these files to S3
            d["s3_key"] = f"migrated/{Path(d['local_path']).name}"
            # Remove the old field for clean response
            del d["local_path"]
        
        documents.append(d)
    
    return documents


@router.get("/documents/{document_id}/generated")
async def get_generated_content(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Get all generated content for a specific document with data transformation.
    Transforms flashcards (term/definition -> question/answer) and mindmaps (tree -> graph).
    """
    docs_collection = db.get_collection("documents")
    gen_collection = db.get_collection("generated_content")
    user_id = str(current_user.get("_id") or current_user.get("id"))
    
    # Security check: verify document ownership
    try:
        doc = await docs_collection.find_one({"_id": document_id})
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if str(doc.get("user_id")) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Fetch generated content
    cursor = gen_collection.find({"document_id": document_id})
    generated_items = []
    async for it in cursor:
        generated_items.append(it)
    
    # Transform data based on content_type
    transformed_items = []
    for item in generated_items:
        transformed_item = {
            "_id": str(item["_id"]),
            "document_id": item["document_id"],
            "user_id": item["user_id"],
            "content_type": item["content_type"],
            "created_at": item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"]),
        }
        
        content_data = item.get("content_data", {})
        
        # Transform based on content type
        if item["content_type"] == ContentTypeEnum.FLASHCARDS.value:
            # Transform flashcards: term/definition -> question/answer
            flashcards_list = content_data.get("flashcards", [])
            transformed_flashcards = [
                {
                    "question": card.get("term", ""),
                    "answer": card.get("definition", "")
                }
                for card in flashcards_list
            ]
            transformed_item["content_data"] = {"flashcards": transformed_flashcards}
            
        elif item["content_type"] == ContentTypeEnum.MINDMAP.value:
            # Transform mindmap: nested tree -> flat nodes/edges graph
            nodes, edges = _transform_mindmap_to_graph(content_data)
            transformed_item["content_data"] = {
                "nodes": nodes,
                "edges": edges
            }
            
        else:
            # Summary or other types: no transformation needed
            transformed_item["content_data"] = content_data
        
        transformed_items.append(transformed_item)
    
    return transformed_items

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.utils.security import get_current_user
from backend.models.user import UserInDB
from backend.utils.search import create_langchain_indexes
from backend.database import db
import inspect

# Prefer the newer langchain_huggingface package when available, fall back to community wrapper
try:
    from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore
except Exception:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
    except Exception:
        HuggingFaceEmbeddings = None
from langchain.prompts import PromptTemplate
from elasticsearch import Elasticsearch
try:
    # newer package
    from langchain_elasticsearch import ElasticsearchStore  # type: ignore
except Exception:
    try:
        from langchain_community.vectorstores import ElasticsearchStore  # type: ignore
    except Exception:
        ElasticsearchStore = None
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/debug/elasticsearch")
async def debug_elasticsearch(current_user: UserInDB = Depends(get_current_user)):
    """Debug endpoint to inspect Elasticsearch index structure and sample documents."""
    es = Elasticsearch(hosts=["http://localhost:9200"])
    
    try:
        # Get index mapping
        mapping = es.indices.get_mapping(index="pdf_chunks")
        
        # Get a few sample documents
        sample_resp = es.search(index="pdf_chunks", body={
            "query": {"match_all": {}},
            "size": 3
        })
        
        # Get index stats
        stats = es.indices.stats(index="pdf_chunks")
        doc_count = stats.get("indices", {}).get("pdf_chunks", {}).get("total", {}).get("docs", {}).get("count", 0)
        
        return {
            "index_exists": True,
            "document_count": doc_count,
            "mapping": mapping,
            "sample_documents": sample_resp.get("hits", {}).get("hits", [])
        }
    except Exception as e:
        return {
            "index_exists": False,
            "error": str(e),
            "document_count": 0,
            "mapping": None,
            "sample_documents": []
        }


class ChatRequest(BaseModel):
    query: str
    document_ids: List[str]


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


# Prompt template (system + user) - Enhanced for better responses
SYSTEM_PROMPT = (
    "You are an expert tutor with deep knowledge across multiple domains. Your role is to provide clear, accurate, "
    "and well-structured explanations that help students understand complex concepts. "
    "You format responses in clean, simple markdown that renders properly in web applications. "
    "You cite all sources meticulously and focus on educational value. "
    "You are helpful, patient, and avoid complex formatting that might break in frontend rendering."
)

USER_TEMPLATE = """CONTEXT:
{context}

QUESTION:
{question}

INSTRUCTIONS:
Format your answer using **clean markdown** for clarity:

1. **Direct Answer**: Start with a clear, concise answer (2-3 sentences)

2. **Detailed Explanation**: Expand with structured content:
   - Use **bold** for key terms and concepts
   - Use bullet points (-) or numbered lists for steps/multiple items
   - Use `code blocks` for technical terms, formulas, or code
   - Use > blockquotes for important notes or definitions

3. **Examples** (if relevant): Provide a concrete example to illustrate the concept

4. **Citations**: When referencing information from the context, cite it as: *[Source: filename.pdf, Page X]*

5. **Key Takeaways**: End with 2-3 bullet points summarizing the most important points

CRITICAL FORMATTING RULES:
- Do NOT use horizontal rules (---) 
- Do NOT use HTML-style comments or tags
- Do NOT use complex nested markdown structures
- Keep headers simple: use ## and ### only
- Ensure proper spacing between sections
- Use ONLY information from the provided CONTEXT
- If the CONTEXT doesn't contain enough information, respond: "I don't have enough information in the provided documents to fully answer that question."
- ALWAYS cite sources using the exact format: *[Source: DocumentName, Page X]*
"""


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: UserInDB = Depends(get_current_user)):
    # Initialize embeddings for semantic search
    if HuggingFaceEmbeddings is None:
        embeddings = None
    else:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Check if index exists
    es = Elasticsearch(hosts=["http://localhost:9200"])
    try:
        exists = es.indices.exists(index="pdf_chunks")
    except Exception:
        exists = False

    if not exists:
        logger.info("Elasticsearch index 'pdf_chunks' does not exist; returning early")
        return ChatResponse(answer="No documents have been indexed yet. Upload PDFs to index them before querying.", sources=[])

    user_id = str(current_user.get("_id") or current_user.get("id"))
    
    # HYBRID SEARCH: Combine semantic (vector) + keyword (BM25) search
    # Use Elasticsearch's native script_score for hybrid scoring
    semantic_results = []
    keyword_results = []
    
    # 1. Semantic search via vector similarity - try both 'vector' and 'embedding' fields,
    # and try nested 'metadata' filters or top-level fields as a fallback.
    if embeddings is not None:
        try:
            query_embedding = embeddings.embed_query(request.query)

            def _run_vector_search(field_name: str, use_metadata: bool):
                # Build base script_score query referencing either nested metadata or top-level fields
                # NOTE: metadata fields are stored as text with .keyword subfields, so use .keyword for exact matches
                user_filter = {"term": {"metadata.user_id.keyword": user_id}} if use_metadata else {"term": {"user_id": user_id}}
                doc_filter = {"terms": {"metadata.document_id.keyword": request.document_ids}} if (use_metadata and request.document_ids) else ({"terms": {"document_id": request.document_ids}} if request.document_ids else None)

                bool_filters = [user_filter]
                if doc_filter is not None:
                    bool_filters.append(doc_filter)

                vector_query = {
                    "script_score": {
                        "query": {
                            "bool": {
                                "filter": bool_filters
                            }
                        },
                        "script": {
                            "source": f"cosineSimilarity(params.query_vector, '{field_name}') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                }
                return es.search(index="pdf_chunks", body={"query": vector_query, "size": 10})

            # Try nested metadata + 'vector' first
            try:
                vector_resp = _run_vector_search('vector', True)
                semantic_results = vector_resp.get("hits", {}).get("hits", [])
            except Exception:
                # fallback: try nested metadata + 'embedding'
                try:
                    vector_resp = _run_vector_search('embedding', True)
                    semantic_results = vector_resp.get("hits", {}).get("hits", [])
                except Exception:
                    # fallback: try top-level 'vector' with top-level user_id/document_id
                    try:
                        vector_resp = _run_vector_search('vector', False)
                        semantic_results = vector_resp.get("hits", {}).get("hits", [])
                    except Exception:
                        try:
                            vector_resp = _run_vector_search('embedding', False)
                            semantic_results = vector_resp.get("hits", {}).get("hits", [])
                        except Exception as e:
                            logger.exception("Semantic search failed (all fallbacks): %s", e)

            logger.info("Semantic search returned %d results", len(semantic_results))
        except Exception as e:
            logger.exception("Semantic search failed: %s", e)
    
    # 2. Keyword search via BM25
    try:
        # Primary: nested metadata filters (use .keyword for exact match on text fields)
        keyword_query = {
            "bool": {
                "must": [
                    {"multi_match": {
                        "query": request.query,
                        "fields": ["text^2", "text.shingles"],
                        "type": "best_fields"
                    }}
                ],
                "filter": [
                    {"term": {"metadata.user_id.keyword": user_id}}
                ]
            }
        }

        if request.document_ids:
            keyword_query["bool"]["filter"].append({"terms": {"metadata.document_id.keyword": request.document_ids}})

        keyword_resp = es.search(index="pdf_chunks", body={"query": keyword_query, "size": 10})
        keyword_results = keyword_resp.get("hits", {}).get("hits", [])

        # If nothing returned, try top-level user_id/document_id fields as a fallback
        if not keyword_results:
            fallback_keyword_query = {
                "bool": {
                    "must": [
                        {"multi_match": {
                            "query": request.query,
                            "fields": ["text^2", "text.shingles"],
                            "type": "best_fields"
                        }}
                    ],
                    "filter": [
                        {"term": {"user_id": user_id}}
                    ]
                }
            }
            if request.document_ids:
                fallback_keyword_query["bool"]["filter"].append({"terms": {"document_id": request.document_ids}})
            try:
                keyword_resp = es.search(index="pdf_chunks", body={"query": fallback_keyword_query, "size": 10})
                keyword_results = keyword_resp.get("hits", {}).get("hits", [])
            except Exception:
                # keep original empty results
                pass

        logger.info("Keyword search returned %d results", len(keyword_results))
    except Exception as e:
        logger.exception("Keyword search failed: %s", e)
    
    # 3. Merge and re-rank results using Reciprocal Rank Fusion (RRF)
    def rrf_score(rank, k=60):
        return 1.0 / (k + rank)
    
    doc_scores = {}
    doc_hits = {}
    
    for rank, hit in enumerate(semantic_results, start=1):
        doc_id = hit.get("_id")
        doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score(rank) * 0.6  # 60% weight for semantic
        doc_hits[doc_id] = hit
    
    for rank, hit in enumerate(keyword_results, start=1):
        doc_id = hit.get("_id")
        doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score(rank) * 0.4  # 40% weight for keyword
        if doc_id not in doc_hits:
            doc_hits[doc_id] = hit
    
    # Sort by combined score and take top results
    sorted_doc_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
    
    # Convert to standard format
    class _Hit:
        def __init__(self, src, score=None):
            self.page_content = src.get("text") or src.get("content") or ""
            # LangChain stores metadata as nested object
            self.metadata = src.get("metadata", {})
            self.score = score
    
    results = []
    for doc_id in sorted_doc_ids[:10]:
        hit = doc_hits[doc_id]
        src = hit.get("_source", {})
        score = doc_scores[doc_id]
        results.append(_Hit(src, score))
    
    # Log hybrid search results
    logger.info("Hybrid search (RRF) returned %d merged results", len(results))
    # Log hybrid search results
    logger.info("Hybrid search (RRF) returned %d merged results", len(results))
    for i, hit in enumerate(results[:20]):
        md = hit.metadata if hasattr(hit, "metadata") else {}
        src = md.get("document_id") or md.get("source") or md.get("document_id_str")
        page = md.get("page_number") or md.get("page") or md.get("page_num")
        score = getattr(hit, "score", None)
        content = (hit.page_content or "")[:400].replace('\n', ' ')
        logger.info("hybrid_chunk[%d] src=%s page=%s score=%.4f preview=%s", i, str(src), str(page), score if score else 0.0, content)

    # Deduplicate by content
    seen = set()
    filtered = []
    for d in results:
        text = d.page_content if hasattr(d, "page_content") else getattr(d, "content", "")
        if not text or text in seen:
            continue
        seen.add(text)
        filtered.append(d)

    # Build context string from top N chunks with document names
    top_chunks = filtered[:6]
    context_parts = []
    sources = []
    
    # Fetch document information to get names
    docs_collection = db.get_collection("documents")
    doc_cache = {}
    
    for idx, d in enumerate(top_chunks, start=1):
        text = d.page_content if hasattr(d, "page_content") else getattr(d, "content", "")
        meta = d.metadata if hasattr(d, "metadata") else {}
        # LangChain stores metadata as-is, so we can access page_number directly
        doc_id = meta.get("document_id") or meta.get("document_id_str") or meta.get("source")
        page_num = meta.get("page_number") or meta.get("page") or meta.get("page_num")
        
        # Fetch document name from database if not cached
        doc_name = "Unknown Document"
        if doc_id:
            if doc_id not in doc_cache:
                try:
                    doc = await docs_collection.find_one({"_id": doc_id})
                    if doc:
                        doc_cache[doc_id] = doc.get("original_filename", "Unknown Document")
                    else:
                        doc_cache[doc_id] = "Unknown Document"
                except Exception:
                    doc_cache[doc_id] = "Unknown Document"
            doc_name = doc_cache.get(doc_id, "Unknown Document")
        
        source_entry = {
            "document_id": doc_id,
            "page": page_num,
            "score": getattr(d, "score", None) or meta.get("score"),
        }
        sources.append(source_entry)
        # Include document name in context for better citations
        context_parts.append(f"[Source: {doc_name}, Page {page_num}]\n{text}")
    
    # Log what we're sending to help debug
    logger.info(f"Context includes {len(context_parts)} chunks from documents: {list(set(doc_cache.values()))}")

    context = "\n\n".join(context_parts)

    # Build prompt
    user_prompt = PromptTemplate(template=USER_TEMPLATE, input_variables=["context", "question"]) .format(context=context, question=request.query)

    # Try to call Mistral via langchain_mistralai if available
    try:
        from langchain_mistralai.chat_models import ChatMistralAI
        from langchain.schema import SystemMessage, HumanMessage

        chat = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.3,
            max_tokens=2048
        )
        # LangChain chat.generate expects a batch: list[list[BaseMessage]]
        messages = [[SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]]
        try:
            resp = chat.generate(messages)
            # extract text from generations if available
            try:
                raw_text = resp.generations[0][0].text
            except Exception:
                raw_text = str(resp)

            # Prefer structured JSON output from the model to enforce grounding
            import json
            answer_text = None
            try:
                parsed = json.loads(raw_text)
                # Expecting {"answer": "...", "sources": [{"document_id": "id", "page": n}...]}
                if isinstance(parsed, dict) and parsed.get("answer"):
                    answer_text = parsed.get("answer")
                    # normalize sources to expected shape
                    sources = parsed.get("sources") if parsed.get("sources") else []
                else:
                    answer_text = raw_text
            except Exception:
                # not JSON, keep raw text and we'll validate later
                answer_text = raw_text
        except Exception as gen_err:
            logger.exception("ChatMistralAI.generate failed: %s", gen_err)
            # try a simpler call pattern
            try:
                answer_text = chat(user_prompt)
                if not isinstance(answer_text, str):
                    answer_text = str(answer_text)
            except Exception as call_err:
                logger.exception("ChatMistralAI call fallback failed: %s", call_err)
                answer_text = None

    except Exception as e:
        logger.exception("Mistral model unavailable or failed to initialize: %s", e)
        answer_text = None

    # Post-process & validation: if answer_text was produced, ensure it's grounded in retrieved sources.
    def _extractive_fallback():
        if context_parts:
            out = "\n\n".join([p.split("\n")[0] for p in context_parts[:2]])
            return "Based on the retrieved documents:\n" + out
        return "I don't have enough information in the provided documents to answer that."

    # If the model returned structured sources, validate they exist in our retrieved set
    try:
        # normalize sources if not already
        validated_sources = []
        if isinstance(sources, list) and sources:
            # Build a quick set of doc ids we retrieved
            retrieved_doc_ids = {str(d.metadata.get("document_id") or d.metadata.get("document_id_str") or d.metadata.get("source")) for d in results}
            for s in sources:
                sid = str(s.get("document_id")) if isinstance(s, dict) else str(s)
                if sid in retrieved_doc_ids:
                    validated_sources.append(s)

        # If the model gave an answer and validated_sources is non-empty (or the model explicitly says no answer), accept it
        if answer_text:
            # If model returned sources but none validated, fall back to extractive
            if isinstance(sources, list) and sources and not validated_sources:
                logger.warning("Model returned sources but none matched retrieved docs; using extractive fallback")
                answer_text = _extractive_fallback()
                sources = []
            else:
                sources = validated_sources if validated_sources else sources if isinstance(sources, list) else []
        else:
            # no answer generated; fallback
            answer_text = _extractive_fallback()
            sources = []
    except Exception as verify_err:
        logger.exception("Error validating model output: %s", verify_err)
        answer_text = _extractive_fallback()
        sources = []

    return ChatResponse(answer=answer_text, sources=sources)

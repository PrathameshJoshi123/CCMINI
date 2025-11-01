from elasticsearch import Elasticsearch, exceptions
from typing import Dict, Any
import logging
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


logger = logging.getLogger(__name__)


class ElasticsearchClient:
    def __init__(self, host: str = "http://localhost:9200"):
        # Create client; in production you may want to read hosts and credentials from env
        logger.info("Initializing Elasticsearch client for host=%s", host)
        self.client = Elasticsearch(hosts=[host])

    def default_mapping(self) -> Dict[str, Any]:
        # Optimized mapping for hybrid search (semantic + keyword)
        # - text: main content field with english analyzer + shingle subfield for phrase matching
        # - embedding: dense_vector for semantic search
        # - metadata fields: page_number, source, document_id, user_id as keywords for filtering
        return {
            "mappings": {
                "properties": {
                    "text": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256},
                            "shingles": {
                                "type": "text",
                                "analyzer": "english_shingle"
                            }
                        }
                    },
                    "page_number": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    # Some LangChain versions store vectors under 'embedding', others under 'vector'.
                    # Keep both for compatibility so queries can reference either field.
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "vector": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine"
                    },
                    # Also include a nested 'metadata' object since some LangChain stores metadata there.
                    "metadata": {
                        "properties": {
                            "page_number": {"type": "integer"},
                            "source": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "user_id": {"type": "keyword"}
                        }
                    }
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "english_shingle": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "english_stop", "shingle"]
                        }
                    },
                    "filter": {
                        "english_stop": {
                            "type": "stop",
                            "stopwords": "_english_"
                        },
                        "shingle": {
                            "type": "shingle",
                            "min_shingle_size": 2,
                            "max_shingle_size": 3
                        }
                    }
                }
            }
        }

    def create_index_if_not_exists(self, index_name: str, mapping: Dict[str, Any] | None = None):
        try:
            exists = self.client.indices.exists(index=index_name)
            logger.info("Index exists check for %s: %s", index_name, exists)
            if exists:
                logger.debug("Index %s already exists", index_name)
                return

            body = mapping if mapping is not None else self.default_mapping()
            logger.info("Creating index %s with mapping (size=%d bytes approx)", index_name, len(str(body)))
            self.client.indices.create(index=index_name, body=body)
            logger.info("Created index %s", index_name)
        except exceptions.ElasticsearchException as e:
            logger.exception("Error creating index %s: %s", index_name, e)
            raise

    async def create_langchain_indexes(self,
        texts: list[str],
        metadatas: list[dict],
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        es_host: str = "http://localhost:9200",
        es_index_name: str = "pdf_chunks",
    ):
        """Create an Elasticsearch index using LangChain's ElasticsearchStore.

        This function embeds texts using HuggingFaceEmbeddings and indexes them
        into Elasticsearch. It no longer uses a local FAISS index; vectors are
        stored directly in Elasticsearch under the `embedding` dense_vector field.
        """
        if HuggingFaceEmbeddings is None:
            raise RuntimeError("Embeddings not installed. Please install sentence-transformers and langchain.")

        # Initialize embeddings model
        logger.info("Initializing embeddings model: %s", model_name)
        embeddings = HuggingFaceEmbeddings(model_name=model_name)

        # Index into Elasticsearch using LangChain's store. This will embed texts
        # and push vectors into the ES `embedding` field according to the mapping.
        if ElasticsearchStore is not None:
            logger.info("Indexing %d documents into ES index=%s via LangChain ElasticsearchStore", len(texts), es_index_name)
            try:
                # Ensure index exists with correct mapping before LangChain writes
                try:
                    self.create_index_if_not_exists(es_index_name)
                except Exception as ci_err:
                    logger.warning("Could not ensure index exists (%s): %s", es_index_name, ci_err)

                # Different langchain versions expect different kwarg names: index_name or index
                try:
                    ElasticsearchStore.from_texts(
                        texts=texts,
                        embedding=embeddings,
                        metadatas=metadatas,
                        es_url=es_host,
                        index_name=es_index_name,
                    )
                except Exception as e_idxname:
                    logger.info("ElasticsearchStore.from_texts failed with index_name, trying 'index' kwarg: %s", e_idxname)
                    ElasticsearchStore.from_texts(
                        texts=texts,
                        embedding=embeddings,
                        metadatas=metadatas,
                        es_url=es_host,
                        index=es_index_name,
                    )
                logger.info("LangChain indexing to %s completed", es_index_name)
            except Exception as e:
                logger.exception("LangChain ElasticsearchStore.from_texts failed: %s", e)
                raise
        else:
            logger.warning("ElasticsearchStore not available; skipping ES indexing")


async def create_langchain_indexes(
    texts: list[str],
    metadatas: list[dict],
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
    es_host: str = "http://localhost:9200",
    es_index_name: str = "pdf_chunks",
):
    """Module-level wrapper for creating LangChain indexes using Elasticsearch.

    This delegates to the ElasticsearchClient implementation to preserve
    the existing behavior while providing a simple import for other modules.
    """
    client = ElasticsearchClient(host=es_host)
    logger.info("create_langchain_indexes wrapper called: index=%s items=%d", es_index_name, len(texts))
    res = await client.create_langchain_indexes(
        texts=texts,
        metadatas=metadatas,
        model_name=model_name,
        es_host=es_host,
        es_index_name=es_index_name,
    )
    logger.info("create_langchain_indexes wrapper finished: index=%s", es_index_name)
    return res

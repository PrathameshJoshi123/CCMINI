#!/usr/bin/env python3
"""
Debug script to inspect Elasticsearch pdf_chunks index.
Run this to see what's actually stored in the index.
"""

import json
from elasticsearch import Elasticsearch

def main():
    es = Elasticsearch(hosts=["http://localhost:9200"])
    
    print("=== Elasticsearch Debug ===")
    
    try:
        # Check if index exists
        exists = es.indices.exists(index="pdf_chunks")
        print(f"Index 'pdf_chunks' exists: {exists}")
        
        if not exists:
            print("Index doesn't exist. No documents have been indexed yet.")
            return
        
        # Get mapping
        print("\n=== Index Mapping ===")
        mapping = es.indices.get_mapping(index="pdf_chunks")
        # Convert to dict if it's an ObjectApiResponse
        if hasattr(mapping, 'body'):
            mapping = mapping.body
        elif hasattr(mapping, '_body'):
            mapping = mapping._body
        print(json.dumps(dict(mapping), indent=2))
        
        # Get stats
        stats = es.indices.stats(index="pdf_chunks")
        doc_count = stats.get("indices", {}).get("pdf_chunks", {}).get("total", {}).get("docs", {}).get("count", 0)
        print(f"\n=== Document Count: {doc_count} ===")
        
        if doc_count == 0:
            print("No documents found in index.")
            return
        
        # Get sample documents
        print("\n=== Sample Documents ===")
        sample_resp = es.search(index="pdf_chunks", body={
            "query": {"match_all": {}},
            "size": 5
        })
        
        hits = sample_resp.get("hits", {}).get("hits", [])
        for i, hit in enumerate(hits):
            print(f"\n--- Document {i+1} ---")
            source = hit.get("_source", {})
            print(f"ID: {hit.get('_id')}")
            print(f"Score: {hit.get('_score')}")
            
            # Show field structure
            for key, value in source.items():
                if key == "text":
                    # Truncate text for readability
                    text_preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                    print(f"  {key}: {text_preview}")
                elif key in ["vector", "embedding"]:
                    # Show vector info without printing the whole array
                    if isinstance(value, list):
                        print(f"  {key}: [vector with {len(value)} dimensions]")
                    else:
                        print(f"  {key}: {type(value).__name__}")
                else:
                    print(f"  {key}: {value}")
        
        # Test a simple search
        print("\n=== Test Search ===")
        test_resp = es.search(index="pdf_chunks", body={
            "query": {
                "bool": {
                    "must": [{"match": {"text": "the"}}]
                }
            },
            "size": 1
        })
        test_count = test_resp.get("hits", {}).get("total", {}).get("value", 0)
        print(f"Simple text search for 'the': {test_count} results")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
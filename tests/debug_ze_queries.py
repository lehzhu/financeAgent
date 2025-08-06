#!/usr/bin/env python3
"""
Debug ZeroEntropy queries resource - likely used for reranking.
"""

import os
from zeroentropy import ZeroEntropy
import json

# Initialize client
api_key = os.environ.get("ZEROENTROPY_API_KEY", "ze_1UiaUVwAy0tWCB28")
client = ZeroEntropy(api_key=api_key)

print("="*60)
print("ZEROENTROPY QUERIES RESOURCE EXPLORATION")
print("="*60)

# Explore the queries resource
print("\n1. Exploring client.queries methods:")
queries_resource = client.queries
for attr in dir(queries_resource):
    if not attr.startswith('_'):
        print(f"   - queries.{attr}")
        try:
            method = getattr(queries_resource, attr)
            if callable(method) and method.__doc__:
                print(f"     Doc: {method.__doc__[:150]}...")
        except:
            pass

# Test the queries.create method (common pattern for API resources)
print("\n2. Testing queries.create() for reranking:")

test_query = "What is Costco's revenue?"
test_documents = [
    "Costco's revenue in 2024 was $254.5 billion.",
    "The company operates 871 warehouses.",
    "Membership fees totaled $4.8 billion."
]

# Try different parameter combinations
test_params = [
    {
        "query": test_query,
        "documents": test_documents,
        "top_k": 2
    },
    {
        "query": test_query,
        "documents": test_documents,
        "model": "default"
    },
    {
        "text": test_query,
        "documents": test_documents
    },
    {
        "input": test_query,
        "documents": test_documents
    }
]

for i, params in enumerate(test_params, 1):
    print(f"\n   Attempt {i}: {list(params.keys())}")
    try:
        result = client.queries.create(**params)
        print(f"   ✅ SUCCESS! Result type: {type(result)}")
        print(f"   Result: {result}")
        # If successful, show how to access the results
        if hasattr(result, 'results'):
            print(f"   Results: {result.results[:2]}")
        if hasattr(result, 'rankings'):
            print(f"   Rankings: {result.rankings[:2]}")
        break
    except Exception as e:
        error_msg = str(e)
        if "required" in error_msg.lower():
            print(f"   ❌ Missing required parameter: {error_msg[:150]}")
        else:
            print(f"   ❌ Error: {error_msg[:150]}")

# Also check documents resource
print("\n3. Exploring client.documents methods:")
documents_resource = client.documents
for attr in dir(documents_resource):
    if not attr.startswith('_') and not attr.startswith('with_'):
        print(f"   - documents.{attr}")

# Check collections resource
print("\n4. Exploring client.collections methods:")
collections_resource = client.collections
for attr in dir(collections_resource):
    if not attr.startswith('_') and not attr.startswith('with_'):
        print(f"   - collections.{attr}")

# Check models resource
print("\n5. Available models:")
try:
    models_resource = client.models
    # Try to list models
    if hasattr(models_resource, 'list'):
        models = models_resource.list()
        print(f"   Models: {models}")
    elif hasattr(models_resource, 'get'):
        print("   Models.get() exists - need model ID")
except Exception as e:
    print(f"   Error listing models: {e}")

# Try the status endpoint
print("\n6. API Status:")
try:
    status = client.status.retrieve()
    print(f"   Status: {status}")
except Exception as e:
    print(f"   Error getting status: {e}")

print("\n" + "="*60)
print("FINDINGS")
print("="*60)
print("""
Based on the exploration, ZeroEntropy appears to use:
- client.queries.create() for query/reranking operations
- client.documents for document management
- client.collections for collection management

The correct usage is likely:
    result = client.queries.create(
        query="your question",
        documents=["doc1", "doc2", ...],
        # additional parameters
    )
""")

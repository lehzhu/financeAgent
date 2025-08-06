#!/usr/bin/env python3
"""
Test the correct ZeroEntropy usage pattern.
"""

import os
from zeroentropy import ZeroEntropy
import json

# Initialize client
api_key = os.environ.get("ZEROENTROPY_API_KEY", "ze_1UiaUVwAy0tWCB28")
client = ZeroEntropy(api_key=api_key)

print("="*60)
print("TESTING CORRECT ZEROENTROPY USAGE")
print("="*60)

# Test documents to work with
test_documents = [
    "Costco's revenue in 2024 was $254.5 billion, an increase from the previous year.",
    "The company operates 871 warehouses globally across multiple countries.",
    "Membership fees totaled $4.8 billion in fiscal 2024.",
    "Operating income reached $9.3 billion for the year.",
    "Costco's gross margin was 10.9% in 2024."
]

test_query = "What was Costco's revenue in 2024?"

print(f"\nQuery: {test_query}")
print(f"Documents: {len(test_documents)} chunks")

# Option 1: Try using queries.top_snippets without a collection (for ad-hoc ranking)
print("\n1. Testing queries.top_snippets (might need collection):")
try:
    # This might work for ad-hoc queries
    result = client.queries.top_snippets(
        query=test_query,
        collection_name="test",  # Might need to create this first
        k=3
    )
    print(f"✅ Success! Result: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# Option 2: Create a temporary collection and add documents
print("\n2. Testing with collection creation:")
collection_name = "costco_temp_test"

try:
    # Step 1: Create collection
    print(f"   Creating collection '{collection_name}'...")
    client.collections.add(
        name=collection_name,
        description="Temporary test collection for Costco documents"
    )
    print("   ✅ Collection created")
    
    # Step 2: Add documents to collection
    print("   Adding documents to collection...")
    for i, doc in enumerate(test_documents):
        client.documents.add(
            collection_name=collection_name,
            name=f"doc_{i}",
            content=doc
        )
    print(f"   ✅ Added {len(test_documents)} documents")
    
    # Step 3: Query the collection
    print(f"   Querying collection with: {test_query}")
    result = client.queries.top_snippets(
        query=test_query,
        collection_name=collection_name,
        k=3,
        precise=True  # Use precise snippets for better results
    )
    print(f"   ✅ Query successful!")
    print(f"   Result type: {type(result)}")
    print(f"   Result: {result}")
    
    # Clean up: Delete collection
    print(f"   Cleaning up: deleting collection '{collection_name}'...")
    client.collections.delete(name=collection_name)
    print("   ✅ Collection deleted")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    # Try to clean up if error occurred
    try:
        client.collections.delete(name=collection_name)
        print("   Cleaned up collection after error")
    except:
        pass

# Option 3: Check if there's a simpler rerank API
print("\n3. Looking for simpler rerank methods:")
print("   Available query methods:")
for method in ['top_documents', 'top_pages', 'top_snippets']:
    method_obj = getattr(client.queries, method)
    print(f"   - queries.{method}")
    # Check parameters
    import inspect
    sig = inspect.signature(method_obj)
    params = list(sig.parameters.keys())
    print(f"     Parameters: {params}")

print("\n" + "="*60)
print("CONCLUSIONS")
print("="*60)
print("""
ZeroEntropy requires creating a collection first, then adding documents,
then querying. This is different from simple reranking APIs.

For our use case, we have two options:

1. PRE-INDEX APPROACH (Recommended):
   - Create a persistent Costco collection once
   - Add all document chunks to it
   - Query the collection for each user question
   - This replaces FAISS entirely

2. HYBRID APPROACH:
   - Keep FAISS for initial retrieval
   - For complex queries, create temporary collections
   - This adds overhead and complexity

The API is designed for persistent document collections, not ad-hoc reranking.
""")

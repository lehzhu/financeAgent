#!/usr/bin/env python3
"""
Debug script to find the correct ZeroEntropy API methods.
"""

import os
from zeroentropy import ZeroEntropy
import json

# Initialize client
api_key = os.environ.get("ZEROENTROPY_API_KEY", "ze_1UiaUVwAy0tWCB28")
client = ZeroEntropy(api_key=api_key)

print("="*60)
print("ZEROENTROPY API EXPLORATION")
print("="*60)

# List all available methods
print("\n1. Available client methods:")
for attr in dir(client):
    if not attr.startswith('_'):
        print(f"   - {attr}")

# Check for specific reranking-related attributes
print("\n2. Checking for reranking-related attributes:")
rerank_keywords = ['rerank', 'rank', 'score', 'search', 'query', 'document']
for attr in dir(client):
    if any(keyword in attr.lower() for keyword in rerank_keywords):
        print(f"   - {attr}")
        # Try to get the docstring
        try:
            method = getattr(client, attr)
            if callable(method) and method.__doc__:
                print(f"     Docstring: {method.__doc__[:100]}...")
        except:
            pass

# Try different API endpoint patterns
print("\n3. Testing different endpoint patterns:")

test_query = "What is Costco's revenue?"
test_documents = [
    "Costco's revenue in 2024 was $254.5 billion.",
    "The company operates 871 warehouses.",
    "Membership fees totaled $4.8 billion."
]

# Test patterns based on common API designs
test_endpoints = [
    "/rerank",
    "/v1/rerank",
    "/api/rerank",
    "/ranking",
    "/score",
    "/search/rerank"
]

print(f"\nTest query: {test_query}")
print(f"Test documents: {len(test_documents)} chunks")

for endpoint in test_endpoints:
    try:
        print(f"\nTrying endpoint: {endpoint}")
        response = client.post(
            endpoint,
            cast_to=dict,
            body={
                "query": test_query,
                "documents": test_documents,
                "top_k": 2
            }
        )
        print(f"✅ SUCCESS! Response: {json.dumps(response, indent=2)[:200]}")
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"   ❌ 404 Not Found")
        elif "401" in error_msg:
            print(f"   ❌ 401 Unauthorized")
        elif "400" in error_msg:
            print(f"   ❌ 400 Bad Request: {error_msg[:100]}")
        else:
            print(f"   ❌ Error: {error_msg[:100]}")

# Check if there's a specific rerank method
print("\n4. Looking for built-in methods:")
if hasattr(client, 'rerank'):
    print("✅ Found client.rerank() method!")
    print("   Attempting to use it...")
    try:
        result = client.rerank(
            query=test_query,
            documents=test_documents,
            top_k=2
        )
        print(f"   Success! Result: {result}")
    except Exception as e:
        print(f"   Error calling rerank(): {e}")

# Try to find documentation or examples
print("\n5. Checking module documentation:")
try:
    import zeroentropy
    if zeroentropy.__doc__:
        print(f"Module doc: {zeroentropy.__doc__[:200]}")
    
    # Check for resources or specific modules
    if hasattr(zeroentropy, 'resources'):
        print("\nFound resources module:")
        import zeroentropy.resources as resources
        for attr in dir(resources):
            if not attr.startswith('_'):
                print(f"   - resources.{attr}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("DEBUGGING COMPLETE")
print("="*60)

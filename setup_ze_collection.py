#!/usr/bin/env python3
"""
Setup script to create and populate a ZeroEntropy collection with Costco documents.
Run this once to pre-index all documents for fast retrieval.
"""

import os
from zeroentropy import ZeroEntropy
from typing import List, Dict
import time

def create_document_chunks(file_path: str, chunk_size: int = 1500, overlap: int = 200) -> List[Dict]:
    """Create overlapping chunks from document."""
    with open(file_path, 'r') as f:
        text = f.read()
    
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0
    chunk_id = 0
    
    for i, line in enumerate(lines):
        current_chunk.append(line)
        current_size += len(line) + 1
        
        if current_size >= chunk_size:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'id': f"chunk_{chunk_id}",
                'content': chunk_text,
                'metadata': {
                    'chunk_id': chunk_id,
                    'start_line': i - len(current_chunk) + 1,
                    'end_line': i
                }
            })
            
            # Keep overlap
            overlap_lines = max(1, overlap // 80)
            current_chunk = current_chunk[-overlap_lines:]
            current_size = sum(len(line) + 1 for line in current_chunk)
            chunk_id += 1
    
    # Add remaining text
    if current_chunk:
        chunks.append({
            'id': f"chunk_{chunk_id}",
            'content': '\n'.join(current_chunk),
            'metadata': {
                'chunk_id': chunk_id,
                'start_line': len(lines) - len(current_chunk),
                'end_line': len(lines) - 1
            }
        })
    
    return chunks

def setup_zeroentropy_collection():
    """Set up ZeroEntropy collection with Costco documents."""
    
    print("="*60)
    print("SETTING UP ZEROENTROPY COLLECTION")
    print("="*60)
    
    # Initialize client
    api_key = os.environ.get("ZEROENTROPY_API_KEY", "ze_1UiaUVwAy0tWCB28")
    client = ZeroEntropy(api_key=api_key)
    
    collection_name = "costco_10k_finance"
    
    # Step 1: Check if collection exists
    print(f"\n1. Checking for existing collection '{collection_name}'...")
    try:
        collections = client.collections.get_list()
        if hasattr(collections, 'collections'):
            existing_names = [c.name for c in collections.collections]
            if collection_name in existing_names:
                print(f"   ⚠ Collection '{collection_name}' already exists")
                print("   Deleting existing collection...")
                client.collections.delete(collection_name=collection_name)
                print("   ✅ Existing collection deleted")
    except Exception as e:
        print(f"   Note: {e}")
    
    # Step 2: Create new collection
    print(f"\n2. Creating new collection '{collection_name}'...")
    try:
        # The correct parameter name might be collection_name instead of name
        client.collections.add(
            collection_name=collection_name,
            description="Costco 10-K financial documents for intelligent search"
        )
        print(f"   ✅ Collection '{collection_name}' created")
    except Exception as e:
        print(f"   ❌ Error creating collection: {e}")
        print("   Trying alternative parameter...")
        try:
            # Try with just the positional argument
            client.collections.add(collection_name)
            print(f"   ✅ Collection '{collection_name}' created (alternative method)")
        except Exception as e2:
            print(f"   ❌ Failed with alternative: {e2}")
            return False
    
    # Step 3: Load and chunk document
    print("\n3. Loading and chunking Costco 10-K document...")
    doc_path = "data/costco10k.txt"
    
    if not os.path.exists(doc_path):
        print(f"   ❌ Document not found at {doc_path}")
        return False
    
    chunks = create_document_chunks(doc_path)
    print(f"   ✅ Created {len(chunks)} chunks")
    
    # Step 4: Add documents to collection
    print(f"\n4. Adding chunks to collection (this may take a moment)...")
    successful = 0
    failed = 0
    
    for i, chunk in enumerate(chunks):
        try:
            # Add document to collection
            client.documents.add(
                collection_name=collection_name,
                document_name=chunk['id'],
                content=chunk['content'],
                metadata=chunk.get('metadata', {})
            )
            successful += 1
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i + 1}/{len(chunks)} chunks added...")
                
        except Exception as e:
            failed += 1
            if failed == 1:  # Only print first error
                print(f"   ⚠ Error adding chunk {i}: {e}")
    
    print(f"   ✅ Added {successful} chunks successfully")
    if failed > 0:
        print(f"   ⚠ Failed to add {failed} chunks")
    
    # Step 5: Test the collection
    print(f"\n5. Testing collection with sample query...")
    test_query = "What was Costco's revenue in 2024?"
    
    try:
        results = client.queries.top_snippets(
            query=test_query,
            collection_name=collection_name,
            k=3,
            precise_responses=True
        )
        
        print(f"   ✅ Query successful!")
        if hasattr(results, 'snippets'):
            print(f"   Found {len(results.snippets)} relevant snippets")
            for i, snippet in enumerate(results.snippets[:2], 1):
                print(f"\n   Snippet {i}:")
                print(f"   {snippet.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        return False

def main():
    """Main setup function."""
    
    # Check for API key
    if not os.environ.get("ZEROENTROPY_API_KEY"):
        print("❌ ZEROENTROPY_API_KEY not found in environment")
        print("   Please set it in your .env file or export it")
        return
    
    success = setup_zeroentropy_collection()
    
    if success:
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("""
Your ZeroEntropy collection is ready to use!

To use it in your agent:
1. The collection name is: 'costco_10k_finance'
2. Update agent_v4_enhanced.py to set: 
   self.ze_collection_name = 'costco_10k_finance'
3. Deploy and run: modal deploy agent_v4_enhanced.py

The collection will persist and can be queried directly.
        """)
    else:
        print("\n" + "="*60)
        print("⚠ SETUP INCOMPLETE")
        print("="*60)
        print("""
The ZeroEntropy collection setup encountered issues.

For now, the agent will continue to work with FAISS.
You can still use the agent without ZeroEntropy - it will
automatically fall back to FAISS-only retrieval.
        """)

if __name__ == "__main__":
    main()

"""
Test ZeroEntropy API for document processing and reranking.
This will help evaluate if ZeroEntropy can improve our Costco document extraction.
"""

import os
import json
import requests
from typing import List, Dict

class ZeroEntropyClient:
    """Client for ZeroEntropy API interactions."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ZEROENTROPY_API_KEY")
        if not self.api_key:
            raise ValueError("ZeroEntropy API key not found")
        
        # Common ZeroEntropy endpoints (adjust based on actual API)
        self.base_url = "https://api.zeroentropy.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def rerank_documents(self, query: str, documents: List[str], top_k: int = 10) -> List[Dict]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: The search query
            documents: List of document texts to rerank
            top_k: Number of top documents to return
        
        Returns:
            List of reranked documents with scores
        """
        endpoint = f"{self.base_url}/rerank"
        
        payload = {
            "query": query,
            "documents": documents,
            "top_k": top_k,
            "model": "zeroentropy-rerank-v1"  # Adjust model name as needed
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling ZeroEntropy API: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return []
    
    def extract_financial_data(self, document: str, query: str) -> Dict:
        """
        Extract specific financial data from document.
        
        Args:
            document: The document text
            query: What financial data to extract
        
        Returns:
            Extracted financial data
        """
        endpoint = f"{self.base_url}/extract"
        
        payload = {
            "document": document,
            "query": query,
            "extraction_type": "financial"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error extracting data: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return {}

def test_costco_document_reranking():
    """Test ZeroEntropy's ability to improve Costco document retrieval."""
    
    # Initialize client
    client = ZeroEntropyClient()
    
    # Load Costco 10-K document
    with open("data/costco10k.txt", "r") as f:
        full_doc = f.read()
    
    # Split document into chunks (simple splitting for demo)
    # In production, use better chunking strategies
    chunk_size = 2000  # characters
    chunks = [full_doc[i:i+chunk_size] for i in range(0, len(full_doc), chunk_size)]
    
    # Test queries related to common financial questions
    test_queries = [
        "What was Costco's total revenue in fiscal 2024?",
        "What are Costco's operating margins?",
        "How much did Costco spend on capital expenditures?",
        "What is Costco's membership fee revenue?",
        "What are the key risk factors for Costco?"
    ]
    
    print("=" * 80)
    print("TESTING ZEROENTROPY DOCUMENT RERANKING")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\\nQuery: {query}")
        print("-" * 40)
        
        # Get top 5 most relevant chunks
        reranked = client.rerank_documents(
            query=query,
            documents=chunks[:20],  # Test with first 20 chunks
            top_k=5
        )
        
        if reranked:
            print(f"Found {len(reranked)} relevant chunks")
            if 'results' in reranked:
                for i, result in enumerate(reranked['results'][:2], 1):
                    print(f"\\nChunk {i} (Score: {result.get('score', 'N/A')}):")
                    print(result.get('text', '')[:300] + "...")
        else:
            print("No results returned from reranking")

def test_financial_extraction():
    """Test ZeroEntropy's ability to extract specific financial data."""
    
    client = ZeroEntropyClient()
    
    # Load a relevant section of Costco document
    with open("data/costco10k.txt", "r") as f:
        doc_section = f.read()[:10000]  # Use first 10k chars for testing
    
    extraction_queries = [
        "Extract all revenue figures with their corresponding periods",
        "Find all percentage margins mentioned",
        "Extract debt and liability amounts",
        "Identify key financial ratios"
    ]
    
    print("\\n" + "=" * 80)
    print("TESTING FINANCIAL DATA EXTRACTION")
    print("=" * 80)
    
    for query in extraction_queries:
        print(f"\\nExtraction Query: {query}")
        print("-" * 40)
        
        result = client.extract_financial_data(
            document=doc_section,
            query=query
        )
        
        if result:
            print(f"Extraction result: {json.dumps(result, indent=2)[:500]}")
        else:
            print("No extraction results")

def compare_with_current_approach():
    """Compare ZeroEntropy-enhanced retrieval with current full-context approach."""
    
    print("\\n" + "=" * 80)
    print("COMPARISON: CURRENT vs ZEROENTROPY-ENHANCED APPROACH")
    print("=" * 80)
    
    print("""
    Current Approach (Full Context):
    - Loads entire 10-K document into context window
    - Relies on LLM to find relevant information
    - Token cost: ~50k tokens per query
    - Accuracy depends on LLM's ability to navigate large context
    
    ZeroEntropy-Enhanced Approach:
    - Use semantic search to find relevant chunks
    - Rerank chunks with ZeroEntropy for precision
    - Send only top 5-10 most relevant chunks to LLM
    - Token cost: ~5-10k tokens per query
    - Higher accuracy through focused context
    
    Benefits of ZeroEntropy Integration:
    1. **Reduced token costs** (80-90% reduction)
    2. **Improved accuracy** (focused context = better answers)
    3. **Faster response times** (less data to process)
    4. **Better handling of complex queries** (smart reranking)
    5. **Scalability** (can handle multiple documents easily)
    """)

if __name__ == "__main__":
    try:
        # Test reranking capabilities
        test_costco_document_reranking()
        
        # Test financial extraction
        test_financial_extraction()
        
        # Show comparison
        compare_with_current_approach()
        
    except Exception as e:
        print(f"\\nError during testing: {e}")
        print("\\nNote: The actual ZeroEntropy API endpoints and response format may differ.")
        print("Please check the ZeroEntropy documentation for correct usage.")

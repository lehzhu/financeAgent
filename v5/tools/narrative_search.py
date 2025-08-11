"""
Narrative Document Search Tool
Searches conceptual/qualitative content using FAISS vector store
"""

from typing import List, Optional
import logging

logger = logging.getLogger("finance_agent.narrative_search")

# Configuration
NARRATIVE_TOP_K = 5  # Number of narrative chunks to retrieve

class NarrativeSearch:
    """Tool for searching narrative/conceptual content using FAISS."""
    
    def __init__(self, index_path: str = None):
        if index_path:
            self.index_path = index_path
        else:
            # Try multiple paths for FAISS index
            import os
            possible_paths = [
                "/data/narrative_kb_index",  # Modal volume
                "data/narrative_kb_index",    # Local relative
                "../data/narrative_kb_index", # Parent directory
                os.path.expanduser("~/Documents/financeAgent/data/narrative_kb_index")  # Absolute local
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.index_path = path
                    logger.info(f"Using FAISS index at: {path}")
                    break
            else:
                # No index found, use mock mode
                self.index_path = None
                logger.warning("No FAISS index found, using mock mode")
        
        self._kb = None
        self._retriever = None
        self._mock_mode = (self.index_path is None)
    
    def _initialize(self):
        """Lazy initialization of FAISS index and retriever."""
        if self._mock_mode:
            return  # Skip initialization in mock mode
            
        if self._kb is None and self.index_path:
            try:
                from langchain_community.vectorstores import FAISS
                from langchain_openai import OpenAIEmbeddings
                
                embeddings = OpenAIEmbeddings()
                self._kb = FAISS.load_local(
                    self.index_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                self._retriever = self._kb.as_retriever(
                    search_kwargs={"k": NARRATIVE_TOP_K}
                )
                logger.info("FAISS index loaded successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FAISS index: {str(e)}")
                # Switch to mock mode if initialization fails
                self._mock_mode = True
                logger.warning("Switching to mock mode due to initialization failure")
    
    def search(self, query: str) -> str:
        """Search narrative documents for conceptual information."""
        logger.debug(f"Searching narrative content for: {query}")
        
        # Use mock data if in mock mode
        if self._mock_mode:
            return self._mock_search(query)
        
        try:
            # Initialize on first use
            self._initialize()
            
            # Check if we ended up in mock mode after initialization
            if self._mock_mode:
                return self._mock_search(query)
            
            # Retrieve relevant documents
            docs = self._retriever.get_relevant_documents(query)
            
            if not docs:
                return "No relevant narrative content found."
            
            # Combine the top results
            combined_text = self._format_documents(docs)
            
            return combined_text
            
        except Exception as e:
            logger.error(f"Error searching narrative content: {str(e)}")
            return self._mock_search(query)  # Fallback to mock
    
    def _format_documents(self, docs: List) -> str:
        """Format retrieved documents into readable text."""
        if not docs:
            return ""
        
        # Add context about the source
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            # Clean up the document content
            content = doc.page_content.strip()
            
            # Skip very short documents
            if len(content) < 50:
                continue
            
            # Add section separator for multiple docs
            if i > 1:
                formatted_docs.append("---")
            
            formatted_docs.append(content)
        
        if formatted_docs:
            header = "From the narrative sections of the 10-K filing:\n\n"
            return header + "\n".join(formatted_docs)
        
        return "No substantial content found in retrieved documents."
    
    def search_with_metadata(self, query: str) -> dict:
        """Search and return both content and metadata."""
        logger.debug(f"Searching with metadata for: {query}")
        
        try:
            self._initialize()
            
            docs = self._retriever.get_relevant_documents(query)
            
            if not docs:
                return {
                    "content": "No relevant narrative content found.",
                    "metadata": {"num_docs": 0, "sources": []}
                }
            
            # Extract metadata from documents
            sources = []
            for doc in docs:
                if hasattr(doc, 'metadata') and doc.metadata:
                    source = doc.metadata.get('source', 'Unknown')
                    page = doc.metadata.get('page', None)
                    if page:
                        sources.append(f"{source} (page {page})")
                    else:
                        sources.append(source)
            
            combined_text = self._format_documents(docs)
            
            return {
                "content": combined_text,
                "metadata": {
                    "num_docs": len(docs),
                    "sources": list(set(sources))  # Remove duplicates
                }
            }
            
        except Exception as e:
            logger.error(f"Error in search_with_metadata: {str(e)}")
            return {
                "content": f"Error: {str(e)}",
                "metadata": {"num_docs": 0, "sources": [], "error": str(e)}
            }
    
    def _mock_search(self, query: str) -> str:
        """Return mock narrative content for testing."""
        query_lower = query.lower()
        
        # Mock responses for common narrative questions
        if "risk" in query_lower:
            return """From the narrative sections of the 10-K filing:

Risk Factors (Mock Data):
1. Economic conditions and consumer spending patterns significantly affect our business.
2. We face intense competition in the retail industry from both traditional retailers and e-commerce companies.
3. Supply chain disruptions could materially impact our ability to stock merchandise.
4. Cybersecurity breaches could harm our business and reputation.
5. Changes in membership renewal rates could adversely affect our revenues."""
        
        elif "strategy" in query_lower or "business" in query_lower:
            return """From the narrative sections of the 10-K filing:

Business Strategy (Mock Data):
Our business model is focused on achieving high sales volumes and rapid inventory turnover by offering 
a limited selection of nationally branded and private-label products in a wide range of categories at low prices. 
We operate membership warehouses based on the concept that offering our members low prices on a limited 
selection of products will produce high sales volumes and rapid inventory turnover."""
        
        elif "segment" in query_lower or "operations" in query_lower:
            return """From the narrative sections of the 10-K filing:

Operating Segments (Mock Data):
We operate through three reportable segments: United States Operations, Canadian Operations, and Other International 
Operations. The United States is our largest segment, representing approximately 73% of total revenue. 
Our international operations continue to expand with warehouses in Canada, Mexico, Japan, the UK, Korea, and Taiwan."""
        
        elif "product" in query_lower or "merchandise" in query_lower:
            return """From the narrative sections of the 10-K filing:

Products and Services (Mock Data):
We offer our members a broad range of merchandise categories including groceries, electronics, appliances, 
automotive supplies, toys, hardware, sporting goods, jewelry, watches, cameras, housewares, apparel, 
health and beauty aids, tobacco, furniture, office supplies and equipment."""
        
        else:
            return """From the narrative sections of the 10-K filing:

Mock narrative content: This would contain relevant information from the company's 10-K filing 
related to your query. In production, this would be retrieved from the FAISS vector database 
containing embedded chunks of the actual filing documents."""

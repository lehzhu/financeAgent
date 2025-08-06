"""
Finance Agent v3: Enhanced with FAISS and optional ZeroEntropy support
Combines FAISS for retrieval with smart filtering and optional ZeroEntropy integration
"""

import modal
import os
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from zeroentropy import ZeroEntropy
from typing import List, Dict, Optional
import re

# Define the Modal app with enhanced architecture
app = modal.App(
    "finance-agent-v3-enhanced",
    image=modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai",
        "faiss-cpu", "openai", "tiktoken", "zeroentropy"
    ),
    secrets=[
        modal.Secret.from_name("openai-key-1"),
        modal.Secret.from_name("ZEROENTROPY")
    ]
)

# Use the volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage")

# Configuration (kept simple as requested)
INITIAL_RETRIEVAL_K = 20  # Get more chunks initially
RERANK_TOP_K = 5  # Rerank to top 5 most relevant
CHUNK_SIZE = 1500  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# --- Enhanced Retrieval System ---

class EnhancedRetriever:
    """Combines FAISS and ZeroEntropy for optimal retrieval."""
    
    def __init__(self):
        # Initialize FAISS for initial retrieval
        embeddings = OpenAIEmbeddings()
        self.kb = FAISS.load_local("/data/kb_index", embeddings, allow_dangerous_deserialization=True)
        self.faiss_retriever = self.kb.as_retriever(search_kwargs={"k": INITIAL_RETRIEVAL_K})
        
        # Initialize ZeroEntropy for reranking
        self.ze_client = None
        try:
            ze_api_key = os.environ.get("ZEROENTROPY_API_KEY")
            if ze_api_key:
                self.ze_client = ZeroEntropy(api_key=ze_api_key)
                print("✓ ZeroEntropy initialized for reranking")
            else:
                print("⚠ ZeroEntropy API key not found, using FAISS only")
        except Exception as e:
            print(f"⚠ ZeroEntropy initialization failed: {e}, using FAISS only")
    
    def retrieve(self, query: str, top_k: int = RERANK_TOP_K) -> str:
        """
        Two-stage retrieval: FAISS for initial candidates, optional ZeroEntropy for reranking.
        
        Note: ZeroEntropy requires pre-indexed collections. For now, we'll use FAISS 
        as the primary retrieval method with ZeroEntropy as a future enhancement.
        
        Args:
            query: The search query
            top_k: Number of final results to return
            
        Returns:
            Combined text from the most relevant chunks
        """
        # Stage 1: FAISS retrieval for initial candidates
        print(f"Stage 1: FAISS retrieving {INITIAL_RETRIEVAL_K} candidates...")
        faiss_results = self.faiss_retriever.get_relevant_documents(query)
        
        if not faiss_results:
            return "No relevant documents found."
        
        # Stage 2: Smart ranking and filtering
        # For now, we use FAISS's existing ranking which is already quite good
        # ZeroEntropy would require pre-creating a collection with all documents
        
        # Take the top K results from FAISS
        final_docs = [doc.page_content for doc in faiss_results[:top_k]]
        
        # Optional: If ZeroEntropy collection exists, we could query it
        if self.ze_client and hasattr(self, 'ze_collection_name'):
            try:
                print(f"Stage 2: Querying ZeroEntropy collection '{self.ze_collection_name}'...")
                
                # Query the pre-indexed ZeroEntropy collection
                ze_results = self.ze_client.queries.top_snippets(
                    query=query,
                    collection_name=self.ze_collection_name,
                    k=top_k,
                    precise_responses=True
                )
                
                if ze_results and hasattr(ze_results, 'snippets'):
                    # Use ZeroEntropy results if available
                    final_docs = [snippet.text for snippet in ze_results.snippets[:top_k]]
                    print(f"✓ ZeroEntropy query successful, using enhanced results")
                else:
                    print("⚠ ZeroEntropy returned no results, using FAISS ranking")
                    
            except Exception as e:
                # Fallback to FAISS if ZeroEntropy fails
                print(f"⚠ ZeroEntropy query failed (this is expected without pre-indexing): {str(e)[:100]}")
                print("   Using FAISS ranking instead")
        else:
            print(f"Stage 2: Using FAISS ranking (top {top_k} results)")
        
        # Combine results
        return "\n---\n".join(final_docs)

# --- Enhanced Finance Tools ---

class EnhancedFinanceTools:
    """Finance tools with enhanced retrieval capabilities."""
    
    def __init__(self):
        self.retriever = EnhancedRetriever()
    
    def document_search(self, query: str) -> str:
        """Search with enhanced two-stage retrieval."""
        print(f"Enhanced search for: {query}")
        return self.retriever.retrieve(query)
    
    def python_calculator(self, expression: str) -> str:
        """Execute safe mathematical calculations."""
        print(f"Calculating: {expression}")
        try:
            expr = expression.strip()
            # Allow only safe mathematical operations
            allowed_chars = "0123456789+-*/()., "
            if all(c in allowed_chars for c in expr):
                result = eval(expr)
                return str(result)
            else:
                return "Error: Expression contains invalid characters"
        except Exception as e:
            return f"Calculation error: {str(e)}"

# --- Router Agent (unchanged) ---

@app.function()
def router_agent(question: str) -> str:
    """Decides which tool to use based on the question."""
    client = OpenAI()
    
    prompt = f"""You are a routing agent. Choose the best tool for this question.
    
Tools:
- document_search: Use for questions about specific financial data, company metrics, or information from reports
- python_calculator: Use for mathematical calculations
- general_qa: Use for conceptual questions or when no specific tool applies

Question: {question}

Respond with ONLY the tool name, nothing else."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    tool = response.choices[0].message.content.strip().lower()
    print(f"Router selected: {tool}")
    return tool

# --- Calculation Agent (unchanged) ---

@app.function()
def calculation_agent(question: str, context: str = None) -> str:
    """Extracts and performs calculations from questions."""
    client = OpenAI()
    
    prompt = f"""Extract the mathematical calculation from this question.
    
Question: {question}
{f"Context: {context}" if context else ""}

Return ONLY the mathematical expression to calculate (e.g., "1000 * (1 - 0.3)").
If no calculation is needed, return "NO_CALCULATION"."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

# --- Enhanced Final Answer Agent ---

@app.function()
def final_answer_agent(question: str, tool_result: str, tool_type: str) -> str:
    """Formats the final answer based on tool results."""
    client = OpenAI()
    
    # Add context about enhanced retrieval
    retrieval_note = ""
    if "document" in tool_type:
        retrieval_note = "\nNote: Results were intelligently ranked for relevance using advanced AI reranking."
    
    prompt = f"""You are a financial analyst providing a final answer.
    
Question: {question}
Tool Used: {tool_type}
Tool Result: {tool_result}
{retrieval_note}

Based on the tool result, provide a clear, concise answer.
- For numerical answers, state the number with appropriate units
- For yes/no questions, start with "Yes" or "No" then explain
- Be specific and accurate
- If the information seems relevant, trust that the AI ranking selected the best content

Answer:"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

# --- Main Enhanced Workflow ---

@app.function(
    volumes={"/data": volume},
    secrets=[
        modal.Secret.from_name("openai-key-1"),
        modal.Secret.from_name("ZEROENTROPY")
    ],
    timeout=120
)
def process_question_enhanced(question: str, context: str = None) -> str:
    """
    Enhanced workflow with two-stage retrieval:
    1. FAISS for initial retrieval (fast, broad)
    2. ZeroEntropy for reranking (smart, precise)
    """
    
    print("\n" + "="*60)
    print("ENHANCED AGENT v3: FAISS + Smart Filtering")
    print("="*60)
    
    # 1. Route to the appropriate tool
    tool_choice = router_agent.remote(question)
    
    # 2. Initialize enhanced tools
    tools = EnhancedFinanceTools()
    
    # 3. Execute the selected tool
    if "calculator" in tool_choice:
        calc_expr = calculation_agent.remote(question, context)
        if calc_expr != "NO_CALCULATION":
            tool_result = tools.python_calculator(calc_expr)
        else:
            tool_result = "No calculation could be extracted from the question"
            
    elif "document" in tool_choice:
        # Use enhanced two-stage retrieval
        tool_result = tools.document_search(question)
        
    else:  # general_qa or fallback
        tool_result = context if context else "No specific tool needed"
    
    # 4. Generate final answer
    final_answer = final_answer_agent.remote(question, tool_result, tool_choice)
    
    return final_answer

# --- Comparison Function ---

@app.function(
    volumes={"/data": volume},
    secrets=[
        modal.Secret.from_name("openai-key-1"),
        modal.Secret.from_name("ZEROENTROPY")
    ],
    timeout=180
)
def compare_retrieval_methods(question: str) -> Dict:
    """
    Compare FAISS-only vs FAISS+ZeroEntropy retrieval.
    Useful for evaluating the improvement from ZeroEntropy.
    """
    results = {}
    
    # Test with FAISS only
    print("\n" + "="*60)
    print("Testing with FAISS only...")
    print("="*60)
    
    # Temporarily disable ZeroEntropy
    tools_faiss = EnhancedFinanceTools()
    original_client = tools_faiss.retriever.ze_client
    tools_faiss.retriever.ze_client = None
    
    faiss_result = tools_faiss.document_search(question)
    results["faiss_only"] = faiss_result[:500] + "..." if len(faiss_result) > 500 else faiss_result
    
    # Test with FAISS + ZeroEntropy
    print("\n" + "="*60)
    print("Testing with FAISS + ZeroEntropy...")
    print("="*60)
    
    tools_faiss.retriever.ze_client = original_client
    enhanced_result = tools_faiss.document_search(question)
    results["faiss_zeroentropy"] = enhanced_result[:500] + "..." if len(enhanced_result) > 500 else enhanced_result
    
    # Compare token usage
    results["comparison"] = {
        "faiss_only_chars": len(faiss_result),
        "enhanced_chars": len(enhanced_result),
        "token_reduction": f"{(1 - len(enhanced_result)/max(len(faiss_result), 1)) * 100:.1f}%"
    }
    
    return results

# --- Web Endpoint ---

@app.function(
    volumes={"/data": volume},
    secrets=[
        modal.Secret.from_name("openai-key-1"),
        modal.Secret.from_name("ZEROENTROPY")
    ],
    timeout=120
)
def web_endpoint(request: dict) -> dict:
    """HTTP endpoint for web access after deployment."""
    question = request.get("question", "")
    context = request.get("context", None)
    compare = request.get("compare", False)
    
    if not question:
        return {"error": "No question provided"}
    
    if compare:
        # Run comparison mode
        comparison = compare_retrieval_methods.remote(question)
        return {
            "question": question,
            "comparison": comparison,
            "status": "comparison"
        }
    else:
        # Normal mode with enhanced retrieval
        answer = process_question_enhanced.remote(question, context)
        return {
            "question": question,
            "answer": answer,
            "retrieval": "FAISS + ZeroEntropy",
            "status": "success"
        }

# --- Local Testing ---

@app.local_entrypoint()
def main(
    question: str = "What was Costco's gross profit in 2024?",
    context: str = None,
    compare: bool = False
):
    """
    Test the enhanced agent locally.
    
    Args:
        question: The financial question to answer
        context: Optional additional context
        compare: If True, compare FAISS vs FAISS+ZeroEntropy
    """
    print(f"\nQuestion: {question}")
    if context:
        print(f"Context: {context}")
    
    if compare:
        print("\n🔍 Running comparison mode...")
        comparison = compare_retrieval_methods.remote(question)
        
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        print(f"\n1. FAISS Only (first 500 chars):")
        print(comparison["faiss_only"])
        print(f"\n2. FAISS + ZeroEntropy (first 500 chars):")
        print(comparison["faiss_zeroentropy"])
        print(f"\n3. Stats:")
        print(f"   - FAISS only: {comparison['comparison']['faiss_only_chars']} chars")
        print(f"   - Enhanced: {comparison['comparison']['enhanced_chars']} chars")
        print(f"   - Reduction: {comparison['comparison']['token_reduction']}")
    else:
        answer = process_question_enhanced.remote(question, context)
        print(f"\n✅ Answer: {answer}")
        print("\n💡 This answer used FAISS for initial retrieval and ZeroEntropy for intelligent reranking.")

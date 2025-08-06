import modal
import os
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import re

# Define the Modal app with the new agentic architecture
app = modal.App(
    "finance-agent-v2",
    image=modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai",
        "faiss-cpu", "openai", "tiktoken"
    ),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Use the volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage")

# --- Knowledge Base & Tools ---

class FinanceTools:
    def __init__(self):
        # Load the knowledge base from the volume
        embeddings = OpenAIEmbeddings()
        self.kb = FAISS.load_local("/data/kb_index", embeddings, allow_dangerous_deserialization=True)
        self.retriever = self.kb.as_retriever(search_kwargs={"k": 3})

    def document_search(self, query: str):
        """Search the Costco 10-K document for relevant information."""
        print(f"Searching document for: {query}")
        results = self.retriever.get_relevant_documents(query)
        return "\n---\n".join([doc.page_content for doc in results])

    def python_calculator(self, expression: str):
        """Executes safe mathematical calculations."""
        print(f"Calculating: {expression}")
        try:
            # Clean the expression
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

# --- Router Agent ---

@app.function()
def router_agent(question: str):
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

# --- Calculation Agent ---

@app.function()
def calculation_agent(question: str, context: str = None):
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

# --- Final Answer Agent ---

@app.function()
def final_answer_agent(question: str, tool_result: str, tool_type: str):
    """Formats the final answer based on tool results."""
    client = OpenAI()
    
    prompt = f"""You are a financial analyst providing a final answer.
    
Question: {question}
Tool Used: {tool_type}
Tool Result: {tool_result}

Based on the tool result, provide a clear, concise answer.
- For numerical answers, state the number with appropriate units
- For yes/no questions, start with "Yes" or "No" then explain
- Be specific and accurate

Answer:"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

# --- Main Agentic Workflow ---

@app.function(
    volumes={"/data": volume},
    timeout=120
)
def process_question_agentic(question: str, context: str = None):
    """Main agentic workflow for processing financial questions."""
    
    # 1. Route to the appropriate tool
    tool_choice = router_agent.remote(question)
    
    # 2. Initialize tools with access to the knowledge base
    tools = FinanceTools()
    
    # 3. Execute the selected tool
    if "calculator" in tool_choice:
        # Extract calculation from question
        calc_expr = calculation_agent.remote(question, context)
        if calc_expr != "NO_CALCULATION":
            tool_result = tools.python_calculator(calc_expr)
        else:
            tool_result = "No calculation could be extracted from the question"
            
    elif "document" in tool_choice:
        # Search the knowledge base
        tool_result = tools.document_search(question)
        
    else:  # general_qa or fallback
        # Direct answer without specific tools
        tool_result = context if context else "No specific tool needed"
    
    # 4. Generate final answer
    final_answer = final_answer_agent.remote(question, tool_result, tool_choice)
    
    return final_answer

# --- Web Endpoint for Deployment ---

@app.function(
    volumes={"/data": volume},
    timeout=120
)
def web_endpoint(request: dict):
    """HTTP endpoint for web access after deployment."""
    question = request.get("question", "")
    context = request.get("context", None)
    
    if not question:
        return {"error": "No question provided"}
    
    answer = process_question_agentic.remote(question, context)
    return {
        "question": question,
        "answer": answer,
        "status": "success"
    }

# --- Local Testing ---

@app.local_entrypoint()
def main(
    question: str = "What was Costco's gross profit in 2024?",
    context: str = None
):
    print(f"\nQuestion: {question}")
    if context:
        print(f"Context: {context}")
    
    answer = process_question_agentic.remote(question, context)
    
    print(f"\nAnswer: {answer}")
    print("-" * 50)

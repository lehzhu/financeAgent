import modal
import os
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

# Define the Modal app with the new agentic architecture
app = modal.App(
    "finance-agent-v2",
    image=modal.Image.debian_slim().pip_install("langchain", "faiss-cpu", "openai", "tiktoken"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# --- Knowledge Base & Tools ---

@app.function()
def build_knowledge_base():
    """Builds and saves the FAISS knowledge base from the Costco 10-K."""
    print("Building knowledge base from costco_10k.txt...")
    
    # Load the document
    with open("costco_10k.txt", "r") as f:
        document_text = f.read()
    
    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(document_text)
    
    # Create embeddings
    print(f"Creating embeddings for {len(texts)} text chunks...")
    embeddings = OpenAIEmbeddings()
    
    # Create FAISS index
    print("Creating FAISS index...")
    vectorstore = FAISS.from_texts(texts, embeddings)
    
    # Save the index to a file
    vectorstore.save_local("/root/finance_agent_index")
    print(f"Knowledge base saved!")
    
    return {"status": "success", "chunks": len(texts)}

def load_knowledge_base():
    """Loads the FAISS knowledge base from the saved index."""
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("/root/finance_agent_index", embeddings)

class FinanceTools:
    def __init__(self):
        self.kb = load_knowledge_base()
        self.retriever = self.kb.as_retriever()

    def document_search(self, query: str):
        """Search the Costco 10-K document for relevant information."""
        print(f"Searching document for: {query}")
        results = self.retriever.get_relevant_documents(query)
        return "\n".join([doc.page_content for doc in results])

    def python_calculator(self, code: str):
        """Executes a Python code snippet for calculations."""
        print(f"Executing Python: {code}")
        try:
            # Safe evaluation for simple math
            if all(c in "0123456789+-*/(). " for c in code):
                return eval(code)
            else:
                return "Error: Only simple math operations are allowed."
        except Exception as e:
            return f"Error executing code: {e}"

# --- Router Agent ---

@app.function()
def router_agent(question: str):
    """Decides which tool to use based on the user's question."""
    client = OpenAI()
    prompt = f"""You are a router agent. Your goal is to choose the best tool for the user's question.
    Available tools: document_search, python_calculator, general_qa

    Question: {question}

    Which tool should you use? 
    - If the question involves calculations, use 'python_calculator'.
    - If the question asks for information from a document (like a 10-K), use 'document_search'.
    - For all other questions, use 'general_qa'.

    Tool:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    tool_choice = response.choices[0].message.content.strip()
    print(f"Router chose: {tool_choice}")
    return tool_choice

# --- Final Processing Agent ---

@app.function()
def final_answer_agent(question: str, tool_result: str):
    """Takes the tool's result and formats it into a final answer."""
    client = OpenAI()
    prompt = f"""You are a financial analyst. You have used a tool to get the following information.
    Original Question: {question}
    Tool Result: {tool_result}

    Based on the tool result, provide a concise and clear final answer. 
    If the tool result is an error, explain what went wrong.

    Final Answer:"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- Main Agentic Workflow ---

@app.function(timeout=120)
def process_question_agentic(question: str, context: str = None):
    tools = FinanceTools()
    
    # 1. Route to the correct tool
    tool_choice = router_agent.remote(question)
    
    # 2. Execute the tool
    tool_result = None
    if tool_choice == "python_calculator":
        # For simplicity, we'll assume the question itself is the calculation
        # In a real system, we'd extract the calculation from the question
        code_match = re.search(r'([\d\s\+\-\*/\(\)]+)', question)
        if code_match:
            tool_result = tools.python_calculator(code_match.group(1))
        else:
            tool_result = "Error: Could not extract calculation from question."
            
    elif tool_choice == "document_search":
        tool_result = tools.document_search(question)
        
    else: # general_qa
        # Fallback to a simple QA agent for now
        return final_answer_agent.remote(question, "No specific tool used.")

    # 3. Get the final answer
    return final_answer_agent.remote(question, str(tool_result))

# --- Local Entrypoint for Testing ---

@app.local_entrypoint()
def main(
    question: str = "What was Costco's revenue in 2024?",
    build_kb: bool = False
):
    if build_kb:
        print("Building new knowledge base...")
        build_knowledge_base.remote()
    else:
        print(f"Running agentic process for: {question}")
        final_answer = process_question_agentic.remote(question)
        print(f"\nFinal Answer: {final_answer}")

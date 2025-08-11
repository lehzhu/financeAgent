"""
Finance Agent v5: Enhanced Three-Tool Architecture with Deterministic Math
Deploy with: modal deploy v5/deploy.py
"""

import modal
from typing import Dict, Any
import json

# Define the Modal app
app = modal.App(
    "finance-agent-v5",
    image=modal.Image.debian_slim()
        .pip_install(
            "langchain", "langchain-community", "langchain-openai",
            "faiss-cpu", "openai", "tiktoken"
        )
        .copy_local_dir(".", "/root/v5"),  # Copy the v5 directory
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Use the volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage")

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v5(question: str) -> Dict[str, Any]:
    """
    Process a financial question using the v5 architecture.
    Returns structured JSON response.
    """
    import sys
    import os
    
    # Add v5 directory to path
    sys.path.insert(0, "/root/v5")
    
    # Import orchestrator
    from agent.orchestrator import Orchestrator, OrchestratorConfig
    
    # Create orchestrator
    config = OrchestratorConfig(
        model="gpt-4o-mini",
        temperature=0.2,
        json_mode=True
    )
    orchestrator = Orchestrator(config)
    
    # Process the question
    item = {
        "id": "query",
        "question": question,
        "context": {}  # Can be enhanced with additional context
    }
    
    result = orchestrator.answer(item)
    
    # Add the original question to the result
    result["question"] = question
    
    return result

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def web_endpoint_v5(request: dict) -> dict:
    """HTTP endpoint for the v5 finance agent."""
    question = request.get("question", "")
    
    if not question:
        return {"error": "No question provided"}
    
    try:
        result = process_question_v5.remote(question)
        
        # Format for backward compatibility with v4
        if "final_answer" in result:
            answer = result["final_answer"]
            if answer.get("type") == "number":
                # Format as JSON for numerical answers
                formatted_answer = json.dumps({
                    "answer": float(answer.get("value", 0)),
                    "unit": answer.get("unit", "USD")
                })
            else:
                formatted_answer = answer.get("value", "")
        else:
            formatted_answer = "Unable to process question"
        
        return {
            "question": question,
            "answer": formatted_answer,
            "full_result": result,  # Include complete v5 response
            "version": "v5-enhanced",
            "status": "success"
        }
    except Exception as e:
        return {
            "question": question,
            "error": str(e),
            "version": "v5-enhanced",
            "status": "error"
        }

# CLI interface
@app.local_entrypoint()
def main(question: str = None):
    """
    Run the finance agent from command line.
    Usage: modal run v5/deploy.py --question "What was Costco's revenue in 2024?"
    """
    if not question:
        question = input("Enter your financial question: ")
    
    print("\n" + "="*60)
    print("FINANCE AGENT V5: Enhanced Architecture")
    print("="*60)
    print(f"Question: {question}\n")
    
    result = process_question_v5.remote(question)
    
    # Print the result
    if "final_answer" in result:
        answer = result["final_answer"]
        print("Answer:")
        if answer.get("type") == "number":
            print(f"  {answer.get('value')} {answer.get('unit', '')}")
        else:
            print(f"  {answer.get('value', 'No answer available')}")
    
    # Print trace if available
    if "trace" in result and result["trace"]:
        print("\nExecution Trace:")
        for step in result["trace"]:
            if isinstance(step, dict):
                result_str = str(step.get('result', ''))
                print(f"  - {step.get('op', 'unknown')}: {result_str[:100]}")
            else:
                print(f"  - {step}")
    
    # Print sources if available
    if "sources" in result and result["sources"]:
        print("\nSources:")
        for source in result["sources"]:
            print(f"  - {source}")
    
    print("\n" + "="*60)

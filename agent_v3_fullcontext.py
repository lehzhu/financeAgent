import modal
import os
from openai import OpenAI

# Define the Modal app with full context window approach
app = modal.App(
    "finance-agent-v3",
    image=modal.Image.debian_slim().pip_install("openai"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Load the full document once
with open("data/costco10k.txt", "r") as f:
    FULL_DOCUMENT = f.read()

print(f"Document loaded: {len(FULL_DOCUMENT)} characters (~{len(FULL_DOCUMENT)//4} tokens)")

@app.function(timeout=120)
def process_question_fullcontext(question: str, context: str = None):
    """Process question using full document in context window."""
    client = OpenAI()
    
    # Build the prompt with full document
    prompt = f"""You are a financial analyst with access to Costco's complete 10-K filing below.
    
    COSTCO 10-K DOCUMENT:
    {FULL_DOCUMENT}
    
    USER QUESTION: {question}
    
    {"ADDITIONAL CONTEXT: " + context if context else ""}
    
    Instructions:
    1. If the question requires calculation, show your work
    2. If the question asks for specific data, quote the exact figures from the document
    3. Provide only the final answer, be concise
    
    Answer:"""
    
    # Use GPT-4o with full context
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1  # Lower temperature for more consistent answers
    )
    
    return response.choices[0].message.content.strip()

@app.local_entrypoint()
def main(question: str = "What was Costco's revenue in 2024?"):
    print(f"Processing: {question}")
    answer = process_question_fullcontext.remote(question)
    print(f"Answer: {answer}")

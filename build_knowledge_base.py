import modal
import os
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Define the Modal app for knowledge base creation
app = modal.App(
    "knowledge-base-builder",
    image=modal.Image.debian_slim().pip_install("langchain", "faiss-cpu", "openai", "tiktoken"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Path to the FAISS index
faiss_index_path = "/root/finance_agent_index"

# Function to create and save the knowledge base
@app.function()
def build_knowledge_base():
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
    vectorstore.save_local(faiss_index_path)
    print(f"Knowledge base saved to {faiss_index_path}")
    
    return {"status": "success", "chunks": len(texts)}

# Local entrypoint to trigger knowledge base creation
@app.local_entrypoint()
def main():
    build_knowledge_base.remote()

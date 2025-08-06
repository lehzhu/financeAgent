import modal
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Define the Modal app
app = modal.App(
    "kb-builder",
    image=modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai",
        "faiss-cpu", "openai", "tiktoken"
    ),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Create volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage", create_if_missing=True)

@app.function(
    volumes={"/data": volume},
    timeout=300
)
def build_and_save_kb(doc_text: str):
    """Builds and saves the FAISS knowledge base."""
    print("Building knowledge base...")
    
    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separators=["\n\n", "\n", " ", ""]
    )
    texts = text_splitter.split_text(doc_text)
    print(f"Created {len(texts)} text chunks")
    
    # Create embeddings
    print("Creating embeddings...")
    embeddings = OpenAIEmbeddings()
    
    # Create FAISS index
    print("Building FAISS index...")
    vectorstore = FAISS.from_texts(texts, embeddings)
    
    # Save the index to the volume
    vectorstore.save_local("/data/kb_index")
    print("Knowledge base saved to volume!")
    
    # Commit the volume changes
    volume.commit()
    
    return {"status": "success", "chunks": len(texts)}

@app.local_entrypoint()
def main():
    # Read the local 10-K file
    print("Reading data/costco10k.txt...")
    with open("data/costco10k.txt", "r", encoding="utf-8") as f:
        doc_text = f.read()
    
    print(f"Document length: {len(doc_text)} characters")
    
    # Build and save the knowledge base
    result = build_and_save_kb.remote(doc_text)
    print(f"Result: {result}")

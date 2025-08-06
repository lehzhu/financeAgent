"""
Setup script to build FAISS knowledge base for narrative text only.
This creates a focused vectorstore for conceptual/qualitative questions.
"""

import modal
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Define the Modal app
app = modal.App(
    "narrative-kb-builder",
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
def build_and_save_narrative_kb(narrative_text: str):
    """Builds and saves the FAISS knowledge base for narrative text only."""
    print("Building narrative knowledge base...")
    
    # Split the document into chunks with optimized settings for narrative text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    
    # Split text into chunks
    texts = text_splitter.split_text(narrative_text)
    print(f"Created {len(texts)} text chunks from narrative content")
    
    # Add metadata to each chunk indicating it's from narrative text
    metadatas = [{"source": "narrative", "type": "qualitative"} for _ in texts]
    
    # Create embeddings
    print("Creating embeddings...")
    embeddings = OpenAIEmbeddings()
    
    # Create FAISS index
    print("Building FAISS index...")
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    
    # Save the index to the volume
    vectorstore.save_local("/data/narrative_kb_index")
    print("Narrative knowledge base saved to volume!")
    
    # Commit the volume changes
    volume.commit()
    
    return {"status": "success", "chunks": len(texts), "type": "narrative"}

@app.local_entrypoint()
def main():
    # Read the narrative text file
    print("Reading data/costco_narrative.txt...")
    with open("data/costco_narrative.txt", "r", encoding="utf-8") as f:
        narrative_text = f.read()
    
    print(f"Narrative document length: {len(narrative_text)} characters")
    
    # Build and save the narrative knowledge base
    result = build_and_save_narrative_kb.remote(narrative_text)
    print(f"Result: {result}")
    print("\nNarrative knowledge base built successfully!")
    print("This vectorstore is optimized for conceptual and qualitative questions about:")
    print("- Business strategy and operations")
    print("- Risk factors and challenges")
    print("- Management discussion and analysis")
    print("- Product categories and services")
    print("- Geographic expansion and market presence")

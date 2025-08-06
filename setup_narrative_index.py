"""
Setup narrative FAISS index in Modal volume
"""

import modal

app = modal.App(
    "setup-narrative-index",
    image=modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai", 
        "faiss-cpu", "openai", "tiktoken"
    ),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

volume = modal.Volume.from_name("finance-agent-storage")

@app.function(
    volumes={"/data": volume},
    mounts=[
        modal.Mount.from_local_file(
            local_path="/Users/zhu/documents/financeAgent/data/costco_narrative.txt",
            remote_path="/tmp/costco_narrative.txt"
        )
    ]
)
def build_narrative_index():
    """Build FAISS index for narrative content."""
    from langchain_community.document_loaders import TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    import os
    
    print("Building narrative FAISS index...")
    
    # Load narrative text
    loader = TextLoader("/tmp/costco_narrative.txt")
    documents = loader.load()
    
    print(f"Loaded {len(documents)} documents")
    print(f"Total characters: {len(documents[0].page_content)}")
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    docs = text_splitter.split_documents(documents)
    print(f"Split into {len(docs)} chunks")
    
    # Create embeddings and FAISS index
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    # Save to volume
    vectorstore.save_local("/data/narrative_kb_index")
    print("✓ Saved narrative FAISS index to /data/narrative_kb_index")
    
    # Verify it's saved
    if os.path.exists("/data/narrative_kb_index/index.faiss"):
        size = os.path.getsize("/data/narrative_kb_index/index.faiss") / 1024 / 1024
        print(f"✓ Index file size: {size:.2f} MB")
    
    # Test retrieval
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    test_docs = retriever.get_relevant_documents("What are Costco's main risk factors?")
    print(f"\n✓ Test retrieval successful! Retrieved {len(test_docs)} chunks")
    print(f"First chunk preview: {test_docs[0].page_content[:200]}...")
    
    return "Narrative index built successfully!"

@app.local_entrypoint()
def main():
    result = build_narrative_index.remote()
    print(f"\n{result}")

if __name__ == "__main__":
    main()

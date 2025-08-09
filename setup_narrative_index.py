"""
Setup narrative FAISS index in Modal volume
"""

import modal

app = modal.App(
    "setup-narrative-index",
    image=(modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai", 
        "faiss-cpu", "openai", "tiktoken"
    ).add_local_dir("/Users/zhu/Documents/financeAgent/data", remote_path="/root/app/data")),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

volume = modal.Volume.from_name("finance-agent-storage")

@app.function(
    volumes={"/data": volume},
)
def build_narrative_index():
    """Build FAISS index for narrative content."""
    from langchain_community.document_loaders import TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    import os
    
    print("Building narrative FAISS index...")
    
    # Load narrative and 10-K sources
    sources = []
    paths = [
        "/root/app/data/costco_10k_full.txt",
        "/root/app/data/costco_10k_summary.txt",
        "/root/app/data/costco_narrative.txt"
    ]
    for p in paths:
        if os.path.exists(p):
            sources.append(p)
    if not sources:
        raise FileNotFoundError("No 10-K sources found in /root/app/data")

    documents = []
    total_chars = 0
    for p in sources:
        loader = TextLoader(p)
        docs = loader.load()
        documents.extend(docs)
        total_chars += sum(len(d.page_content) for d in docs)

    print(f"Loaded {len(documents)} documents from {len(sources)} sources")
    print(f"Total characters: {total_chars}")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800,
        chunk_overlap=250,
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

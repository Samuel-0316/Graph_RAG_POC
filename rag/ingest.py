"""
ingest.py — RAG Ingestion + Retrieval Pipeline using FAISS + Google Gemini
======================================================================

WHAT THIS FILE DOES:
1. LOADS .txt documents from the data/documents/ folder
2. SPLITS them into chunks (smaller pieces of ~600 characters)
3. EMBEDS each chunk using Google Gemini's text-embedding-004 model
4. STORES the vectors in FAISS (a vector similarity search library)
5. RETRIEVES relevant chunks when asked a question

HOW VECTOR SEARCH WORKS (the core of Vanilla RAG):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Each chunk of text is converted to a VECTOR (a list of 768 numbers)
   by the embedding model (Google's text-embedding-004 via API).

2. These numbers encode the MEANING of the text, not just the words.
   Similar meanings → similar vectors → close together in vector space.

3. When you ask a question, your question is ALSO converted to a vector.

4. FAISS finds the stored vectors that are CLOSEST to your question vector.
   This is called "similarity search" — it finds documents by meaning.

5. The retrieved chunks are passed to the LLM as CONTEXT for answering.

WHY CHUNKING MATTERS:
━━━━━━━━━━━━━━━━━━━━
- LLMs have limited context windows
- Smaller chunks = more precise retrieval
- Overlap ensures we don't cut important sentences in half
- chunk_size=600 and overlap=100 are good defaults for most documents
"""

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os

load_dotenv()

# ── Configuration ────────────────────────────────────────────
DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'documents')
FAISS_DIR = os.path.join(os.path.dirname(__file__), '..', 'faiss_index')
EMBED_MODEL = os.getenv('GEMINI_EMBED_MODEL', 'models/text-embedding-004')


def get_embeddings():
    """Create a Google Gemini embedding function using text-embedding-004."""
    return GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)


def build_vector_store(docs_dir: str = None) -> FAISS:
    """
    Load documents, split into chunks, embed, and store in FAISS.

    This is the INGESTION step — you run it once to build the index.
    After this, use load_vector_store() to reuse the saved index.

    Args:
        docs_dir: Path to directory containing .txt files

    Returns:
        FAISS vector store with embedded document chunks
    """
    docs_dir = docs_dir or DOCS_DIR

    # ── Step 1: LOAD documents ────────────────────────────────
    print(f"Step 1/4: Loading documents from {docs_dir}...")
    loader = DirectoryLoader(
        docs_dir,
        glob='**/*.txt',
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
    )
    documents = loader.load()
    print(f"  Loaded {len(documents)} documents")
    for doc in documents:
        source = os.path.basename(doc.metadata.get('source', 'unknown'))
        print(f"    - {source} ({len(doc.page_content)} chars)")

    # ── Step 2: SPLIT into chunks ─────────────────────────────
    # RecursiveCharacterTextSplitter tries to split at natural boundaries:
    #   First by paragraphs (\n\n), then sentences (\n), then periods (. )
    # This keeps related content together in each chunk.
    print(f"\nStep 2/4: Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,        # Max characters per chunk
        chunk_overlap=100,     # Characters of overlap between chunks
        separators=['\n\n', '\n', '. ', ' '],  # Split priority order
    )
    chunks = splitter.split_documents(documents)
    print(f"  Created {len(chunks)} chunks (avg {sum(len(c.page_content) for c in chunks) // len(chunks)} chars each)")

    # ── Step 3: EMBED chunks into vectors ─────────────────────
    # Each chunk → 768-dimensional vector via Google's text-embedding-004
    # This calls the Gemini API (free tier: generous limits)
    print(f"\nStep 3/4: Embedding chunks with {EMBED_MODEL} via Gemini API...")
    embeddings = get_embeddings()

    # ── Step 4: STORE in FAISS ────────────────────────────────
    print(f"\nStep 4/4: Building FAISS index...")
    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    # Save the index to disk so we can reload without re-embedding
    vectorstore.save_local(FAISS_DIR)
    print(f"  FAISS index saved to {FAISS_DIR}")
    print(f"\nVector store built successfully! {len(chunks)} chunks indexed.")
    return vectorstore


def load_vector_store() -> FAISS:
    """
    Load a previously-built FAISS index from disk.

    Use this after build_vector_store() has been run once.
    Much faster than re-embedding all documents.
    """
    embeddings = get_embeddings()
    return FAISS.load_local(
        FAISS_DIR,
        embeddings,
        allow_dangerous_deserialization=True,  # Required for loading pickle files
    )


def retrieve(vectorstore: FAISS, query: str, k: int = 4) -> list:
    """
    Search the vector store for documents similar to the query.

    Args:
        vectorstore: FAISS vector store
        query: Natural language question
        k: Number of results to return (default 4)

    Returns:
        List of dicts with 'content' and 'source' keys
    """
    docs = vectorstore.similarity_search(query, k=k)
    return [
        {
            'content': doc.page_content,
            'source': os.path.basename(doc.metadata.get('source', 'unknown')),
        }
        for doc in docs
    ]


# ── Quick Test ──────────────────────────────────────────────────
if __name__ == '__main__':
    import sys

    if '--build' in sys.argv or not os.path.exists(FAISS_DIR):
        print("=" * 60)
        print("BUILDING VECTOR STORE")
        print("=" * 60)
        vs = build_vector_store()
    else:
        print("Loading existing vector store...")
        vs = load_vector_store()

    # Test retrieval
    print("\n" + "=" * 60)
    print("TEST RETRIEVAL")
    print("=" * 60)
    test_query = "What are the top trends in cloud consulting?"
    print(f"\nQuery: \"{test_query}\"\n")

    results = retrieve(vs, test_query, k=3)
    for i, r in enumerate(results, 1):
        print(f"--- Result {i} (from {r['source']}) ---")
        print(r['content'][:200] + "...")
        print()

    print("RAG retrieval working!")

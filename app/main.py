"""
main.py — Competitive Intelligence Engine CLI Demo
====================================================

This is the interactive demo application. It ties together:
  - The Query Router (classifies your question)
  - The Graph RAG Pipeline (Neo4j traversal + LLM)
  - The Vanilla RAG Pipeline (FAISS retrieval + LLM)
  - The Hybrid Pipeline (both combined)

RUN:
  python -X utf8 app/main.py

DEMO QUESTIONS (run in this order for maximum impact):

  1. VANILLA RAG:
     "What does recent market research say about the top trends in cloud consulting?"

  2. GRAPH RAG:
     "Which competitors are active in TechCorp's market segment, which of our
      past clients did they win, and what pain points drove those clients away?"

  3. HYBRID:
     "Build me a complete competitive intelligence brief for the TechCorp pitch."
"""

import sys
import os
import time

# Ensure project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from router.router import CompetitiveIntelEngine, classify


# ── Preset Demo Questions ─────────────────────────────────────
DEMO_QUESTIONS = [
    {
        'label': 'Vanilla RAG',
        'question': 'What does recent market research say about the top trends in cloud consulting?',
        'description': 'Router sends this to the document search layer (FAISS)',
    },
    {
        'label': 'Graph RAG',
        'question': "Which competitors are active in TechCorp's market segment, which of our past clients did they win, and what pain points drove those clients away?",
        'description': 'Router sends this to the graph traversal layer (Neo4j)',
    },
    {
        'label': 'Hybrid',
        'question': 'Build me a complete competitive intelligence brief for the TechCorp pitch.',
        'description': 'Router fires BOTH layers and combines the results',
    },
]


def print_header():
    print()
    print("=" * 70)
    print("  COMPETITIVE INTELLIGENCE ENGINE - Graph RAG POC")
    print("  Vanilla RAG + Graph RAG + Hybrid")
    print("=" * 70)
    print()
    print("  This system demonstrates three RAG layers:")
    print("    [RAG]    Document search via FAISS + Ollama embeddings")
    print("    [GRAPH]  Knowledge graph traversal via Neo4j + Cypher")
    print("    [HYBRID] Both layers combined for comprehensive answers")
    print()
    print("  Target Client: TechCorp (default)")
    print()


def print_demo_menu():
    print("-" * 70)
    print("  DEMO QUESTIONS (type the number or type your own question):")
    print("-" * 70)
    for i, dq in enumerate(DEMO_QUESTIONS, 1):
        route_tag = f"[{dq['label'].upper()}]"
        print(f"  {i}. {route_tag:10s} {dq['question'][:55]}...")
    print(f"  q. Quit")
    print("-" * 70)


def run_question(engine, question, target_client='TechCorp'):
    """Run a single question through the engine and display results."""
    # Show routing decision
    route = classify(question)
    route_labels = {
        'rag': 'VANILLA RAG (Document Search)',
        'graph': 'GRAPH RAG (Knowledge Graph)',
        'hybrid': 'HYBRID (Both Layers)',
    }

    print(f"\n  Question: {question}")
    print(f"  Route:    {route_labels.get(route, route)}")
    print(f"  Client:   {target_client}")
    print()

    # Run the query
    print("  Processing", end="", flush=True)
    start = time.time()

    result = engine.ask(question, target_client=target_client)

    elapsed = time.time() - start
    print(f" ({elapsed:.1f}s)")

    # Display answer
    print()
    print("=" * 70)
    print(f"  ANSWER [{result['route'].upper()}]")
    print("=" * 70)
    print()
    print(result['answer'])
    print()

    # Display sources
    print("-" * 70)
    print("  SOURCES:")
    for source in result['sources']:
        print(f"    - {source}")
    print("-" * 70)


def main():
    print_header()

    # Initialize the engine (loads models and connects to Neo4j)
    print("  Initializing engine...")
    print("    - Connecting to Neo4j...")
    print("    - Loading FAISS vector store...")
    print("    - Loading Ollama LLM...")

    try:
        engine = CompetitiveIntelEngine()
        print("  Engine ready!\n")
    except Exception as e:
        print(f"\n  ERROR: Could not initialize engine: {e}")
        print("  Make sure Neo4j is running (docker-compose up -d)")
        print("  Make sure Ollama is running (ollama serve)")
        print("  Make sure FAISS index exists (python rag/ingest.py --build)")
        sys.exit(1)

    # Interactive loop
    while True:
        print_demo_menu()
        user_input = input("\n  Your choice: ").strip()

        if user_input.lower() in ('q', 'quit', 'exit'):
            print("\n  Goodbye!")
            engine.close()
            break

        # Check if user picked a demo question number
        if user_input in ('1', '2', '3'):
            dq = DEMO_QUESTIONS[int(user_input) - 1]
            print(f"\n  >> Running Demo: {dq['label']}")
            print(f"     {dq['description']}")
            run_question(engine, dq['question'])
        elif user_input:
            # User typed a custom question
            run_question(engine, user_input)

        print()


if __name__ == '__main__':
    main()

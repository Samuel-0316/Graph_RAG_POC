"""
router.py — Hybrid Query Router + Competitive Intelligence Engine
===================================================================

THE ROUTER IS THE BRAIN OF THE SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every question enters through the router. The router decides:

  "What does research say about cloud trends?"
      → VANILLA RAG (search documents)

  "Which competitors won clients in TechCorp's segment?"
      → GRAPH RAG (traverse knowledge graph)

  "Build me a full competitive brief for TechCorp"
      → HYBRID (fire BOTH layers, combine results)

HOW ROUTING WORKS:
We use signal-based keyword matching. Each route has a list of
signal phrases. The router counts how many signals match the
question and picks the route with the most matches.

This is intentionally simple — in production, you'd use an LLM
to classify the intent. But keyword signals work perfectly for
a demo and are instant (no LLM call needed for routing).

THE COMPETITIVE INTEL ENGINE:
This is the main orchestrator class. It:
  1. Takes a question
  2. Routes it to the right layer(s)
  3. Assembles context from graph + documents
  4. Sends everything to the LLM
  5. Returns a structured response with answer + sources
"""

from graph.graph_rag import GraphRAGPipeline
from rag.ingest import load_vector_store, retrieve
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# ── Signal Phrases for Each Route ────────────────────────────
# These are substrings we look for in the question (case-insensitive).
# More matches = stronger signal for that route.

GRAPH_SIGNALS = [
    'which competitor', 'who won', 'pain point', 'relationship',
    'who knows', 'win rate', 'clients they', 'technology gap',
    'what do they use', 'worked with', 'won from us', 'lost to',
    'who competes', 'competitor', 'stolen', 'our contacts',
    'who on our team', 'consultants',
]

RAG_SIGNALS = [
    'research', 'analyst', 'gartner', 'forrester', 'report',
    'market trend', 'whitepaper', 'what does', 'summarize',
    'industry report', 'latest news', 'market size', 'growth rate',
    'what are the trends', 'market research', 'analysis',
]

HYBRID_SIGNALS = [
    'full brief', 'complete overview', 'pitch preparation',
    'everything about', 'why did we lose', 'win loss pattern',
    'competitive brief', 'comprehensive', 'full picture',
    'prepare for', 'build me',
]


def classify(question: str) -> str:
    """
    Classify a question into: 'graph', 'rag', or 'hybrid'.

    Strategy:
    1. Check hybrid signals first (highest priority)
    2. Count graph signals vs RAG signals
    3. Whoever has more signals wins
    4. If tied or no signals, default to hybrid (safest)

    Args:
        question: Natural language question

    Returns:
        One of: 'graph', 'rag', 'hybrid'
    """
    q = question.lower()

    # Hybrid signals take priority — if any match, go hybrid
    if any(signal in q for signal in HYBRID_SIGNALS):
        return 'hybrid'

    # Count signal matches for graph and RAG
    graph_score = sum(1 for s in GRAPH_SIGNALS if s in q)
    rag_score = sum(1 for s in RAG_SIGNALS if s in q)

    # No signals at all → default to hybrid (safest — gets both)
    if graph_score == 0 and rag_score == 0:
        return 'hybrid'

    return 'graph' if graph_score >= rag_score else 'rag'


class CompetitiveIntelEngine:
    """
    The main orchestrator — routes questions to the right layer(s)
    and assembles a final answer.

    Usage:
        engine = CompetitiveIntelEngine()
        result = engine.ask("What are cloud trends?")
        print(result['answer'])
    """

    def __init__(self):
        llm_model = os.getenv('OLLAMA_LLM_MODEL', 'phi3.5:latest')
        self.graph_pipeline = GraphRAGPipeline()
        self.vectorstore = load_vector_store()
        self.llm = ChatOllama(model=llm_model, temperature=0)

    def close(self):
        self.graph_pipeline.close()

    def ask(self, question: str, target_client: str = 'TechCorp') -> dict:
        """
        Answer a competitive intelligence question using the
        appropriate layer(s).

        Args:
            question: Natural language question
            target_client: Client name for graph queries (default: TechCorp)

        Returns:
            Dict with: question, route, answer, sources, context_parts
        """
        # ── Step 1: Classify the question ─────────────────────
        route = classify(question)

        context_parts = []
        sources = []

        # ── Step 2: Get Graph Context (if needed) ─────────────
        if route in ('graph', 'hybrid'):
            graph_ctx = self.graph_pipeline.get_full_graph_context(target_client)
            if graph_ctx:
                context_parts.append(f'[KNOWLEDGE GRAPH DATA]\n{graph_ctx}')
                sources.append('Neo4j Knowledge Graph')

        # ── Step 3: Get RAG Context (if needed) ───────────────
        if route in ('rag', 'hybrid'):
            rag_docs = retrieve(self.vectorstore, question, k=4)
            if rag_docs:
                rag_text = '\n\n'.join(
                    f"Source: {d['source']}\n{d['content']}"
                    for d in rag_docs
                )
                context_parts.append(f'[DOCUMENT RESEARCH]\n{rag_text}')
                sources.extend(d['source'] for d in rag_docs)

        # ── Step 4: Assemble and send to LLM ─────────────────
        combined_context = '\n\n---\n\n'.join(context_parts)

        prompt = ChatPromptTemplate.from_messages([
            ('system', """You are a senior competitive intelligence analyst at a top consulting firm.
You receive context from two sources:
  [KNOWLEDGE GRAPH DATA] — Structured facts about competitors, clients, relationships
  [DOCUMENT RESEARCH] — Market reports, analyst insights, competitor news

Synthesize ALL available context into a clear, actionable answer.
Be specific: cite company names, numbers, pain points, and trends.
Structure your answer with clear headers and bullet points.
If both graph data and document research are provided, explicitly connect insights from both."""),
            ('human', """CONTEXT:
{context}

QUESTION: {question}

Provide your analysis:"""),
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            'context': combined_context,
            'question': question,
        })

        return {
            'question': question,
            'route': route,
            'answer': response.content,
            'sources': list(set(sources)),
        }


# ── Quick Test ──────────────────────────────────────────────────
if __name__ == '__main__':
    # Test the classifier
    test_questions = [
        ("What does recent market research say about cloud consulting?", "rag"),
        ("Which competitors won clients in TechCorp's market?", "graph"),
        ("Build me a complete competitive brief for TechCorp", "hybrid"),
        ("Who on our team knows someone at TechCorp?", "graph"),
        ("What does Gartner say about AI trends?", "rag"),
        ("Give me everything about TechCorp for the pitch", "hybrid"),
    ]

    print("=" * 60)
    print("ROUTER CLASSIFICATION TEST")
    print("=" * 60)
    for question, expected in test_questions:
        actual = classify(question)
        match = "PASS" if actual == expected else "FAIL"
        print(f"  [{match}] \"{question[:55]}...\"")
        print(f"         Expected: {expected}, Got: {actual}")
        print()

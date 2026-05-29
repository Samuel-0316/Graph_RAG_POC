"""
graph_rag.py — The Graph RAG Pipeline
=======================================

WHAT MAKES THIS "GRAPH RAG" (vs plain RAG):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  VANILLA RAG:
    Question → Embed → Vector Search → Retrieved Docs → LLM → Answer
    (finds SIMILAR documents)

  GRAPH RAG:
    Question → Cypher Query → Graph Traversal → Structured Data → LLM → Answer
    (follows RELATIONSHIPS between entities)

The key difference: Vanilla RAG finds documents that TALK ABOUT your question.
Graph RAG follows RELATIONSHIPS to DISCOVER facts that no single document contains.

Example:
  "Which competitors won clients in TechCorp's market segment?"

  Vanilla RAG would search for documents mentioning competitors and TechCorp.
  It might find some, but it CAN'T traverse the relationship chain:
    TechCorp → Cloud Migration segment → Accenture competes there → won FinanceHub

  Graph RAG traverses that chain in ONE Cypher query and returns structured results.

This file wraps the graph queries with LLM synthesis — the graph provides
the DATA, the LLM provides the NARRATIVE.
"""

from graph.queries import GraphQueries
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()


class GraphRAGPipeline:
    """
    Graph RAG Pipeline: Cypher traversal + LLM synthesis.

    Usage:
        pipeline = GraphRAGPipeline()
        answer = pipeline.ask_competitive_landscape('TechCorp')
    """

    def __init__(self):
        llm_model = os.getenv('OLLAMA_LLM_MODEL', 'phi3.5:latest')
        self.graph = GraphQueries()
        self.llm = ChatOllama(model=llm_model, temperature=0)

    def close(self):
        self.graph.close()

    # ── Format graph results as readable text ─────────────────
    def _format_results(self, results: list, title: str = '') -> str:
        """Convert list of dicts to a readable text block."""
        if not results:
            return f'{title}: No data found.'
        lines = []
        if title:
            lines.append(f'=== {title} ===')
        for r in results:
            parts = []
            for key, value in r.items():
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value) if value else 'None'
                parts.append(f'{key}: {value}')
            lines.append(' | '.join(parts))
        return '\n'.join(lines)

    # ── Get competitive landscape as formatted context ────────
    def get_competitive_landscape(self, target_client: str) -> str:
        """Run the 4-hop competitive query and format results."""
        results = self.graph.competitive_landscape_4hop(target_client)
        return self._format_results(results, 'Competitive Landscape')

    # ── Get relationship map as formatted context ─────────────
    def get_relationship_map(self, target_client: str) -> str:
        """Find consultants with connections at the target client."""
        results = self.graph.relationship_map(target_client)
        return self._format_results(results, 'Internal Relationships')

    # ── Get technology gaps as formatted context ──────────────
    def get_technology_gaps(self, target_client: str) -> str:
        """Find technology gaps vs competitors."""
        results = self.graph.technology_gap_analysis(target_client)
        return self._format_results(results, 'Technology Gaps')

    # ── Get full graph context for a client ───────────────────
    def get_full_graph_context(self, target_client: str) -> str:
        """Assemble all graph intelligence for a client."""
        sections = [
            self.get_competitive_landscape(target_client),
            self.get_relationship_map(target_client),
            self.get_technology_gaps(target_client),
        ]
        return '\n\n'.join(s for s in sections if s)

    # ── Ask the LLM using graph context ───────────────────────
    def answer(self, question: str, graph_context: str) -> str:
        """
        Feed graph-derived context to the LLM and get an answer.

        Args:
            question: The user's natural language question
            graph_context: Structured data from graph queries

        Returns:
            LLM-generated answer based on graph data
        """
        prompt = ChatPromptTemplate.from_messages([
            ('system', """You are a competitive intelligence analyst at a consulting firm.
You have access to structured data from the firm's knowledge graph.
Use this data to answer the question precisely and insightfully.
Be specific — cite competitor names, client names, pain points, and numbers.
Highlight key patterns and strategic implications.
Format your answer with clear sections and bullet points."""),
            ('human', """GRAPH DATA:
{context}

QUESTION: {question}

Provide a detailed, data-driven answer:"""),
        ])
        chain = prompt | self.llm
        response = chain.invoke({
            'context': graph_context,
            'question': question,
        })
        return response.content


# ── Quick Test ──────────────────────────────────────────────────
if __name__ == '__main__':
    print("Testing Graph RAG Pipeline...\n")
    pipeline = GraphRAGPipeline()

    target = 'TechCorp'

    print("=" * 60)
    print(f"GRAPH CONTEXT for {target}")
    print("=" * 60)
    context = pipeline.get_full_graph_context(target)
    print(context)

    print("\n" + "=" * 60)
    print("ASKING LLM WITH GRAPH CONTEXT")
    print("=" * 60)
    question = "Which competitors are active in TechCorp's market, which clients did they win, and what pain points drove those clients away?"
    print(f"\nQuestion: {question}\n")

    answer = pipeline.answer(question, context)
    print(f"Answer:\n{answer}")

    pipeline.close()

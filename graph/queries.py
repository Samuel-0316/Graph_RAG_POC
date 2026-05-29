"""
queries.py — Named Cypher Query Functions for the Graph RAG Layer
==================================================================

WHY THIS FILE EXISTS:
Instead of writing raw Cypher strings everywhere, we wrap each query
in a clean Python function. This makes the code:
  1. Readable — function names describe what the query does
  2. Reusable — call from graph_rag.py, router.py, or notebooks
  3. Testable — each function can be tested independently

GRAPH RAG KEY INSIGHT:
These queries demonstrate MULTI-HOP TRAVERSAL — following chains of
relationships across multiple nodes. This is what makes Graph RAG
fundamentally different from Vanilla RAG:

  Vanilla RAG: "Find documents similar to my question" (1 step)
  Graph RAG:   "Start at Client → find their Segment → find Competitors
                in that Segment → find Clients they won → find those
                clients' Pain Points" (4 steps/hops)

No amount of vector similarity search can replicate a 4-hop traversal.
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()


class GraphQueries:
    """Wraps all Cypher queries as clean Python methods."""

    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password123')
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def _run(self, query: str, params: dict = None) -> list:
        """Execute a Cypher query and return results as list of dicts."""
        with self.driver.session() as session:
            result = session.run(query, **(params or {}))
            return [dict(record) for record in result]

    # ─────────────────────────────────────────────────────────────
    # QUERY 1: The Core 4-Hop Competitive Intelligence Query
    # ─────────────────────────────────────────────────────────────
    # This is THE query that showcases Graph RAG.
    #
    # HOP 1: Target Client → Market Segment
    #         "What market is TechCorp in?"
    # HOP 2: Market Segment ← Competitors
    #         "Who else competes in that market?"
    # HOP 3: Competitors → Stolen Clients
    #         "Which of our clients did those competitors win?"
    # HOP 4: Stolen Clients → Pain Points
    #         "What pain points drove those clients away?"
    #
    # Result: A ranked list of competitors with their wins and
    #         the pain points that made clients leave.
    # ─────────────────────────────────────────────────────────────
    def competitive_landscape_4hop(self, target_client: str) -> list:
        """
        4-hop traversal: Client → Segment → Competitors → Won Clients → Pain Points

        Args:
            target_client: Name of the client (e.g., 'TechCorp')

        Returns:
            List of dicts with: competitor, clients_won, pain_points, win_count
        """
        query = """
        MATCH (target:Client {name: $name})
          -[:OPERATES_IN]->(seg:MarketSegment)
          <-[:COMPETES_IN]-(comp:Competitor)
          -[:WON_CLIENT]->(stolen:Client)
          -[:HAD_PAIN_POINT]->(pain:PainPoint)
        RETURN comp.name            AS competitor,
               collect(DISTINCT stolen.name)      AS clients_won,
               collect(DISTINCT pain.description)  AS pain_points,
               count(DISTINCT stolen)              AS win_count
        ORDER BY win_count DESC
        """
        return self._run(query, {'name': target_client})

    # ─────────────────────────────────────────────────────────────
    # QUERY 2: Relationship Strength — Who Knows Someone?
    # ─────────────────────────────────────────────────────────────
    # Finds consultants in YOUR firm who have direct relationships
    # at the target client, and traces their past successful deals.
    #
    # This answers: "Who should we put on the pitch team?"
    # ─────────────────────────────────────────────────────────────
    def relationship_map(self, target_client: str) -> list:
        """
        Find consultants with connections at the target client
        and their track record of successful deals.

        Args:
            target_client: Name of the client (e.g., 'TechCorp')

        Returns:
            List of dicts with: consultant, level, technologies, deals
        """
        query = """
        MATCH (c:Client {name: $name})
          <-[:HAS_RELATIONSHIP_WITH]-(cons:Consultant)
        OPTIONAL MATCH (cons)<-[:DELIVERED_BY]-(deal:Deal {outcome: 'Won'})
          -[:SOLVED_WITH]->(tech:Technology)
        RETURN cons.name           AS consultant,
               cons.seniority      AS level,
               cons.specialization AS specialization,
               collect(DISTINCT tech.name)  AS technologies_delivered,
               count(DISTINCT deal)         AS successful_deals
        ORDER BY successful_deals DESC
        """
        return self._run(query, {'name': target_client})

    # ─────────────────────────────────────────────────────────────
    # QUERY 3: Technology Gap Analysis
    # ─────────────────────────────────────────────────────────────
    # What technologies do competitors use that we haven't
    # delivered in any of our won deals?
    #
    # This reveals capability gaps to address in our pitch.
    # ─────────────────────────────────────────────────────────────
    def technology_gap_analysis(self, target_client: str) -> list:
        """
        Find technologies competitors use that we haven't delivered.

        Args:
            target_client: Name of the client (e.g., 'TechCorp')

        Returns:
            List of dicts with: competitor, technology_gap, category
        """
        query = """
        MATCH (comp:Competitor)-[:COMPETES_IN]->(seg:MarketSegment)
          <-[:OPERATES_IN]-(target:Client {name: $name})
        MATCH (comp)-[:USES_TECHNOLOGY]->(tech:Technology)
        WHERE NOT EXISTS {
          MATCH (:Deal {outcome: 'Won'})-[:SOLVED_WITH]->(tech)
        }
        RETURN comp.name     AS competitor,
               tech.name     AS technology_gap,
               tech.category AS category
        ORDER BY comp.name
        """
        return self._run(query, {'name': target_client})

    # ─────────────────────────────────────────────────────────────
    # QUERY 4: Win/Loss Pattern Analysis
    # ─────────────────────────────────────────────────────────────
    # Compare pain point categories across won vs lost clients.
    # Shows patterns: "We win when the pain is X, we lose when
    # the pain is Y."
    # ─────────────────────────────────────────────────────────────
    def win_loss_patterns(self) -> list:
        """
        Compare pain point categories for won vs lost clients.

        Returns:
            List of dicts with: category, outcome, frequency
        """
        query = """
        MATCH (won_client:Client)-[:HAD_PAIN_POINT]->(pain:PainPoint)
        WHERE EXISTS {
          MATCH (:Deal {outcome: 'Won'})-[:DELIVERED_BY]->(:Consultant)
            -[:HAS_RELATIONSHIP_WITH]->(won_client)
        }
        WITH pain.category AS category, 'Won' AS outcome, count(*) AS frequency
        RETURN category, outcome, frequency

        UNION

        MATCH (lost_client:Client)<-[:WON_CLIENT]-(:Competitor)
        MATCH (lost_client)-[:HAD_PAIN_POINT]->(pain:PainPoint)
        WITH pain.category AS category, 'Lost' AS outcome, count(*) AS frequency
        RETURN category, outcome, frequency
        """
        return self._run(query)

    # ─────────────────────────────────────────────────────────────
    # QUERY 5: Full Client Briefing (used by Hybrid route)
    # ─────────────────────────────────────────────────────────────
    # Gathers everything about a client into one result set:
    # their segment, competitors, pain points, and our contacts.
    # ─────────────────────────────────────────────────────────────
    def full_client_briefing(self, target_client: str) -> dict:
        """
        Gather all graph intelligence about a client into a
        structured briefing dictionary.

        Args:
            target_client: Name of the client (e.g., 'TechCorp')

        Returns:
            Dict with keys: competitive_landscape, relationship_map,
                           technology_gaps, win_loss_patterns
        """
        return {
            'competitive_landscape': self.competitive_landscape_4hop(target_client),
            'relationship_map': self.relationship_map(target_client),
            'technology_gaps': self.technology_gap_analysis(target_client),
            'win_loss_patterns': self.win_loss_patterns(),
        }


# ── Quick Test ──────────────────────────────────────────────────
if __name__ == '__main__':
    print("Testing Graph Queries against Neo4j...\n")
    gq = GraphQueries()

    print("=" * 60)
    print("QUERY 1: 4-Hop Competitive Landscape for TechCorp")
    print("=" * 60)
    results = gq.competitive_landscape_4hop('TechCorp')
    if results:
        for r in results:
            print(f"  Competitor: {r['competitor']}")
            print(f"  Clients Won: {r['clients_won']}")
            print(f"  Pain Points: {r['pain_points']}")
            print(f"  Win Count: {r['win_count']}")
            print()
    else:
        print("  No results found (check if data is seeded)")

    print("=" * 60)
    print("QUERY 2: Relationship Map for TechCorp")
    print("=" * 60)
    results = gq.relationship_map('TechCorp')
    for r in results:
        print(f"  {r['consultant']} ({r['level']}) — {r['successful_deals']} won deals")
        print(f"    Technologies: {r['technologies_delivered']}")
        print()

    print("=" * 60)
    print("QUERY 3: Technology Gap Analysis for TechCorp")
    print("=" * 60)
    results = gq.technology_gap_analysis('TechCorp')
    for r in results:
        print(f"  {r['competitor']} uses {r['technology_gap']} ({r['category']}) — we don't")

    print()
    print("=" * 60)
    print("QUERY 4: Win/Loss Patterns")
    print("=" * 60)
    results = gq.win_loss_patterns()
    for r in results:
        icon = "+" if r['outcome'] == 'Won' else "-"
        print(f"  [{icon}] {r['category']}: {r['outcome']} ({r['frequency']}x)")

    gq.close()
    print("\nAll queries executed successfully!")

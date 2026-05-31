"""
seed_neo4j.py — Populate Neo4j with Synthetic Competitive Intelligence Data
=============================================================================

WHAT THIS SCRIPT DOES:
1. Connects to your Neo4j instance (local or Neo4j Aura cloud)
2. Runs the schema constraints/indexes (from schema.cypher)
3. Creates nodes: Competitors, Clients, Market Segments, Pain Points,
   Technologies, Consultants, and Deals
4. Creates relationships between all of them

AFTER RUNNING THIS, your graph will look like:

    Competitor ──COMPETES_IN──> MarketSegment <──OPERATES_IN── Client
        │                                                        │
        └──WON_CLIENT──> Client ──HAD_PAIN_POINT──> PainPoint   │
                                                                 │
    Consultant ──HAS_RELATIONSHIP_WITH──> Client                 │
        │                                                        │
        └──DELIVERED_BY── Deal ──SOLVED_WITH──> Technology       │

KEY CONCEPTS:
- MERGE = "create if it doesn't exist" (idempotent — safe to run multiple times)
- Each relationship is a directed edge with a label (e.g., :WON_CLIENT)
- Parameters ($name, $n) prevent Cypher injection and improve performance
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

# ── Synthetic Data ───────────────────────────────────────────────

COMPETITORS = [
    {'name': 'McKinsey Digital', 'focus': ['Cloud Strategy', 'Digital Transformation']},
    {'name': 'Accenture', 'focus': ['Data & AI', 'Cloud Migration']},
    {'name': 'Deloitte Tech', 'focus': ['Cybersecurity', 'Cloud Migration']},
    {'name': 'ThoughtWorks', 'focus': ['Platform Engineering', 'DevOps']},
    {'name': 'EPAM', 'focus': ['Product Development', 'Cloud Native']},
]

CLIENTS = [
    {'name': 'TechCorp', 'industry': 'Cloud Migration', 'revenue': '500M', 'region': 'North America'},
    {'name': 'RetailGiant', 'industry': 'Digital Transformation', 'revenue': '2B', 'region': 'Europe'},
    {'name': 'FinanceHub', 'industry': 'Data & AI', 'revenue': '800M', 'region': 'APAC'},
    {'name': 'HealthSys', 'industry': 'Cloud Migration', 'revenue': '300M', 'region': 'North America'},
    {'name': 'ManuCo', 'industry': 'Cybersecurity', 'revenue': '1.2B', 'region': 'Europe'},
]

SEGMENTS = ['Cloud Migration', 'Data & AI', 'Digital Transformation', 'Cybersecurity']

PAIN_POINTS = [
    {'description': 'Legacy system integration taking too long', 'category': 'Integration', 'severity': 'High'},
    {'description': 'Data silos preventing real-time decisions', 'category': 'Data', 'severity': 'Critical'},
    {'description': 'High infrastructure cost with no scalability', 'category': 'Cost', 'severity': 'High'},
    {'description': 'Lack of engineering talent for cloud native', 'category': 'Talent', 'severity': 'Medium'},
    {'description': 'Compliance and data residency concerns', 'category': 'Compliance', 'severity': 'Critical'},
]

TECHNOLOGIES = [
    {'name': 'Kubernetes', 'category': 'Infrastructure'},
    {'name': 'Kafka', 'category': 'Data Streaming'},
    {'name': 'Terraform', 'category': 'IaC'},
    {'name': 'Spark', 'category': 'Data Processing'},
    {'name': 'dbt', 'category': 'Data Transformation'},
    {'name': 'Neo4j', 'category': 'Graph Database'},
    {'name': 'React', 'category': 'Frontend'},
]

CONSULTANTS = [
    {'name': 'Alice Chen', 'seniority': 'Partner', 'specialization': 'Cloud Strategy'},
    {'name': 'Bob Martinez', 'seniority': 'Director', 'specialization': 'Data & AI'},
    {'name': 'Carol Singh', 'seniority': 'Manager', 'specialization': 'Digital Transformation'},
    {'name': 'David Kim', 'seniority': 'Senior Consultant', 'specialization': 'DevOps'},
]

DEALS = [
    {'id': 'DEAL-001', 'value': '12M', 'year': 2024, 'outcome': 'Won', 'duration': 18,
     'client': 'TechCorp', 'consultant': 'Alice Chen', 'tech': ['Kubernetes', 'Terraform']},
    {'id': 'DEAL-002', 'value': '8M', 'year': 2023, 'outcome': 'Won', 'duration': 12,
     'client': 'ManuCo', 'consultant': 'Bob Martinez', 'tech': ['Kafka', 'Spark']},
    {'id': 'DEAL-003', 'value': '15M', 'year': 2024, 'outcome': 'Lost', 'duration': 0,
     'client': 'RetailGiant', 'consultant': 'Carol Singh', 'tech': []},
    {'id': 'DEAL-004', 'value': '6M', 'year': 2023, 'outcome': 'Won', 'duration': 9,
     'client': 'HealthSys', 'consultant': 'David Kim', 'tech': ['Kubernetes', 'dbt']},
]


def seed(driver):
    """Populate the Neo4j graph with all synthetic data."""
    with driver.session() as s:

        # ── Step 1: Run schema constraints ──────────────────────
        print("[1/11] Creating schema constraints and indexes...")
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'graph', 'schema.cypher')
        with open(schema_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('//'):
                    try:
                        s.run(line)
                    except Exception as e:
                        # Constraints may already exist — that's fine
                        print(f"  SKIP (may already exist): {str(e)[:80]}")

        # ── Step 2: Create Market Segments ──────────────────────
        print("\n[2/11] Creating Market Segments...")
        for seg in SEGMENTS:
            s.run('MERGE (m:MarketSegment {name: $n})', n=seg)
            print(f"  * {seg}")

        # ── Step 3: Create Competitors + link to segments ───────
        print("\n[3/11] Creating Competitors...")
        for comp in COMPETITORS:
            s.run(
                'MERGE (c:Competitor {name: $n}) SET c.focus_areas = $f',
                n=comp['name'], f=comp['focus']
            )
            # Each competitor COMPETES_IN their focus area segments
            for focus in comp['focus']:
                if focus in SEGMENTS:
                    s.run('''
                        MATCH (c:Competitor {name: $c}), (m:MarketSegment {name: $m})
                        MERGE (c)-[:COMPETES_IN]->(m)
                    ''', c=comp['name'], m=focus)
            print(f"  * {comp['name']} -> {comp['focus']}")

        # ── Step 4: Create Clients + link to segments + pain points ──
        print("\n[4/11] Creating Clients and Pain Points...")
        for i, client in enumerate(CLIENTS):
            s.run(
                'MERGE (c:Client {name: $n}) SET c.industry = $ind, c.annual_revenue = $rev, c.region = $reg',
                n=client['name'], ind=client['industry'],
                rev=client['revenue'], reg=client['region']
            )
            # Client OPERATES_IN their industry segment
            s.run('''
                MATCH (c:Client {name: $c}), (m:MarketSegment {name: $m})
                MERGE (c)-[:OPERATES_IN]->(m)
            ''', c=client['name'], m=client['industry'])

            # Each client has a pain point
            pain = PAIN_POINTS[i % len(PAIN_POINTS)]
            s.run(
                'MERGE (p:PainPoint {description: $d}) SET p.category = $cat, p.severity = $sev',
                d=pain['description'], cat=pain['category'], sev=pain['severity']
            )
            s.run('''
                MATCH (c:Client {name: $c}), (p:PainPoint {description: $d})
                MERGE (c)-[:HAD_PAIN_POINT]->(p)
            ''', c=client['name'], d=pain['description'])
            print(f"  * {client['name']} ({client['industry']}) -> Pain: {pain['description'][:40]}...")

        # ── Step 5: Create Technologies ─────────────────────────
        print("\n[5/11] Creating Technologies...")
        for tech in TECHNOLOGIES:
            s.run(
                'MERGE (t:Technology {name: $n}) SET t.category = $cat',
                n=tech['name'], cat=tech['category']
            )
            print(f"  * {tech['name']} ({tech['category']})")

        # ── Step 6: Competitor → Technology relationships ───────
        print("\n[6/11] Linking Competitors to Technologies...")
        comp_tech = {
            'McKinsey Digital': ['Kubernetes', 'Terraform', 'React'],
            'Accenture': ['Kafka', 'Spark', 'Kubernetes'],
            'Deloitte Tech': ['Terraform', 'Neo4j'],
            'ThoughtWorks': ['Kubernetes', 'Kafka', 'dbt'],
            'EPAM': ['React', 'Kubernetes', 'Spark'],
        }
        for comp_name, techs in comp_tech.items():
            for tech_name in techs:
                s.run('''
                    MATCH (c:Competitor {name: $c}), (t:Technology {name: $t})
                    MERGE (c)-[:USES_TECHNOLOGY]->(t)
                ''', c=comp_name, t=tech_name)
            print(f"  * {comp_name} -> {techs}")

        # ── Step 7: Competitors WON some clients ────────────────
        print("\n[7/11] Creating Competitor Win relationships...")
        wins = [
            ('McKinsey Digital', 'RetailGiant'),
            ('Accenture', 'FinanceHub'),
            ('ThoughtWorks', 'HealthSys'),
            ('Accenture', 'TechCorp'),       # Accenture also won TechCorp
        ]
        for comp_name, client_name in wins:
            s.run('''
                MATCH (c:Competitor {name: $c}), (cl:Client {name: $cl})
                MERGE (c)-[:WON_CLIENT]->(cl)
            ''', c=comp_name, cl=client_name)
            # Also create the reverse: Client LOST_TO Competitor
            s.run('''
                MATCH (cl:Client {name: $cl}), (c:Competitor {name: $c})
                MERGE (cl)-[:LOST_TO]->(c)
            ''', cl=client_name, c=comp_name)
            print(f"  * {comp_name} won {client_name}")

        # ── Step 8: Create Consultants ──────────────────────────
        print("\n[8/11] Creating Consultants...")
        for cons in CONSULTANTS:
            s.run(
                'MERGE (c:Consultant {name: $n}) SET c.seniority = $s, c.specialization = $sp',
                n=cons['name'], s=cons['seniority'], sp=cons['specialization']
            )
            print(f"  * {cons['name']} ({cons['seniority']})")

        # ── Step 9: Consultant relationships with clients ───────
        print("\n[9/11] Creating Consultant <-> Client relationships...")
        relationships = [
            ('Alice Chen', 'TechCorp'),
            ('Alice Chen', 'ManuCo'),
            ('Bob Martinez', 'FinanceHub'),
            ('Bob Martinez', 'TechCorp'),
            ('Carol Singh', 'RetailGiant'),
            ('David Kim', 'HealthSys'),
            ('David Kim', 'TechCorp'),
        ]
        for cons_name, client_name in relationships:
            s.run('''
                MATCH (cons:Consultant {name: $cons}), (c:Client {name: $c})
                MERGE (cons)-[:HAS_RELATIONSHIP_WITH]->(c)
            ''', cons=cons_name, c=client_name)
            print(f"  * {cons_name} knows someone at {client_name}")

        # ── Step 10: Create Deals + wire relationships ──────────
        print("\n[10/11] Creating Deals...")
        for deal in DEALS:
            s.run('''
                MERGE (d:Deal {deal_id: $id})
                SET d.value = $val, d.year_closed = $yr,
                    d.outcome = $out, d.duration_months = $dur
            ''', id=deal['id'], val=deal['value'],
                yr=deal['year'], out=deal['outcome'], dur=deal['duration'])

            # Deal DELIVERED_BY Consultant
            s.run('''
                MATCH (d:Deal {deal_id: $id}), (cons:Consultant {name: $cons})
                MERGE (d)-[:DELIVERED_BY]->(cons)
            ''', id=deal['id'], cons=deal['consultant'])

            # Deal SOLVED_WITH Technology
            for tech_name in deal['tech']:
                s.run('''
                    MATCH (d:Deal {deal_id: $id}), (t:Technology {name: $t})
                    MERGE (d)-[:SOLVED_WITH]->(t)
                ''', id=deal['id'], t=tech_name)

            status = "[WON]" if deal['outcome'] == 'Won' else "[LOST]"
            print(f"  {status} {deal['id']}: ${deal['value']} with {deal['client']} ({deal['outcome']})")

        # ── Step 11: Pain Points REFERENCED_IN Market Segments ──
        print("\n[11/11] Linking Pain Points to Market Segments...")
        pain_segment_links = [
            ('Legacy system integration taking too long', 'Cloud Migration'),
            ('Data silos preventing real-time decisions', 'Data & AI'),
            ('High infrastructure cost with no scalability', 'Cloud Migration'),
            ('Lack of engineering talent for cloud native', 'Digital Transformation'),
            ('Compliance and data residency concerns', 'Cybersecurity'),
        ]
        for pain_desc, seg_name in pain_segment_links:
            s.run('''
                MATCH (p:PainPoint {description: $p}), (m:MarketSegment {name: $m})
                MERGE (p)-[:REFERENCED_IN]->(m)
            ''', p=pain_desc, m=seg_name)
            print(f"  * '{pain_desc[:40]}...' -> {seg_name}")


def print_summary(driver):
    """Print a summary of what's in the graph."""
    with driver.session() as s:
        print("\n" + "=" * 60)
        print("GRAPH SUMMARY")
        print("=" * 60)
        result = s.run("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"  {record['label']:20s} -> {record['count']} nodes")

        result = s.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY count DESC
        """)
        print("\n  Relationships:")
        for record in result:
            print(f"  {record['type']:25s} -> {record['count']} edges")
        print("=" * 60)


if __name__ == '__main__':
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password123')

    print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Verify connection
    driver.verify_connectivity()
    print("Connected!\n")

    seed(driver)
    print_summary(driver)

    driver.close()
    print("\nGraph seeded successfully!")
    print("  If using Neo4j Aura: check your instance at https://console.neo4j.io")
    print("  If using local Neo4j: open http://localhost:7474 to explore.")

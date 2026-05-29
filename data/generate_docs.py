"""
generate_docs.py — Create Synthetic Research Documents for the RAG Layer
=========================================================================

WHAT THIS DOES:
Creates realistic .txt documents that simulate what a consulting firm
would have in their research library:
  - Market research reports (Gartner, Forrester style)
  - Competitor news articles
  - Industry trend analysis
  - Past engagement summaries

WHY SYNTHETIC DATA?
For a POC, we don't need real data. These documents are carefully
written to contain keywords and facts that the RAG system will
retrieve when asked relevant questions.

VANILLA RAG CONCEPT:
These documents will be:
  1. LOADED from the filesystem
  2. SPLIT into chunks (smaller pieces of text)
  3. EMBEDDED into vectors (numbers that capture meaning)
  4. STORED in FAISS (a vector database)
  5. RETRIEVED when a question is semantically similar

The key insight: RAG finds documents by MEANING, not keywords.
"What are cloud trends?" matches a document about "cloud migration
market projections" even though the exact words differ.
"""

import os


DOCUMENTS = {
    'gartner_cloud_2025.txt': """Gartner Market Report: Cloud Consulting Services 2025

The cloud consulting market is projected to reach $650B by 2026, representing a 23% compound
annual growth rate. This makes it one of the fastest-growing segments in the IT services industry.

Key Trends Identified:

1. FinOps Adoption: 78% of enterprises plan to implement FinOps practices by 2026.
   Cloud cost optimization has become a board-level priority, with organizations spending
   an average of 35% more than budgeted on cloud infrastructure.

2. Multi-Cloud Governance: Organizations are moving from single-cloud to multi-cloud
   strategies. AWS, Azure, and GCP adoption is increasingly simultaneous rather than
   exclusive. Governance frameworks are becoming essential.

3. AI-Native Infrastructure: The rise of GenAI workloads is driving demand for
   GPU-optimized cloud architectures. Consulting firms that can advise on AI
   infrastructure positioning are winning disproportionate market share.

4. Legacy Migration Pain: 67% of organizations cite integration complexity as the
   primary barrier to cloud adoption. Legacy system modernization engagements
   represent the largest single category of cloud consulting revenue.

5. Sustainability Mandates: Green cloud strategies are emerging as a differentiator.
   European clients in particular are requiring carbon-neutral cloud architectures.

Market Leaders: Accenture, Deloitte, and McKinsey Digital continue to lead in cloud
consulting revenue. However, boutique firms specializing in cloud-native architectures
(ThoughtWorks, EPAM) are gaining share in the mid-market segment.
""",

    'competitor_accenture_news.txt': """Accenture Technology News — Q1 2025 Summary

EXPANSION: Accenture announced a major expansion of its Data & AI practice, hiring
5,000 cloud engineers across APAC. This represents a 40% increase in their regional
technical capacity and signals aggressive growth plans in the Asia-Pacific market.

NEW SERVICE LAUNCH: The firm launched a new managed cloud service called "CloudBridge"
targeting mid-market financial services firms. CloudBridge offers a fixed-price
migration package with guaranteed timelines — a direct challenge to traditional
time-and-materials consulting models.

KEY WIN: Accenture secured a $40M digital transformation engagement with a leading
European bank, displacing an incumbent vendor. The deal includes cloud migration,
data platform modernization, and AI-powered risk analytics. Industry sources suggest
the incumbent lost due to slow delivery pace and lack of AI capabilities.

PARTNERSHIP: Accenture deepened its partnership with Google Cloud, becoming the first
consulting firm to achieve "AI Ready" certification. This positions them strongly
for the growing GenAI consulting market.

ANALYST COMMENTARY: "Accenture is executing a land-and-expand strategy in financial
services. Their CloudBridge offering lowers the entry barrier, and they upsell to
larger transformation programs once inside." — Forrester Research
""",

    'competitor_mckinsey_digital.txt': """McKinsey Digital — Market Intelligence Brief

STRATEGY SHIFT: McKinsey Digital has pivoted from pure strategy consulting to
hands-on implementation. Their "McKinsey Build" division now accounts for 30%
of digital revenue, up from 10% three years ago.

TALENT ACQUISITION: The firm acquired a 200-person cloud engineering boutique
in Berlin, adding Kubernetes and Terraform expertise. This addresses their
historical weakness in technical implementation.

PRICING: McKinsey's day rates remain the highest in the market ($8,000-$15,000
per consultant per day), but they are introducing outcome-based pricing for
cloud migration engagements to compete with lower-cost rivals.

FOCUS AREAS: McKinsey Digital is concentrating on three verticals:
  1. Financial Services — Cloud risk and compliance frameworks
  2. Healthcare — Clinical data platform modernization
  3. Retail — AI-powered supply chain optimization

WEAKNESS: Multiple industry sources report that McKinsey struggles with
sustained technical delivery beyond the strategy phase. Clients report
high consultant turnover on long-duration implementation projects.
""",

    'market_fintech_trends.txt': """Fintech Digital Transformation — Industry Analysis 2025

Financial services firms are accelerating cloud migration driven by three forces:
regulatory pressure, cost optimization mandates, and competitive threat from
digital-native challengers.

DEAL DYNAMICS:
- Average consulting engagement in fintech: 18 months
- Typical deal value: $8-15M for mid-market, $25-50M for enterprise
- Key decision makers: CDOs and CTOs drive vendor selection
- CFOs increasingly involved, demanding measurable ROI within 12 months

PAIN POINTS REPORTED BY FINTECH CLIENTS:
- Data silos preventing real-time decision making (cited by 73% of respondents)
- Regulatory compliance complexity slowing innovation (68%)
- Legacy system integration costs exceeding projections by 2-3x (62%)
- Difficulty retaining cloud engineering talent (58%)
- Security and data residency concerns blocking cloud adoption (55%)

COMPETITIVE LANDSCAPE:
Accenture leads in fintech consulting market share, followed by Deloitte and
McKinsey Digital. Boutique firms like ThoughtWorks are gaining traction with
clients seeking engineering-led approaches over strategy-led ones.

OPPORTUNITY: Mid-market fintech firms ($200M-$1B revenue) are underserved.
Large consultancies focus on enterprise clients, creating a gap for firms
that can offer senior talent at mid-market pricing.
""",

    'industry_healthcare_cloud.txt': """Healthcare Cloud Migration — Strategic Overview

The healthcare industry is undergoing a massive shift to cloud-based
infrastructure, driven by interoperability mandates, telehealth expansion,
and the need for AI-powered clinical decision support.

MARKET SIZE: Healthcare cloud consulting is a $45B market growing at 28% CAGR.

KEY CHALLENGES:
- HIPAA and data residency requirements create unique cloud architecture needs
- Electronic Health Record (EHR) systems are deeply embedded and resistant to migration
- Clinical workflows cannot tolerate downtime — zero-disruption migration is essential
- Data integration across hospital networks requires sophisticated ETL pipelines

COMPETITOR ACTIVITY:
- Deloitte Tech has a dedicated healthcare cloud practice with 2,000+ consultants
- ThoughtWorks won three major hospital network migrations in 2024
- EPAM is building a healthcare-specific cloud platform called "HealthCloud"
- Accenture partnered with Epic Systems for EHR-to-cloud migration tooling

TECHNOLOGY TRENDS:
- Kubernetes adoption in healthcare jumped from 15% to 45% in two years
- FHIR API standards are enabling cloud-based data exchange
- AI diagnostics require GPU-intensive cloud infrastructure
- Edge computing for real-time patient monitoring

RECOMMENDATION: Firms entering healthcare cloud consulting should invest in
HIPAA compliance expertise and EHR integration capabilities. The barrier to
entry is high, but margins exceed general cloud consulting by 20%.
""",
}


def generate():
    """Generate all synthetic documents."""
    docs_dir = os.path.join(os.path.dirname(__file__), 'documents')
    os.makedirs(docs_dir, exist_ok=True)

    print("Generating synthetic research documents...\n")
    for filename, content in DOCUMENTS.items():
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        word_count = len(content.split())
        print(f"  [+] {filename} ({word_count} words)")

    print(f"\nGenerated {len(DOCUMENTS)} documents in {docs_dir}")
    print("\nThese documents will be embedded into FAISS in the next step.")
    print("The RAG system will search these by MEANING, not keywords.")


if __name__ == '__main__':
    generate()

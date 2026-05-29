// ============================================================
// Competitive Intelligence Graph — Schema Setup
// ============================================================
// Run these commands ONCE in the Neo4j Browser (http://localhost:7474)
// or execute via the seed_neo4j.py script.
//
// WHAT THIS DOES:
// 1. Creates UNIQUENESS CONSTRAINTS — ensures no duplicate nodes
//    (e.g., you can't accidentally create two "Accenture" competitors)
// 2. Creates PERFORMANCE INDEXES — makes queries fast
//    (without these, every query scans ALL nodes)
// ============================================================

// --- Uniqueness Constraints ---
// These serve two purposes:
//   a) Data integrity: prevents duplicate nodes
//   b) Performance: constraints automatically create an index
//
// Think of it like a PRIMARY KEY in SQL, but for graph nodes.

CREATE CONSTRAINT IF NOT EXISTS FOR (c:Competitor)    REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Client)        REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (m:MarketSegment) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (p:PainPoint)     REQUIRE p.description IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology)    REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Consultant)    REQUIRE c.name IS UNIQUE;

// --- Performance Indexes ---
// These speed up queries that filter by these properties.
// Without indexes, Neo4j does a full scan of all nodes of that label.
//
// Example: When we query "MATCH (d:Deal {outcome: 'Won'})",
// the index on Deal.outcome means Neo4j jumps straight to
// won deals instead of checking every deal.

CREATE INDEX IF NOT EXISTS FOR (c:Client)     ON (c.industry);
CREATE INDEX IF NOT EXISTS FOR (c:Competitor) ON (c.name);
CREATE INDEX IF NOT EXISTS FOR (d:Deal)       ON (d.outcome);
CREATE INDEX IF NOT EXISTS FOR (d:Deal)       ON (d.year_closed);

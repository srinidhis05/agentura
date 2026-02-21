// Aspora Knowledge Graph Schema (Neo4j)
// Connects entities across domains for cross-domain reasoning

// ============================================
// NODES
// ============================================

// Users (shared across all domains)
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;

// Wealth domain
CREATE CONSTRAINT portfolio_id IF NOT EXISTS FOR (p:Portfolio) REQUIRE p.portfolio_id IS UNIQUE;
CREATE CONSTRAINT goal_id IF NOT EXISTS FOR (g:Goal) REQUIRE g.goal_id IS UNIQUE;
CREATE CONSTRAINT instrument_id IF NOT EXISTS FOR (i:Instrument) REQUIRE i.isin IS UNIQUE;

// FinCrime domain
CREATE CONSTRAINT alert_id IF NOT EXISTS FOR (a:Alert) REQUIRE a.event_id IS UNIQUE;
CREATE CONSTRAINT beneficiary_id IF NOT EXISTS FOR (b:Beneficiary) REQUIRE b.beneficiary_id IS UNIQUE;
CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:InvestigationCase) REQUIRE c.case_id IS UNIQUE;

// Fraud domain
CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (r:FraudRule) REQUIRE r.rule_name IS UNIQUE;
CREATE CONSTRAINT simulation_id IF NOT EXISTS FOR (s:Simulation) REQUIRE s.simulation_id IS UNIQUE;

// Skill executions (shared)
CREATE CONSTRAINT execution_id IF NOT EXISTS FOR (e:SkillExecution) REQUIRE e.execution_id IS UNIQUE;
CREATE CONSTRAINT correction_id IF NOT EXISTS FOR (cr:Correction) REQUIRE cr.correction_id IS UNIQUE;

// ============================================
// RELATIONSHIPS
// ============================================

// User → Portfolio (Wealth)
// (:User)-[:OWNS]->(:Portfolio)
// (:Portfolio)-[:CONTAINS]->(:Instrument)
// (:User)-[:HAS_GOAL]->(:Goal)
// (:Goal)-[:FUNDED_BY]->(:Instrument)

// User → Transactions → Beneficiaries (FinCrime)
// (:User)-[:SENT_TO]->(:Beneficiary)
// (:User)-[:TRIGGERED]->(:Alert)
// (:Alert)-[:INVOLVES]->(:Beneficiary)
// (:Alert)-[:INVESTIGATED_IN]->(:InvestigationCase)
// (:Beneficiary)-[:RECEIVED_FROM]->(:User)  -- CRITICAL: cross-user link

// Fraud Rules → Simulations
// (:FraudRule)-[:SIMULATED_IN]->(:Simulation)
// (:Simulation)-[:FLAGGED]->(:Transaction)

// Skill Executions → Corrections → Reflexion
// (:SkillExecution)-[:PRODUCED]->(:Output)
// (:SkillExecution)-[:CORRECTED_BY]->(:Correction)
// (:Correction)-[:GENERATED]->(:ReflexionEntry)
// (:Correction)-[:GENERATED]->(:RegressionTest)

// ============================================
// CROSS-DOMAIN QUERIES (the power of GraphRAG)
// ============================================

// Query 1: "Is this wealth customer flagged in fincrime?"
// MATCH (u:User {user_id: $uid})-[:TRIGGERED]->(a:Alert)
// WHERE a.severity = 'Critical' AND a.disposition != 'Approved'
// RETURN a.event_id, a.trm_rule_tag, a.composite_risk_score

// Query 2: "Which beneficiaries receive from multiple users?" (money mule detection)
// MATCH (b:Beneficiary)<-[:SENT_TO]-(u:User)
// WITH b, COUNT(DISTINCT u) AS user_count, COLLECT(u.user_id) AS users
// WHERE user_count >= 3
// RETURN b.beneficiary_id, b.name, user_count, users

// Query 3: "What corrections improved this skill?" (learning lineage)
// MATCH (s:Skill {name: 'fincrime/triage-alerts'})<-[:FOR_SKILL]-(e:SkillExecution)
//       -[:CORRECTED_BY]->(c:Correction)-[:GENERATED]->(r:ReflexionEntry)
// RETURN c.user_correction, r.rule, r.confidence
// ORDER BY e.timestamp DESC

// Query 4: "Cross-domain risk: user with fincrime alerts AND large wealth allocation"
// MATCH (u:User)-[:TRIGGERED]->(a:Alert {severity: 'Critical'})
// MATCH (u)-[:OWNS]->(p:Portfolio)
// WHERE p.total_value_inr > 5000000
// RETURN u.user_id, COUNT(a) AS critical_alerts, p.total_value_inr
// ORDER BY critical_alerts DESC

// ============================================
// SAMPLE DATA
// ============================================

// Users
CREATE (u1:User {user_id: 'USR-NRI-2847', name: 'Rahul Mehta', country: 'AE', nationality: 'IN'});
CREATE (u2:User {user_id: 'USR-38472', name: 'Amir Hassan', country: 'AE', nationality: 'AE'});
CREATE (u3:User {user_id: 'USR-29384', name: 'Fatima Al-Sayed', country: 'AE', nationality: 'AE'});

// Beneficiaries
CREATE (b1:Beneficiary {beneficiary_id: 'BEN-7832', name: 'Mohammed Al-Rashid', country: 'IN'});

// Cross-user link (money mule signal)
MATCH (u2:User {user_id: 'USR-38472'}), (b1:Beneficiary {beneficiary_id: 'BEN-7832'})
CREATE (u2)-[:SENT_TO {amount: 4999, currency: 'AED', date: '2026-02-15'}]->(b1);

MATCH (u3:User {user_id: 'USR-29384'}), (b1:Beneficiary {beneficiary_id: 'BEN-7832'})
CREATE (u3)-[:SENT_TO {amount: 3200, currency: 'AED', date: '2026-02-16'}]->(b1);

// Wealth user who is also in fincrime (cross-domain)
// This enables: "Before recommending allocation for USR-NRI-2847, check fincrime status"
MATCH (u1:User {user_id: 'USR-NRI-2847'})
CREATE (u1)-[:OWNS]->(:Portfolio {portfolio_id: 'PF-2847', total_value_inr: 3753141});

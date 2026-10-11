# ProvLens: Digital Media Provenance &amp; Forensics GraphRAG Platform

Based on # Data-Lineage---Data-Provinence

**ProvLens** is an auditable, graph-grounded digital media forensics web platform powered by **Neo4j**, **GraphRAG**, and **W3C PROV** lineage modeling.

The system tracks multi-stage media transformation pathways as association triplets `{i, T, o}`, detects tampering anomalies across high-dimensional containment hierarchies, and provides hallucination-free investigative intelligence for legal and judicial proceedings.

---

## Why ProvLens?

* **Prov** (Provenance): Complete, immutable historical lifecycle tracking from hardware capture sensors to judicial court exhibits.
* **Lens** (Forensic Lens): Multi-granular examination through Ibis containment hierarchies, allowing forensic examiners to zoom seamlessly from multi-gigabyte video containers down to individual suspicious frames.

---

## Key Capabilities

* **Grounded GraphRAG Assistant:** Executes hybrid vector and Cypher traversals using Neo4j to retrieve deterministic, multi-hop subgraphs over W3C PROV and containment paths before prompting the LLM, eliminating hallucinations in forensic chain-of-custody analysis.
* **Bidirectional Forensic Tracing:**  
  * **Backward Tracing (Root-Cause / 'Why-Provenance'):** Traverses upstream `:WAS_DERIVED_FROM` and `:USED` paths to identify original camera sensors, acquisition timestamps, and modifying software agents.
  * **Forward Tracing (Blast-Radius Analysis):** Tracks downstream outputs derived from compromised source frames to map error and tampering propagation across derivative publications.
* **Multi-Granular Containment Hierarchy (Ibis Model):** Prevents graph explosion over massive multimedia assets by nesting parent `:MediaContainer` files down to `:MediaSegment` and `:MediaFrame` subsets.
* **Vertical Judicial Alignment (JDFEG):** Bridges low-level bitstream forensics (hashes, codecs, offsets) to high-level legal models (`:LogicalEvidence`, `:CaseExhibit`).
* **Zero-Setup Simulation Fallback:** Built-in in-memory fallback graph engine allows immediate local exploration and testing without requiring an active Neo4j connection upfront.
* **Auditable Evidence Certificate Export:** Generates formal, downloadable chain-of-custody reports for judicial proceedings.

---

## Architectural Foundations

```
                          +------------------------+
                          |   :CaseExhibit         | (Conceptual Model)
                          +-----------^------------+
                                      | :REPRESENTS_CONCEPT
                          +-----------+------------+
                          |   :LogicalEvidence     | (Logical Model)
                          +-----------^------------+
                                      | :IMPLEMENTS_LOGICAL
  +-----------------------------------+------------------------------------+
  | Physical Lineage &amp; Containment (W3C PROV + Ibis Model)             |
  |                                                                        |
  |   (:MediaContainer:Entity)                                             |
  |              |                                                         |
  |              | :CONTAINS_DATA (Ibis Data Containment)                  |
  |              v                                                         |
  |       (:MediaFrame:Entity) ----[:USED]----&gt; (:Transform:Activity)   |
  |              ^                                   |                     |
  |              | :WAS_DERIVED_FROM                 | :WAS_ASSOCIATED_WITH|
  |              |                                   v                     |
  |       (:MediaFrame:Entity)                   (:Agent:SoftwareTool)     |
  +------------------------------------------------------------------------+

```

1. **W3C PROV Standard &amp; Association Triplets {i, T, o}:**Every processing step is represented as an association triplet relating input entities `i`, transformation actors `T`, and output entities `o`, attributed to software or human agents.
2. **Ibis Multi-Layer Containment:**  
  * **Data Containment:** Enforces child data points (frames) as strict subsets of containing parent files (containers).
  * **Operator Containment:** Structures granular edit tasks under overarching job sessions.
3. **Judicial Digital Forensic Evidence Graphs (JDFEGs):**Unifies digital forensic entities (hashes, IP addresses, files) with legal actors (plaintiff, defendant, complaints) to ensure judicial admissibility.

---

## Repository Structure

```
.
├── provlens-media-forensics.py   # Main Streamlit web application &amp; GraphRAG engine
├── requirements.txt              # Python package dependencies
├── provlens-README.md            # Architecture documentation &amp; setup guide
└── .streamlit/
    └── secrets.toml              # (Optional) Neo4j and OpenAI API credentials

```

---

## Quickstart (Local)

### 1\. Prerequisites

* Python 3.10+
* (Optional) Neo4j 5.x Database or Neo4j AuraDB instance
* (Optional) OpenAI API Key (for live LLM generation)

### 2\. Installation

Install the dependencies:

```
pip install streamlit neo4j openai

```

### 3\. Run Application

```
streamlit run provlens-media-forensics.py

```

Open `http://localhost:8501` in your browser.

* *Tip:* Click **'Seed Case'** in the sidebar to populate a complete CCTV tampering scenario and explore the features immediately.

# Technical Architecture: The 6 Roles of Neo4j in ProvLens

This specification details the foundational architecture of the **ProvLens** digital media forensics platform, detailing how **Neo4j** operates as the primary graph database, provenance engine, and retrieval substrate for verifiable digital media investigations.

---

## Executive Overview

In digital forensics and data lineage systems, lineage represents a specialized form of **why-provenance**, recording data origins, movements, and sequential transformations over time. Traditional relational or flat vector stores treat media files as isolated objects, creating severe vulnerabilities in legal and investigative domains:

* Inability to trace multi-hop transformation histories across editing pipelines.
* Vulnerability to generative AI hallucinations when analyzing chain of custody.
* Difficulty managing multi-gigabyte multimedia files without encountering graph explosion.

ProvLens resolves these challenges by using Neo4j to model data lineage natively as an **association graph**, where data containers act as vertices and processing steps act as connecting edges.

---

## 1\. W3C PROV Association Graph Modeling

The **W3C PROV** standard formalizes provenance through three structural primitives:

* **`:Entity`**: Physical or digital assets, including raw video containers (`:MediaContainer`) and individual video frames (`:MediaFrame`).
* **`:Activity`**: Processes, executions, or algorithmic operations that consume or generate entities.
* **`:Agent`**: Hardware recording devices (`:HardwareDevice`), automated software suites (`:SoftwareTool`), or human examiners (`:ForensicExaminer`) responsible for an activity.

```
(:Agent) &lt;--[:WAS_ASSOCIATED_WITH]-- (:Activity:Transform) --[:USED]--&gt; (:Entity:MediaFrame)
                                             |                                ^
                                   [:WAS_GENERATED_BY]                        | [:WAS_DERIVED_FROM]
                                             v                                |
                                    (:Entity:MediaFrame) ---------------------+

```

### Transformation Association Triplets {i, T, o}

Every processing step across operators is formalized as an association triplet `{i, T, o}`, where `i` denotes the input entity set, `T` denotes the transformation actor, and `o` denotes the output entity set:

* **Input Association (`i -&gt; T`)**: Materialized via `(:Activity)-[:USED]-&gt;(:Entity)`.
* **Output Generation (`T -&gt; o`)**: Materialized via `(:Entity)-[:WAS_GENERATED_BY]-&gt;(:Activity)`.
* **Derivation Linkage (`i -&gt; o`)**: Materialized via `(:Entity)-[:WAS_DERIVED_FROM]-&gt;(:Entity)`.

This representation guarantees strict accountability for every algorithmic modification applied to evidentiary assets.

---

## 2\. Multi-Layer Containment Hierarchy (The Ibis Model)

Unstructured multimedia assets account for approximately 90% of big data volumes. Tracking fine-grained transformations at every millisecond or pixel boundary creates an immense state space that causes graph explosion and degrades query performance.

ProvLens implements the **Ibis provenance model** in Neo4j to structure multi-granular containment across two distinct dimensions:

```
DATA CONTAINMENT                               OPERATOR CONTAINMENT
(:MediaContainer:Entity)                       (:PipelineJob:Activity)
       |                                                |
       | [:CONTAINS_DATA]                               | [:CONTAINS_OPERATOR]
       v                                                v
(:MediaSegment:Entity)                         (:Transform:Activity)
       |
       | [:CONTAINS_DATA]
       v
(:MediaFrame:Entity)

```

1. **Data Containment (`[:CONTAINS_DATA]`)**: Enforces that contained child data points are strict subsets of containing parent supersets. A parent video container (`:MediaContainer`) contains intermediate segments (`:MediaSegment`), which contain individual image frames (`:MediaFrame`). Examiners can perform coarse-grained file auditing and selectively drill down into granular frame nodes only when anomalies are flagged.
2. **Operator Containment (`[:CONTAINS_OPERATOR]`)**: Establishes that a contained child operator executes a discrete sub-task of an overarching parent operation. A parent pipeline session (`:PipelineJob`) contains fine-grained transformation tasks (`:Transform`), attributing overall supervisory responsibility to a forensic examiner while logging specific execution parameters to automated tools.

---

## 3\. Vertical Judicial Grounding (JDFEG Integration)

Enterprise data lineage encompasses two dimensions:

* **Horizontal Lineage**: The chronological path data traverses from origin sensors through downstream pipeline transformations.
* **Vertical Lineage**: The mapping of physical data assets upward across logical and conceptual models.

ProvLens incorporates **Judicial Digital Forensic Evidence Graphs (JDFEGs)**, partitioning graph vertices V = VE U VJ:

* **Digital Forensic Evidence Entities (VE)**: Physical files, frame offsets, SHA-256 cryptographic hashes, and perceptual hashes.
* **Judicial Entities (VJ)**: Court case filings, judicial roles (plaintiff, defendant, examining agent), and formal case exhibits.

```
                     (:CaseExhibit)          &lt;-- Conceptual Legal Model (VJ)
                            ^
                            | [:REPRESENTS_CONCEPT]
                     (:LogicalEvidence)      &lt;-- Logical Evidentiary Model (VJ)
                            ^
                            | [:IMPLEMENTS_LOGICAL]
                  (:MediaContainer:Entity)   &lt;-- Physical File Storage (VE)
                            |
                            | [:CONTAINS_DATA]
                            v
                    (:MediaFrame:Entity)     &lt;-- Granular Forensic Asset (VE)

```

Neo4j links these layers vertically:

* Physical container files link to logical evidence records via `[:IMPLEMENTS_LOGICAL]`.
* Logical evidence records link directly to official court exhibits via `[:REPRESENTS_CONCEPT]`.
* This vertical mapping ensures that bitstream-level tampering directly updates the legal admissibility status of corresponding court exhibits.

---

## 4\. Automated Multi-Hop Cypher Traversal Engines

Neo4j's Cypher graph engine powers five core forensic traversal queries:

### 4.1 Backward Tracing Query (Root-Cause "Why-Provenance")

Traces `:WAS_DERIVED_FROM` paths up to 10 hops upstream to identify the original hardware sensor and intermediate modifying tools:

```
MATCH path = (suspect:Entity {entity_id: $entity_id})-[:WAS_DERIVED_FROM*1..10]-&gt;(origin:Entity)
WHERE NOT (origin)-[:WAS_DERIVED_FROM]-&gt;()
OPTIONAL MATCH (suspect)-[:WAS_GENERATED_BY]-&gt;(act:Activity)-[:WAS_ASSOCIATED_WITH]-&gt;(agent:Agent)
OPTIONAL MATCH (origin)&lt;-[:CONTAINS_DATA]-(rootContainer:MediaContainer)
OPTIONAL MATCH (origin)-[:WAS_GENERATED_BY]-&gt;(:Activity)-[:WAS_ASSOCIATED_WITH]-&gt;(sensor:Agent)
RETURN
    suspect.entity_id AS suspect_id,
    suspect.frame_number AS suspect_frame,
    act.operation_type AS operation_applied,
    agent.name AS tool_or_agent,
    origin.entity_id AS upstream_source_id,
    rootContainer.file_name AS root_container,
    sensor.name AS root_sensor,
    suspect.phash_distance AS phash_divergence,
    length(path) AS hops;

```

### 4.2 Forward Tracing Query (Blast-Radius &amp; Compromise Propagation)

Maps downstream outputs produced by a compromised input, identifying all derived publications and legal exhibits:

```
MATCH path = (origin:Entity {entity_id: $entity_id})&lt;-[:WAS_DERIVED_FROM*1..10]-(downstream:Entity)
OPTIONAL MATCH (downstream)&lt;-[:CONTAINS_DATA]-(container:MediaContainer)
OPTIONAL MATCH (downstream)-[:WAS_GENERATED_BY]-&gt;(act:Activity)
RETURN
    origin.entity_id AS origin_id,
    downstream.entity_id AS compromised_derivative_id,
    labels(downstream) AS derivative_type,
    container.file_name AS derivative_container,
    act.operation_type AS operation,
    length(path) AS hops;

```

### 4.3 Multi-Granularity Zoom Query (Ibis Data Containment)

Navigates downward from high-level containers into child frames, returning perceptual hashes and tampering flags:

```
MATCH (container:MediaContainer {entity_id: $container_id})-[:CONTAINS_DATA]-&gt;(frame:Entity)
OPTIONAL MATCH (frame)-[:WAS_GENERATED_BY]-&gt;(act:Activity)-[:WAS_ASSOCIATED_WITH]-&gt;(ag:Agent)
RETURN
    frame.entity_id AS entity_id,
    frame.frame_number AS frame_number,
    frame.perceptual_hash AS phash,
    frame.tampering_flag AS tampered,
    frame.phash_distance AS phash_distance,
    act.operation_type AS operation,
    ag.name AS agent_name
ORDER BY frame.frame_number ASC;

```

### 4.4 Operator Containment Inspection

Extracts overarching pipeline jobs and reveals all contained child manipulation tasks, parameter configurations, and supervising personnel:

```
MATCH (job:PipelineJob)-[:CONTAINS_OPERATOR]-&gt;(task:Transform)
OPTIONAL MATCH (task)-[:WAS_ASSOCIATED_WITH]-&gt;(agent:Agent)
OPTIONAL MATCH (job)-[:WAS_ASSOCIATED_WITH]-&gt;(examiner:Agent)
RETURN
    job.job_name AS job_name,
    task.operation_type AS task_operation,
    task.parameters AS parameters,
    agent.name AS software_tool,
    examiner.name AS supervising_examiner;

```

### 4.5 Behavioral Anomaly Scanner

Identifies unexpected changes in entity attributes over time. Queries perceptual hash divergence distance to isolate synthetic manipulations:

```
MATCH (f:Entity:MediaFrame)
WHERE f.tampering_flag = true OR f.phash_distance &gt;= $threshold
MATCH (f)-[:WAS_GENERATED_BY]-&gt;(act:Activity)-[:WAS_ASSOCIATED_WITH]-&gt;(agent:Agent)
MATCH (f)&lt;-[:CONTAINS_DATA]-(container:MediaContainer)
RETURN
    f.entity_id AS entity_id,
    f.frame_number AS frame_number,
    f.phash_distance AS phash_distance,
    f.perceptual_hash AS phash,
    act.operation_type AS operation,
    agent.name AS agent,
    container.file_name AS container_file
ORDER BY f.phash_distance DESC;

```

---

## 5\. Hybrid GraphRAG Retrieval Pipeline

Standard vector-only RAG segments text into isolated chunks and retrieves them using approximate similarity. In high-stakes legal forensics, this introduces two critical vulnerabilities:

1. **Context Fragmentation**: Vector search cannot traverse multi-hop paths, missing upstream origin sensors and intermediate modifications.
2. **Generative Hallucinations**: Without verified relational constraints, LLMs fabricate plausible but nonexistent provenance connections.

```
User Query ---&gt; [Vector Index Search] ---&gt; Pinpoint Initial Entry Entities
                      +
                [Full-Text Index]
                      |
                      v
              [Cypher Graph Traversal] ---&gt; Extract Multi-Hop PROV Subgraph
                      |
                      v
              [Prompt Augmentation]   ---&gt; Ingest Verified Relational Context
                      |
                      v
              [LLM Synthesis]         ---&gt; Generate Hallucination-Free Audit Report

```

Neo4j resolves these limitations through **GraphRAG**:

* **Dual Indexing**: Pairs vector embeddings with full-text lexical indexes to locate candidate entry nodes accurately.
* **Deterministic Subgraph Retrieval**: Traverses explicit edges to pull connected nodes into a structured JSON context.
* **Grounded LLM Reasoning**: Supplies the structured subgraph directly to the LLM prompt with strict grounding directives, guaranteeing legally defensible outputs.

---

## 6\. Schema Integrity, Constraints, and Index Optimization

Neo4j enforces schema integrity and rapid lookup across millions of forensic nodes through declarative DDL statements:

```
// Uniqueness Constraints
CREATE CONSTRAINT unique_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE;
CREATE CONSTRAINT unique_agent_id IF NOT EXISTS FOR (ag:Agent) REQUIRE ag.agent_id IS UNIQUE;
CREATE CONSTRAINT unique_evidence_id IF NOT EXISTS FOR (l:LogicalEvidence) REQUIRE l.evidence_id IS UNIQUE;
CREATE CONSTRAINT unique_exhibit_id IF NOT EXISTS FOR (c:CaseExhibit) REQUIRE c.exhibit_id IS UNIQUE;

// Property Indexes
CREATE INDEX entity_hash_idx IF NOT EXISTS FOR (e:Entity) ON (e.sha256_hash);
CREATE INDEX entity_phash_idx IF NOT EXISTS FOR (e:Entity) ON (e.perceptual_hash);
CREATE INDEX activity_timestamp_idx IF NOT EXISTS FOR (a:Activity) ON (a.timestamp);

// Full-Text Index for Hybrid Search
CREATE FULLTEXT INDEX mediaFulltext IF NOT EXISTS
FOR (n:Entity) ON EACH [n.file_name, n.description, n.operation_type];

```

---

## Architectural Summary

| #     | Architectural Role               | Neo4j Implementation Primitives                                                                     | Forensic Outcome                                                                       |
| ----- | -------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **1** | **W3C PROV Modeling**            | Nodes (`:Entity`, `:Activity`, `:Agent`), Edges (`:USED`, `:WAS_GENERATED_BY`, `:WAS_DERIVED_FROM`) | Standardized, legally compliant chain-of-custody representation.                       |
| **2** | **Ibis Containment**             | Hierarchical edges (`[:CONTAINS_DATA]`, `[:CONTAINS_OPERATOR]`)                                     | Prevents graph explosion over massive multimedia assets.                               |
| **3** | **Vertical Lineage (JDFEG)**     | Bridging edges (`[:IMPLEMENTS_LOGICAL]`, `[:REPRESENTS_CONCEPT]`)                                   | Connects low-level file modifications directly to formal court exhibits.               |
| **4** | **Cypher Traversal Engines**     | Multi-hop pattern matching (`*1..10`), path filtering                                               | Enables root-cause attribution and blast-radius compromise mapping.                    |
| **5** | **Hybrid GraphRAG**              | Vector index + Full-text index + Cypher retrieval queries                                           | Replaces fragmented vector chunks with verified subgraphs to eliminate hallucinations. |
| **6** | **Schema Constraints &amp; Indexes** | Unique constraints, hash indexes, full-text indexes                                                 | Guarantees evidence integrity and provides sub-second query performance.               |

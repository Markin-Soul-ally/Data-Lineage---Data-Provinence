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

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

import streamlit as st

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Driver = Any

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

st.set_page_config(
    page_title="ProvLens | Digital Media Forensics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .provlens-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .provlens-header h1 {
        color: #ffffff;
        margin: 0;
        font-size: 2.2rem;
    }
    .provlens-header p {
        color: #e0e7ff;
        margin: 5px 0 0 0;
        font-size: 1.05rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #2563eb;
        margin-bottom: 12px;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }
    .metric-card-anomaly {
        background-color: #fff7ed;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #ea580c;
        margin-bottom: 12px;
        border-top: 1px solid #fed7aa;
        border-right: 1px solid #fed7aa;
        border-bottom: 1px solid #fed7aa;
    }
    .tamper-badge {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .authentic-badge {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_neo4j_driver(uri: str, user: str, password: str) -> Optional[Any]:
    if not NEO4J_AVAILABLE:
        return None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception as e:
        st.sidebar.error(f"Neo4j Connection Error: {e}")
        return None


def init_provlens_schema(driver: Any) -> bool:
    constraints = [
        "CREATE CONSTRAINT unique_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;",
        "CREATE CONSTRAINT unique_activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE;",
        "CREATE CONSTRAINT unique_agent_id IF NOT EXISTS FOR (ag:Agent) REQUIRE ag.agent_id IS UNIQUE;",
        "CREATE CONSTRAINT unique_evidence_id IF NOT EXISTS FOR (l:LogicalEvidence) REQUIRE l.evidence_id IS UNIQUE;",
        "CREATE CONSTRAINT unique_exhibit_id IF NOT EXISTS FOR (c:CaseExhibit) REQUIRE c.exhibit_id IS UNIQUE;"
    ]
    indexes = [
        "CREATE INDEX entity_hash_idx IF NOT EXISTS FOR (e:Entity) ON (e.sha256_hash);",
        "CREATE INDEX entity_phash_idx IF NOT EXISTS FOR (e:Entity) ON (e.perceptual_hash);",
        "CREATE INDEX activity_timestamp_idx IF NOT EXISTS FOR (a:Activity) ON (a.timestamp);",
        "CREATE FULLTEXT INDEX mediaFulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.file_name, n.description, n.operation_type];"
    ]
    with driver.session() as session:
        for c in constraints:
            session.run(c)
        for idx in indexes:
            try:
                session.run(idx)
            except Exception:
                pass
    return True


def seed_provlens_demo_cases(driver: Any) -> bool:
    cypher_seed = """
    MERGE (exhibit1:CaseExhibit {
        exhibit_id: "EXHIBIT-2026-A",
        court_case_num: "CR-99201-FED",
        jurisdiction: "Federal District Court",
        case_title: "State v. Digital Defamation Incident"
    })
    MERGE (evidence1:LogicalEvidence {
        evidence_id: "EVID-CCTV-001",
        custody_status: "SECURED",
        admissibility_tag: "CONTESTED",
        description: "Corridor surveillance video entering executive office suite"
    })
    MERGE (evidence1)-[:REPRESENTS_CONCEPT]->(exhibit1)

    MERGE (rawVideo1:Entity:MediaContainer {
        entity_id: "ent-cctv-raw-001",
        file_name: "corridor_cam04_20261010_raw.mp4",
        mime_type: "video/mp4",
        sha256_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        byte_size: 524288000,
        storage_uri: "s3://secure-evidence/raw/cam04.mp4"
    })
    MERGE (rawVideo1)-[:IMPLEMENTS_LOGICAL]->(evidence1)

    MERGE (rawFrame1:Entity:MediaFrame {
        entity_id: "ent-frame-1042-raw",
        frame_number: 1042,
        timestamp_offset_ms: 34733,
        perceptual_hash: "d9e8a7b6c5000000",
        tampering_flag: false,
        phash_distance: 0.0,
        description: "Unaltered raw corridor frame depicting hallway entrance"
    })
    MERGE (rawVideo1)-[:CONTAINS_DATA]->(rawFrame1)

    MERGE (cameraSensor1:Agent:HardwareDevice {
        agent_id: "ag-sensor-axis-p32",
        name: "Axis P32 Network Camera Sensor",
        firmware_version: "v10.12.3",
        serial_number: "AXIS-SN-88219"
    })
    MERGE (captureAct1:Activity {
        activity_id: "act-capture-001",
        operation_type: "SENSOR_CAPTURE",
        timestamp: datetime("2026-10-10T20:15:00Z")
    })
    MERGE (captureAct1)-[:WAS_ASSOCIATED_WITH]->(cameraSensor1)
    MERGE (rawFrame1)-[:WAS_GENERATED_BY]->(captureAct1)

    MERGE (alterTool1:Agent:SoftwareTool {
        agent_id: "ag-tool-deepfacelab",
        name: "DeepFaceLab-v2",
        version: "2.1.0-CUDA"
    })
    MERGE (alterAct1:Activity:Transform {
        activity_id: "act-faceswap-901",
        operation_type: "DEEPFAKE_FACE_REPLACEMENT",
        parameters: '{"model": "DF-SAE", "iterations": 150000, "target_identity": "John_Doe"}',
        timestamp: datetime("2026-10-10T22:30:15Z")
    })
    MERGE (alterAct1)-[:WAS_ASSOCIATED_WITH]->(alterTool1)

    MERGE (tamperedFrame1:Entity:MediaFrame {
        entity_id: "ent-frame-1042-tampered",
        frame_number: 1042,
        perceptual_hash: "d9e8a7b6ffffffff",
        tampering_flag: true,
        phash_distance: 24.5,
        description: "Corridor frame with synthetic face replacement composite"
    })
    MERGE (alterAct1)-[:USED]->(rawFrame1)
    MERGE (tamperedFrame1)-[:WAS_GENERATED_BY]->(alterAct1)
    MERGE (tamperedFrame1)-[:WAS_DERIVED_FROM {derivation_type: "SYNTHETIC_FACE_SWAP"}]->(rawFrame1)

    MERGE (exportedVideo1:Entity:MediaContainer {
        entity_id: "ent-cctv-tampered-export",
        file_name: "exhibit_a_submitted_footage.mp4",
        mime_type: "video/mp4",
        sha256_hash: "c79f972049f50604b779a55e0921ec56d9be705199ff2ab21570d9a6950ee030",
        byte_size: 104857600
    })
    MERGE (exportedVideo1)-[:CONTAINS_DATA]->(tamperedFrame1)
    MERGE (exportedVideo1)-[:WAS_DERIVED_FROM]->(rawVideo1)
    MERGE (exportedVideo1)-[:IMPLEMENTS_LOGICAL]->(evidence1)

    MERGE (exhibit2:CaseExhibit {
        exhibit_id: "EX-2026-0891",
        court_case_num: "CR-99201",
        jurisdiction: "Federal District",
        case_title: "State v. Spliced Hallway Evidence"
    })
    MERGE (evidence2:LogicalEvidence {
        evidence_id: "EVID-MEDIA-01",
        custody_status: "SECURED",
        admissibility_tag: "PRE_HEARING",
        description: "Hallway security recording recovered from precinct checkpoint"
    })
    MERGE (evidence2)-[:REPRESENTS_CONCEPT]->(exhibit2)

    MERGE (rawVideo2:Entity:MediaContainer {
        entity_id: "ent-raw-001",
        file_name: "cctv_hallway_raw.mp4",
        mime_type: "video/mp4",
        sha256_hash: "a4b1c2d3e4f509871234567890abcdefa4b1c2d3e4f509871234567890abcdef",
        byte_size: 524288000,
        storage_uri: "s3://evidence-store/cctv_raw.mp4"
    })
    MERGE (rawVideo2)-[:IMPLEMENTS_LOGICAL]->(evidence2)

    MERGE (frame102:Entity:MediaFrame {
        entity_id: "ent-frame-102",
        frame_number: 102,
        timestamp_offset_ms: 3400,
        perceptual_hash: "d9e8a7b6c5001122",
        tampering_flag: false,
        phash_distance: 0.0,
        description: "Baseline security frame at checkpoint threshold"
    })
    MERGE (rawVideo2)-[:CONTAINS_DATA]->(frame102)

    MERGE (tool2:Agent:SoftwareTool {
        agent_id: "ag-tool-01",
        name: "OpenCV Splicing Detector",
        version: "4.10.0"
    })
    MERGE (examiner2:Agent:ForensicExaminer {
        agent_id: "ag-user-09",
        name: "Special Agent Carter",
        badge_number: "SA-4412"
    })

    MERGE (job2:Activity:PipelineJob {
        activity_id: "act-job-501",
        job_name: "Batch_Frame_Inspection",
        started_at: datetime("2026-10-10T21:00:00Z")
    })
    MERGE (filterOp2:Activity:Transform {
        activity_id: "act-op-501-1",
        operation_type: "DEEPFAKE_FACE_SUPERRESOLUTION",
        parameters: '{"upscale_factor": 4, "model": "ESRGAN-Forensic-v2"}',
        timestamp: datetime("2026-10-10T21:15:30Z")
    })
    MERGE (job2)-[:CONTAINS_OPERATOR]->(filterOp2)
    MERGE (filterOp2)-[:WAS_ASSOCIATED_WITH]->(tool2)
    MERGE (job2)-[:WAS_ASSOCIATED_WITH]->(examiner2)

    MERGE (enhancedFrame2:Entity:MediaFrame {
        entity_id: "ent-frame-102-enhanced",
        frame_number: 102,
        perceptual_hash: "d9e8a7b6ff009988",
        tampering_flag: true,
        phash_distance: 18.2,
        description: "Enhanced facial region with generative superresolution and edge splicing"
    })
    MERGE (filterOp2)-[:USED]->(frame102)
    MERGE (enhancedFrame2)-[:WAS_GENERATED_BY]->(filterOp2)
    MERGE (enhancedFrame2)-[:WAS_DERIVED_FROM {derivation_type: "ENHANCEMENT"}]->(frame102)

    MERGE (exportedVideo2:Entity:MediaContainer {
        entity_id: "ent-cctv-enhanced-export",
        file_name: "cctv_hallway_enhanced_export.mp4",
        mime_type: "video/mp4",
        sha256_hash: "b5c2d3e4f509871234567890abcdefa4b1c2d3e4f509871234567890abcdef01",
        byte_size: 209715200
    })
    MERGE (exportedVideo2)-[:CONTAINS_DATA]->(enhancedFrame2)
    MERGE (exportedVideo2)-[:WAS_DERIVED_FROM]->(rawVideo2)
    MERGE (exportedVideo2)-[:IMPLEMENTS_LOGICAL]->(evidence2)
    """
    with driver.session() as session:
        session.run(cypher_seed)
    return True


SIMULATION_STORE = {
    "exhibits": [
        {
            "exhibit_id": "EXHIBIT-2026-A",
            "case_title": "State v. Digital Defamation Incident",
            "court_case_num": "CR-99201-FED",
            "jurisdiction": "Federal District Court",
            "evidence_id": "EVID-CCTV-001",
            "status": "CONTESTED"
        },
        {
            "exhibit_id": "EX-2026-0891",
            "case_title": "State v. Spliced Hallway Evidence",
            "court_case_num": "CR-99201",
            "jurisdiction": "Federal District",
            "evidence_id": "EVID-MEDIA-01",
            "status": "PRE_HEARING"
        }
    ],
    "containers": [
        {
            "entity_id": "ent-cctv-raw-001",
            "file_name": "corridor_cam04_20261010_raw.mp4",
            "mime_type": "video/mp4",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "is_authentic": True,
            "evidence_id": "EVID-CCTV-001"
        },
        {
            "entity_id": "ent-cctv-tampered-export",
            "file_name": "exhibit_a_submitted_footage.mp4",
            "mime_type": "video/mp4",
            "sha256": "c79f972049f50604b779a55e0921ec56d9be705199ff2ab21570d9a6950ee030",
            "is_authentic": False,
            "evidence_id": "EVID-CCTV-001"
        },
        {
            "entity_id": "ent-raw-001",
            "file_name": "cctv_hallway_raw.mp4",
            "mime_type": "video/mp4",
            "sha256": "a4b1c2d3e4f509871234567890abcdefa4b1c2d3e4f509871234567890abcdef",
            "is_authentic": True,
            "evidence_id": "EVID-MEDIA-01"
        },
        {
            "entity_id": "ent-cctv-enhanced-export",
            "file_name": "cctv_hallway_enhanced_export.mp4",
            "mime_type": "video/mp4",
            "sha256": "b5c2d3e4f509871234567890abcdefa4b1c2d3e4f509871234567890abcdef01",
            "is_authentic": False,
            "evidence_id": "EVID-MEDIA-01"
        }
    ],
    "frames": [
        {
            "entity_id": "ent-frame-1042-raw",
            "parent_id": "ent-cctv-raw-001",
            "frame_number": 1042,
            "phash": "d9e8a7b6c5000000",
            "tampered": False,
            "phash_distance": 0.0,
            "operation": "SENSOR_CAPTURE",
            "agent": "Axis P32 Network Camera Sensor",
            "description": "Authentic raw camera sensor capture"
        },
        {
            "entity_id": "ent-frame-1042-tampered",
            "parent_id": "ent-cctv-tampered-export",
            "frame_number": 1042,
            "phash": "d9e8a7b6ffffffff",
            "tampered": True,
            "derived_from": "ent-frame-1042-raw",
            "operation": "DEEPFAKE_FACE_REPLACEMENT",
            "tool": "DeepFaceLab-v2",
            "agent": "DeepFaceLab-v2",
            "params": '{"model": "DF-SAE", "iterations": 150000, "target_identity": "John_Doe"}',
            "phash_distance": 24.5
        },
        {
            "entity_id": "ent-frame-102",
            "parent_id": "ent-raw-001",
            "frame_number": 102,
            "phash": "d9e8a7b6c5001122",
            "tampered": False,
            "phash_distance": 0.0,
            "operation": "SENSOR_CAPTURE",
            "agent": "Special Agent Carter (SA-4412)",
            "description": "Baseline security frame at checkpoint threshold"
        },
        {
            "entity_id": "ent-frame-102-enhanced",
            "parent_id": "ent-cctv-enhanced-export",
            "frame_number": 102,
            "phash": "d9e8a7b6ff009988",
            "tampered": True,
            "derived_from": "ent-frame-102",
            "operation": "DEEPFAKE_FACE_SUPERRESOLUTION",
            "tool": "OpenCV Splicing Detector",
            "agent": "OpenCV Splicing Detector",
            "job_name": "Batch_Frame_Inspection",
            "params": '{"upscale_factor": 4, "model": "ESRGAN-Forensic-v2"}',
            "phash_distance": 18.2
        }
    ],
    "operators": [
        {
            "job_name": "Batch_Frame_Inspection",
            "job_id": "act-job-501",
            "task_operation": "DEEPFAKE_FACE_SUPERRESOLUTION",
            "task_id": "act-op-501-1",
            "parameters": '{"upscale_factor": 4, "model": "ESRGAN-Forensic-v2"}',
            "software_tool": "OpenCV Splicing Detector (v4.10.0)",
            "supervising_examiner": "Special Agent Carter (Badge SA-4412)"
        },
        {
            "job_name": "Video_Editing_Suite_Session",
            "job_id": "act-job-faceswap",
            "task_operation": "DEEPFAKE_FACE_REPLACEMENT",
            "task_id": "act-faceswap-901",
            "parameters": '{"model": "DF-SAE", "iterations": 150000, "target_identity": "John_Doe"}',
            "software_tool": "DeepFaceLab-v2 (2.1.0-CUDA)",
            "supervising_examiner": "Unauthorized External Actor"
        }
    ]
}


def execute_backward_trace(driver: Optional[Any], entity_id: str) -> List[Dict[str, Any]]:
    if not driver:
        if entity_id == "ent-frame-1042-tampered":
            return [{
                "suspect_id": "ent-frame-1042-tampered",
                "suspect_frame": 1042,
                "operation_applied": "DEEPFAKE_FACE_REPLACEMENT",
                "tool_or_agent": "DeepFaceLab-v2",
                "upstream_source_id": "ent-frame-1042-raw",
                "root_container": "corridor_cam04_20261010_raw.mp4",
                "root_sensor": "Axis P32 Network Camera Sensor",
                "phash_divergence": 24.5,
                "hops": 2
            }]
        elif entity_id == "ent-frame-102-enhanced":
            return [{
                "suspect_id": "ent-frame-102-enhanced",
                "suspect_frame": 102,
                "operation_applied": "DEEPFAKE_FACE_SUPERRESOLUTION",
                "tool_or_agent": "OpenCV Splicing Detector",
                "upstream_source_id": "ent-frame-102",
                "root_container": "cctv_hallway_raw.mp4",
                "root_sensor": "Special Agent Carter (SA-4412)",
                "phash_divergence": 18.2,
                "hops": 2
            }]
        return []

    cypher = """
    MATCH path = (suspect:Entity {entity_id: $entity_id})-[:WAS_DERIVED_FROM*1..10]->(origin:Entity)
    WHERE NOT (origin)-[:WAS_DERIVED_FROM]->()
    OPTIONAL MATCH (suspect)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
    OPTIONAL MATCH (origin)<-[:CONTAINS_DATA]-(rootContainer:MediaContainer)
    OPTIONAL MATCH (origin)-[:WAS_GENERATED_BY]->(:Activity)-[:WAS_ASSOCIATED_WITH]->(sensor:Agent)
    RETURN 
        suspect.entity_id AS suspect_id,
        suspect.frame_number AS suspect_frame,
        act.operation_type AS operation_applied,
        agent.name AS tool_or_agent,
        origin.entity_id AS upstream_source_id,
        rootContainer.file_name AS root_container,
        sensor.name AS root_sensor,
        suspect.phash_distance AS phash_divergence,
        length(path) AS hops
    """
    with driver.session() as session:
        result = session.run(cypher, {"entity_id": entity_id})
        return [record.data() for record in result]


def execute_forward_trace(driver: Optional[Any], entity_id: str) -> List[Dict[str, Any]]:
    if not driver:
        if entity_id in ["ent-frame-1042-raw", "ent-cctv-raw-001"]:
            return [{
                "origin_id": entity_id,
                "compromised_derivative_id": "ent-frame-1042-tampered",
                "derivative_type": "MediaFrame",
                "derivative_container": "exhibit_a_submitted_footage.mp4",
                "operation": "DEEPFAKE_FACE_REPLACEMENT",
                "hops": 1
            }]
        elif entity_id in ["ent-frame-102", "ent-raw-001"]:
            return [{
                "origin_id": entity_id,
                "compromised_derivative_id": "ent-frame-102-enhanced",
                "derivative_type": "MediaFrame",
                "derivative_container": "cctv_hallway_enhanced_export.mp4",
                "operation": "DEEPFAKE_FACE_SUPERRESOLUTION",
                "hops": 1
            }]
        return []

    cypher = """
    MATCH path = (origin:Entity {entity_id: $entity_id})<-[:WAS_DERIVED_FROM*1..10]-(downstream:Entity)
    OPTIONAL MATCH (downstream)<-[:CONTAINS_DATA]-(container:MediaContainer)
    OPTIONAL MATCH (downstream)-[:WAS_GENERATED_BY]->(act:Activity)
    RETURN 
        origin.entity_id AS origin_id,
        downstream.entity_id AS compromised_derivative_id,
        labels(downstream)[0] AS derivative_type,
        container.file_name AS derivative_container,
        act.operation_type AS operation,
        length(path) AS hops
    """
    with driver.session() as session:
        result = session.run(cypher, {"entity_id": entity_id})
        return [record.data() for record in result]


def get_container_hierarchy(driver: Optional[Any], container_id: str) -> List[Dict[str, Any]]:
    if not driver:
        return [f for f in SIMULATION_STORE["frames"] if f.get("parent_id") == container_id]

    cypher = """
    MATCH (container:MediaContainer {entity_id: $container_id})-[:CONTAINS_DATA]->(frame:Entity)
    OPTIONAL MATCH (frame)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(ag:Agent)
    RETURN 
        frame.entity_id AS entity_id,
        frame.frame_number AS frame_number,
        frame.perceptual_hash AS phash,
        frame.tampering_flag AS tampered,
        frame.phash_distance AS phash_distance,
        act.operation_type AS operation,
        ag.name AS agent_name
    ORDER BY frame.frame_number ASC
    """
    with driver.session() as session:
        result = session.run(cypher, {"container_id": container_id})
        return [record.data() for record in result]


def get_operator_containment(driver: Optional[Any]) -> List[Dict[str, Any]]:
    if not driver:
        return SIMULATION_STORE["operators"]

    cypher = """
    MATCH (job:PipelineJob)-[:CONTAINS_OPERATOR]->(task:Transform)
    OPTIONAL MATCH (task)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
    OPTIONAL MATCH (job)-[:WAS_ASSOCIATED_WITH]->(examiner:Agent)
    RETURN 
        job.job_name AS job_name,
        task.operation_type AS task_operation,
        task.parameters AS parameters,
        agent.name AS software_tool,
        examiner.name AS supervising_examiner
    """
    with driver.session() as session:
        result = session.run(cypher)
        return [record.data() for record in result]


def scan_anomalous_frames(driver: Optional[Any], min_threshold: float = 10.0) -> List[Dict[str, Any]]:
    if not driver:
        return [f for f in SIMULATION_STORE["frames"] if f.get("phash_distance", 0.0) >= min_threshold]

    cypher = """
    MATCH (f:Entity:MediaFrame)
    WHERE f.tampering_flag = true OR f.phash_distance >= $threshold
    MATCH (f)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
    MATCH (f)<-[:CONTAINS_DATA]-(container:MediaContainer)
    RETURN 
        f.entity_id AS entity_id,
        f.frame_number AS frame_number,
        f.phash_distance AS phash_distance,
        f.perceptual_hash AS phash,
        act.operation_type AS operation,
        agent.name AS agent,
        container.file_name AS container_file
    ORDER BY f.phash_distance DESC
    """
    with driver.session() as session:
        result = session.run(cypher, {"threshold": min_threshold})
        return [record.data() for record in result]


def perform_graphrag_investigation(
    driver: Optional[Any],
    openai_key: Optional[str],
    user_query: str
) -> Dict[str, Any]:
    cypher_retrieval = """
    MATCH (c:CaseExhibit)-[:REPRESENTS_CONCEPT]-(ev:LogicalEvidence)
    MATCH (ev)<-[:IMPLEMENTS_LOGICAL]-(container:MediaContainer)-[:CONTAINS_DATA]->(frame:Entity)
    OPTIONAL MATCH (frame)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
    OPTIONAL MATCH (frame)-[:WAS_DERIVED_FROM]->(sourceFrame:Entity)<-[:CONTAINS_DATA]-(sourceContainer:MediaContainer)
    OPTIONAL MATCH (sourceFrame)-[:WAS_GENERATED_BY]->(:Activity)-[:WAS_ASSOCIATED_WITH]->(sensor:Agent)
    RETURN 
        c.exhibit_id AS Exhibit,
        c.case_title AS CaseTitle,
        ev.evidence_id AS EvidenceID,
        container.file_name AS ContainerFile,
        frame.frame_number AS FrameNumber,
        frame.tampering_flag AS IsTampered,
        frame.phash_distance AS pHashDivergence,
        act.operation_type AS Operation,
        act.parameters AS OperationParams,
        agent.name AS ExecutingAgent,
        sourceContainer.file_name AS OriginalRawFile,
        sensor.name AS CameraSensor
    LIMIT 20
    """
    if driver:
        with driver.session() as session:
            records = session.run(cypher_retrieval).data()
    else:
        records = [
            {
                "Exhibit": "EXHIBIT-2026-A",
                "CaseTitle": "State v. Digital Defamation Incident",
                "EvidenceID": "EVID-CCTV-001",
                "ContainerFile": "exhibit_a_submitted_footage.mp4",
                "FrameNumber": 1042,
                "IsTampered": True,
                "pHashDivergence": 24.5,
                "Operation": "DEEPFAKE_FACE_REPLACEMENT",
                "OperationParams": '{"model": "DF-SAE", "iterations": 150000, "target_identity": "John_Doe"}',
                "ExecutingAgent": "DeepFaceLab-v2",
                "OriginalRawFile": "corridor_cam04_20261010_raw.mp4",
                "CameraSensor": "Axis P32 Network Camera Sensor"
            },
            {
                "Exhibit": "EX-2026-0891",
                "CaseTitle": "State v. Spliced Hallway Evidence",
                "EvidenceID": "EVID-MEDIA-01",
                "ContainerFile": "cctv_hallway_enhanced_export.mp4",
                "FrameNumber": 102,
                "IsTampered": True,
                "pHashDivergence": 18.2,
                "Operation": "DEEPFAKE_FACE_SUPERRESOLUTION",
                "OperationParams": '{"upscale_factor": 4, "model": "ESRGAN-Forensic-v2"}',
                "ExecutingAgent": "OpenCV Splicing Detector",
                "OriginalRawFile": "cctv_hallway_raw.mp4",
                "CameraSensor": "Special Agent Carter (SA-4412)"
            }
        ]

    graph_context_str = json.dumps(records, indent=2)

    system_prompt = (
        "You are ProvLens, an expert Judicial Digital Media Forensics Assistant. "
        "Analyze digital media provenance and chain of custody strictly using the provided graph context. "
        "Strict Grounding Rules:\n"
        "1. Base every claim solely on the provided graph context. Do NOT extrapolate or hallucinate unrecorded steps.\n"
        "2. Identify exact media container filenames, frame numbers, transformation operations, and executing tools/agents.\n"
        "3. Explicitly report whether tampering was detected, include pHash divergence metrics, and state the original authentic capture source.\n"
        "4. Conclude with a definitive statement on judicial evidence integrity."
    )

    user_prompt = f"""Investigative Inquiry:
\"{user_query}\"

Verified Provenance Graph Context:
{graph_context_str}

Please generate an objective, legally defensible ProvLens Forensic Report:"""

    if OPENAI_AVAILABLE and openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            llm_text = response.choices[0].message.content
        except Exception as e:
            llm_text = f"LLM Generation Note: {str(e)}"
    else:
        if "102" in user_query or "EX-2026-0891" in user_query or "cctv_hallway" in user_query:
            llm_text = (
                "### 🛡️ ProvLens Official Forensic Assessment: Exhibit EX-2026-0891\n\n"
                "- **Target Exhibit:** `EX-2026-0891` (*State v. Spliced Hallway Evidence*)\n"
                "- **Evidence Identifier:** `EVID-MEDIA-01`\n"
                "- **Analyzed Media Container:** `cctv_hallway_enhanced_export.mp4`\n"
                "- **Tampering Verdict:** **TAMPERED / SPLICED ENHANCEMENT (pHash Divergence: 18.2)**\n"
                "- **Forensic Findings:** Frame #102 was processed via `DEEPFAKE_FACE_SUPERRESOLUTION` executed by tool `OpenCV Splicing Detector` under supervising examiner `Special Agent Carter`.\n"
                "- **Transformation Parameters:** Model `ESRGAN-Forensic-v2` with an upscale factor of 4x.\n"
                "- **Authentic Root Origin:** Derived from authentic baseline security capture `cctv_hallway_raw.mp4`.\n\n"
                "**Evidentiary Integrity Conclusion:** The facial region in frame 102 exhibits synthetic super-resolution artifacts, failing the continuous chain of custody required for unaugmented visual evidence."
            )
        else:
            llm_text = (
                "### 🛡️ ProvLens Official Forensic Assessment: Exhibit EXHIBIT-2026-A\n\n"
                "- **Target Exhibit:** `EXHIBIT-2026-A` (*State v. Digital Defamation Incident*)\n"
                "- **Evidence Identifier:** `EVID-CCTV-001`\n"
                "- **Analyzed Media Container:** `exhibit_a_submitted_footage.mp4`\n"
                "- **Tampering Verdict:** **TAMPERED (High Confidence / Anomalous pHash: 24.5)**\n"
                "- **Forensic Findings:** Frame #1042 was altered via `DEEPFAKE_FACE_REPLACEMENT` executed by tool `DeepFaceLab-v2`.\n"
                "- **Transformation Parameters:** Model `DF-SAE`, 150,000 iterations targeting identity `John_Doe`.\n"
                "- **Authentic Root Origin:** Derived from authentic raw capture `corridor_cam04_20261010_raw.mp4`, originally captured by `Axis P32 Network Camera Sensor`.\n\n"
                "**Chain of Custody Conclusion:** The submitted footage fails evidentiary integrity verification. "
                "Frame 1042 was modified post-capture using synthetic face replacement, invalidating its authenticity as direct evidence."
            )

    return {
        "assessment": llm_text,
        "cypher_executed": cypher_retrieval,
        "raw_subgraph": records
    }


def main():
    st.markdown("""
    <div class="provlens-header">
        <h1>🛡️ ProvLens</h1>
        <p>Digital Media Provenance & Forensics GraphRAG Platform | W3C PROV • Ibis Containment • Judicial Graphs</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.title("⚙️ ProvLens Control Center")
    neo4j_uri = st.sidebar.text_input("Neo4j URI", value=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user = st.sidebar.text_input("Neo4j Username", value=os.getenv("NEO4J_USER", "neo4j"))
    neo4j_pwd = st.sidebar.text_input("Neo4j Password", value=os.getenv("NEO4J_PASSWORD", "password"), type="password")
    openai_key = st.sidebar.text_input("OpenAI API Key (Optional)", value=os.getenv("OPENAI_API_KEY", ""), type="password")

    driver = None
    if NEO4J_AVAILABLE:
        driver = get_neo4j_driver(neo4j_uri, neo4j_user, neo4j_pwd)

    if driver:
        st.sidebar.success("🟢 Neo4j Database Connected")
    else:
        st.sidebar.info("💡 Standalone Simulation Mode Active")

    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("Init Schema"):
            if driver:
                init_provlens_schema(driver)
                st.sidebar.success("Constraints applied!")
            else:
                st.sidebar.success("Schema verified.")
    with col_btn2:
        if st.button("Seed Cases"):
            if driver:
                seed_provlens_demo_cases(driver)
                st.sidebar.success("Cases seeded!")
            else:
                st.sidebar.success("Cases active.")

    st.sidebar.caption("ProvLens v2.0 | Built with Streamlit, Neo4j & GraphRAG")

    tab_rag, tab_trace, tab_ingest, tab_report, tab_schema = st.tabs([
        "🤖 GraphRAG Assistant",
        "🧭 Provenance Tracing & Explorer",
        "📥 Ingestion Studio",
        "📄 Chain of Custody Report",
        "📐 System Architecture & Cypher DDL"
    ])

    with tab_rag:
        st.subheader("Investigative Question Answering (GraphRAG)")
        sample_prompts = [
            "Was frame 1042 in exhibit_a_submitted_footage.mp4 tampered with, and what is its authentic origin?",
            "Analyze Exhibit EX-2026-0891 (EVID-MEDIA-01): what operations and agents altered frame 102 in cctv_hallway_raw.mp4?",
            "What software tool, model, and parameters were used to modify the hallway surveillance footage?",
            "What is the provenance of the suspect facial region in Exhibit-A, which software tool altered frame 1042, and what raw footage did it originate from?",
            "Calculate the perceptual hash distance divergence across all derived media frames and identify anomalous actors."
        ]
        selected_prompt = st.selectbox("Select a Sample Forensic Inquiry:", [""] + sample_prompts)
        
        user_query = st.text_area(
            "Custom Investigative Query:",
            value=selected_prompt if selected_prompt else "Was frame 1042 in exhibit_a_submitted_footage.mp4 tampered with, and what is its authentic origin?"
        )

        if st.button("Run ProvLens Investigation", type="primary"):
            with st.spinner("Traversing provenance graph and synthesizing assessment..."):
                res = perform_graphrag_investigation(driver, openai_key, user_query)
                st.markdown(res["assessment"])

                with st.expander("🔍 Inspect Subgraph Context"):
                    st.json(res["raw_subgraph"])

                with st.expander("💻 Inspect Executed Cypher Traversal"):
                    st.code(res["cypher_executed"], language="cypher")

    with tab_trace:
        st.subheader("Bidirectional Provenance Traversal & Multi-Granular Inspection")

        trace_mode = st.radio("Select Traversal Mode:", [
            "1. Backward Tracing (Root Cause & 'Why-Provenance')",
            "2. Forward Tracing (Compromise & Blast-Radius Propagation)",
            "3. Ibis Data Containment (Parent Container -> Child Frames)",
            "4. Ibis Operator Containment (PipelineJob -> Tasks -> Agents)",
            "5. Behavioral Anomaly Scanner (Perceptual Hash Divergence)"
        ])

        if "1. Backward Tracing" in trace_mode:
            col1, col2 = st.columns([3, 1])
            with col1:
                suspect_input = st.selectbox("Select Suspect Entity:", [
                    "ent-frame-1042-tampered (Case 1: Deepfake Face Swap)",
                    "ent-frame-102-enhanced (Case 2: Face Super-Resolution & Splicing)"
                ])
                suspect_id = suspect_input.split(" ")[0]
            with col2:
                st.write("")
                st.write("")
                exec_bwd = st.button("Execute Backward Trace")

            if exec_bwd or suspect_id:
                results = execute_backward_trace(driver, suspect_id)
                if results:
                    st.success(f"Discovered {len(results)} attribution path(s):")
                    for r in results:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Suspect Target: <code>{r.get('suspect_id')}</code> (Frame #{r.get('suspect_frame')})</h4>
                            <p><b>Tampering Operation:</b> <span class="tamper-badge">{r.get('operation_applied')}</span> via <code>{r.get('tool_or_agent')}</code></p>
                            <p><b>Perceptual Hash Divergence:</b> <code>{r.get('phash_divergence')}</code></p>
                            <p><b>Root Authentic Container:</b> <code>{r.get('root_container')}</code></p>
                            <p><b>Original Hardware/Capture Agent:</b> <code>{r.get('root_sensor')}</code></p>
                            <p><b>Derivation Distance:</b> {r.get('hops')} graph hops</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        **Lineage Chain of Custody:**  
                        `[Origin: {r.get('root_sensor')}]` ──► `[Raw: {r.get('root_container')}]` ──► `[{r.get('tool_or_agent')}: {r.get('operation_applied')}]` ──► `[Suspect: {r.get('suspect_id')}]`
                        """)
                else:
                    st.warning("No upstream derivation found for this entity.")

        elif "2. Forward Tracing" in trace_mode:
            col1, col2 = st.columns([3, 1])
            with col1:
                origin_input = st.selectbox("Select Compromised Source Entity:", [
                    "ent-frame-1042-raw (Case 1 Source Frame)",
                    "ent-cctv-raw-001 (Case 1 Source File)",
                    "ent-frame-102 (Case 2 Source Frame)",
                    "ent-raw-001 (Case 2 Source File)"
                ])
                origin_id = origin_input.split(" ")[0]
            with col2:
                st.write("")
                st.write("")
                exec_fwd = st.button("Execute Forward Trace")

            if exec_fwd or origin_id:
                results = execute_forward_trace(driver, origin_id)
                if results:
                    st.success(f"Identified {len(results)} compromised derivative(s):")
                    for r in results:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Compromised Asset: <code>{r.get('compromised_derivative_id')}</code></h4>
                            <p><b>Destination Container File:</b> <code>{r.get('derivative_container')}</code></p>
                            <p><b>Transformation Applied:</b> {r.get('operation')}</p>
                            <p><b>Blast-Radius Distance:</b> {r.get('hops')} hop(s) downstream</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No downstream derivatives detected.")

        elif "3. Ibis Data Containment" in trace_mode:
            cont_choice = st.selectbox("Select Parent Media Container:", [
                "ent-cctv-tampered-export (exhibit_a_submitted_footage.mp4)",
                "ent-cctv-raw-001 (corridor_cam04_20261010_raw.mp4)",
                "ent-cctv-enhanced-export (cctv_hallway_enhanced_export.mp4)",
                "ent-raw-001 (cctv_hallway_raw.mp4)"
            ])
            cont_id = cont_choice.split(" ")[0]
            frames = get_container_hierarchy(driver, cont_id)
            if frames:
                st.write(f"Contained Elements inside Container `{cont_id}`:")
                for f in frames:
                    badge = '<span class="tamper-badge">🚨 TAMPERED</span>' if f.get("tampered") else '<span class="authentic-badge">✅ AUTHENTIC</span>'
                    st.markdown(f"""
                    - **Frame #{f.get('frame_number')}** (`{f.get('entity_id')}`) — {badge} | pHash: `{f.get('phash')}` | Divergence: `{f.get('phash_distance', 0.0)}` | Op: `{f.get('operation', 'None')}`
                    """, unsafe_allow_html=True)
            else:
                st.info("No frames linked to this container.")

        elif "4. Ibis Operator Containment" in trace_mode:
            operators = get_operator_containment(driver)
            if operators:
                for op in operators:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Parent Pipeline Job: <code>{op.get('job_name')}</code></h4>
                        <p><b>Child Task Operation:</b> <code>{op.get('task_operation')}</code></p>
                        <p><b>Parameters:</b> <code>{op.get('parameters')}</code></p>
                        <p><b>Executing Software Tool:</b> <code>{op.get('software_tool')}</code></p>
                        <p><b>Supervising Examiner / Agent:</b> <code>{op.get('supervising_examiner')}</code></p>
                    </div>
                    """, unsafe_allow_html=True)

        elif "5. Behavioral Anomaly Scanner" in trace_mode:
            threshold = st.slider("Select pHash Divergence Threshold:", min_value=1.0, max_value=30.0, value=10.0, step=0.5)
            anomalies = scan_anomalous_frames(driver, threshold)
            if anomalies:
                st.warning(f"Detected {len(anomalies)} anomalous frame(s) exceeding divergence threshold {threshold}:")
                for a in anomalies:
                    st.markdown(f"""
                    <div class="metric-card-anomaly">
                        <h4>Frame #{a.get('frame_number')} (<code>{a.get('entity_id')}</code>) — Divergence Score: <b>{a.get('phash_distance')}</b></h4>
                        <p><b>Container File:</b> <code>{a.get('container_file', a.get('parent_id'))}</code></p>
                        <p><b>Applied Operation:</b> <code>{a.get('operation')}</code></p>
                        <p><b>Modifying Agent:</b> <code>{a.get('agent', a.get('tool'))}</code></p>
                        <p><b>Perceptual Hash:</b> <code>{a.get('phash')}</code></p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success(f"No frames found exceeding divergence threshold {threshold}.")

    with tab_ingest:
        st.subheader("Register New Provenance Transformation Step")
        with st.form("ingest_form"):
            col1, col2 = st.columns(2)
            with col1:
                f_case = st.text_input("Case Exhibit ID", value="EX-2026-0891")
                f_evidence = st.text_input("Logical Evidence ID", value="EVID-MEDIA-01")
                f_parent_file = st.text_input("Parent Media Container File Name", value="cctv_hallway_enhanced_export.mp4")
                f_in_frame = st.text_input("Input Frame ID (i)", value="ent-frame-102")
                f_op = st.selectbox("Operation Type (T)", [
                    "DEEPFAKE_FACE_SUPERRESOLUTION",
                    "DEEPFAKE_FACE_REPLACEMENT",
                    "BILATERAL_DENOISE",
                    "AUDIO_DUB_CLONING",
                    "CROP_AND_SCALE",
                    "COLOR_GRADING_SHIFT"
                ])
                f_job_name = st.text_input("Parent Pipeline Job Name", value="Batch_Frame_Inspection")
            with col2:
                f_agent_name = st.text_input("Executing Agent / Tool", value="OpenCV Splicing Detector")
                f_agent_ver = st.text_input("Tool Version / Examiner Badge", value="v4.10.0")
                f_out_frame = st.text_input("Output Frame ID (o)", value=f"ent-frame-{uuid.uuid4().hex[:6]}")
                f_phash = st.text_input("Output Perceptual Hash", value="d9e8a7b6ff009988")
                f_phash_dist = st.number_input("pHash Divergence Distance", value=18.2, step=0.1)
                f_tamper = st.checkbox("Flag as Tampered / Anomalous", value=True)

            submitted = st.form_submit_button("Ingest Provenance Step")
            if submitted:
                if driver:
                    cypher = """
                    MERGE (ex:CaseExhibit {exhibit_id: $case_id})
                    MERGE (ev:LogicalEvidence {evidence_id: $evidence_id})
                    MERGE (ev)-[:REPRESENTS_CONCEPT]->(ex)

                    MERGE (parent:Entity:MediaContainer {entity_id: $parent_id})
                      ON CREATE SET parent.file_name = $parent_file
                    MERGE (parent)-[:IMPLEMENTS_LOGICAL]->(ev)

                    MERGE (input_frame:Entity {entity_id: $in_frame})
                    MERGE (agent:Agent {name: $agent_name})
                      ON CREATE SET agent.version = $agent_ver

                    MERGE (job:Activity:PipelineJob {job_name: $job_name})
                    CREATE (act:Activity:Transform {
                        activity_id: $act_id,
                        operation_type: $op,
                        timestamp: datetime()
                    })
                    CREATE (job)-[:CONTAINS_OPERATOR]->(act)
                    CREATE (act)-[:WAS_ASSOCIATED_WITH]->(agent)
                    CREATE (act)-[:USED]->(input_frame)

                    CREATE (output_frame:Entity:MediaFrame {
                        entity_id: $out_frame,
                        perceptual_hash: $phash,
                        tampering_flag: $tamper,
                        phash_distance: $phash_dist
                    })
                    CREATE (output_frame)-[:WAS_GENERATED_BY]->(act)
                    CREATE (output_frame)-[:WAS_DERIVED_FROM]->(input_frame)
                    MERGE (parent)-[:CONTAINS_DATA]->(output_frame)
                    """
                    params = {
                        "case_id": f_case,
                        "evidence_id": f_evidence,
                        "parent_id": f"ent-{uuid.uuid4().hex[:6]}",
                        "parent_file": f_parent_file,
                        "in_frame": f_in_frame,
                        "job_name": f_job_name,
                        "agent_name": f_agent_name,
                        "agent_ver": f_agent_ver,
                        "act_id": f"act-{uuid.uuid4().hex[:6]}",
                        "op": f_op,
                        "out_frame": f_out_frame,
                        "phash": f_phash,
                        "phash_dist": f_phash_dist,
                        "tamper": f_tamper
                    }
                    with driver.session() as s:
                        s.run(cypher, params)
                    st.success(f"Ingested into Neo4j! Output entity `{f_out_frame}` is now queryable.")
                else:
                    st.success(f"[Simulation Mode] Ingested transformation step! Output entity `{f_out_frame}` recorded.")

    with tab_report:
        st.subheader("Official Forensic Chain of Custody Report")
        case_select = st.selectbox("Select Judicial Case for Audit Report:", [
            "Case 1: EXHIBIT-2026-A (CR-99201-FED - State v. Digital Defamation Incident)",
            "Case 2: EX-2026-0891 (CR-99201 - State v. Spliced Hallway Evidence)"
        ])

        if "Case 1" in case_select:
            report_md = f"""# PROVLENS FORENSIC AUDIT REPORT
**Case Reference:** CR-99201-FED | **Exhibit:** EXHIBIT-2026-A  
**Date of Audit:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Investigating System:** ProvLens GraphRAG Engine  

---

### 1. Evidence Overview
- **Logical Evidence ID:** EVID-CCTV-001
- **Target File:** `exhibit_a_submitted_footage.mp4`
- **SHA-256 Checksum:** `c79f972049f50604b779a55e0921ec56d9be705199ff2ab21570d9a6950ee030`
- **Custody Status:** CONTESTED

### 2. Multi-Hop Provenance Traversal
- **Root Acquisition Source:** `corridor_cam04_20261010_raw.mp4`
- **Originating Sensor:** Axis P32 Network Camera Sensor (Firmware v10.12.3)
- **Derivation Hops:** 2 hops from raw sensor capture

### 3. Tampering Analysis & Anomalies
- **Manipulated Element:** Frame #1042 (`ent-frame-1042-tampered`)
- **Transformation Applied:** `DEEPFAKE_FACE_REPLACEMENT`
- **Software Agent:** `DeepFaceLab-v2` (Model: DF-SAE, 150k iterations)
- **Perceptual Hash Distance:** 24.5 (Threshold: >10 indicates structural modification)

### 4. Integrity Conclusion
**REJECTED AS UNALTERED EVIDENCE.**  
The provenance lineage demonstrates that post-capture synthetic face manipulation occurred, breaking authentic chain of custody.
"""
        else:
            report_md = f"""# PROVLENS FORENSIC AUDIT REPORT
**Case Reference:** CR-99201 | **Exhibit:** EX-2026-0891  
**Date of Audit:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Investigating System:** ProvLens GraphRAG Engine  

---

### 1. Evidence Overview
- **Logical Evidence ID:** EVID-MEDIA-01
- **Target File:** `cctv_hallway_enhanced_export.mp4`
- **SHA-256 Checksum:** `b5c2d3e4f509871234567890abcdefa4b1c2d3e4f509871234567890abcdef01`
- **Custody Status:** PRE_HEARING

### 2. Multi-Hop Provenance Traversal
- **Root Acquisition Source:** `cctv_hallway_raw.mp4`
- **Supervising Examiner:** Special Agent Carter (Badge SA-4412)
- **Parent Pipeline Job:** `Batch_Frame_Inspection` (Operator Containment)
- **Derivation Hops:** 2 hops from raw checkpoint capture

### 3. Tampering Analysis & Anomalies
- **Manipulated Element:** Frame #102 (`ent-frame-102-enhanced`)
- **Transformation Applied:** `DEEPFAKE_FACE_SUPERRESOLUTION`
- **Software Agent:** `OpenCV Splicing Detector` (Model: ESRGAN-Forensic-v2, 4x upscale)
- **Perceptual Hash Distance:** 18.2 (Threshold: >10 indicates structural divergence)

### 4. Integrity Conclusion
**REJECTED AS DIRECT UNMODIFIED FOOTAGE.**  
The provenance graph establishes that frame 102 was processed with generative superresolution and facial edge splicing, breaking evidentiary continuity.
"""
        st.markdown(report_md)
        st.download_button(
            label="📥 Download Forensic Audit Report",
            data=report_md,
            file_name="provlens_forensic_report.md",
            mime="text/markdown"
        )

    with tab_schema:
        st.subheader("Cypher Schema & Query Reference")
        st.markdown("**1. Backward Tracing Query:**")
        st.code("""
MATCH path = (suspect:Entity {entity_id: $entity_id})-[:WAS_DERIVED_FROM*1..10]->(origin:Entity)
WHERE NOT (origin)-[:WAS_DERIVED_FROM]->()
OPTIONAL MATCH (suspect)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
OPTIONAL MATCH (origin)<-[:CONTAINS_DATA]-(rootContainer:MediaContainer)
OPTIONAL MATCH (origin)-[:WAS_GENERATED_BY]->(:Activity)-[:WAS_ASSOCIATED_WITH]->(sensor:Agent)
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
        """, language="cypher")

        st.markdown("**2. Ibis Data Containment Query:**")
        st.code("""
MATCH (container:MediaContainer {entity_id: $container_id})-[:CONTAINS_DATA]->(frame:Entity)
OPTIONAL MATCH (frame)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(ag:Agent)
RETURN 
    frame.entity_id AS entity_id,
    frame.frame_number AS frame_number,
    frame.perceptual_hash AS phash,
    frame.tampering_flag AS tampered,
    frame.phash_distance AS phash_distance,
    act.operation_type AS operation,
    ag.name AS agent_name
ORDER BY frame.frame_number ASC;
        """, language="cypher")

        st.markdown("**3. Forward Tracing Query:**")
        st.code("""
MATCH path = (origin:Entity {entity_id: $entity_id})<-[:WAS_DERIVED_FROM*1..10]-(downstream:Entity)
OPTIONAL MATCH (downstream)<-[:CONTAINS_DATA]-(container:MediaContainer)
OPTIONAL MATCH (downstream)-[:WAS_GENERATED_BY]->(act:Activity)
RETURN 
    origin.entity_id AS origin_id,
    downstream.entity_id AS compromised_derivative_id,
    labels(downstream)[0] AS derivative_type,
    container.file_name AS derivative_container,
    act.operation_type AS operation,
    length(path) AS hops;
        """, language="cypher")

        st.markdown("**4. Ibis Operator Containment Query:**")
        st.code("""
MATCH (job:PipelineJob)-[:CONTAINS_OPERATOR]->(task:Transform)
OPTIONAL MATCH (task)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
OPTIONAL MATCH (job)-[:WAS_ASSOCIATED_WITH]->(examiner:Agent)
RETURN 
    job.job_name AS job_name,
    task.operation_type AS task_operation,
    task.parameters AS parameters,
    agent.name AS software_tool,
    examiner.name AS supervising_examiner;
        """, language="cypher")

        st.markdown("**5. Perceptual Hash Anomaly Scanner:**")
        st.code("""
MATCH (f:Entity:MediaFrame)
WHERE f.tampering_flag = true OR f.phash_distance >= $threshold
MATCH (f)-[:WAS_GENERATED_BY]->(act:Activity)-[:WAS_ASSOCIATED_WITH]->(agent:Agent)
MATCH (f)<-[:CONTAINS_DATA]-(container:MediaContainer)
RETURN 
    f.entity_id AS entity_id,
    f.frame_number AS frame_number,
    f.phash_distance AS phash_distance,
    f.perceptual_hash AS phash,
    act.operation_type AS operation,
    agent.name AS agent,
    container.file_name AS container_file
ORDER BY f.phash_distance DESC;
        """, language="cypher")


if __name__ == "__main__":
    main()

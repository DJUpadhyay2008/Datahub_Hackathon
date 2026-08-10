# ==============================================================================
# FILE: backend/main.py
# WHY THIS FILE EXISTS:
#   Main entrypoint for the FastAPI REST Backend server of the DataHub Learning Lab.
# WHAT IT DOES:
#   1. Exposes standard RESTful API endpoints for searching metadata, fetching schemas, lineage DAGs, owners, and tags.
#   2. Integrates `ai_grounding.py` for the AI Chatbot endpoint (`/ask`).
#   3. Exposes auto-generated Swagger UI interactive documentation at `http://localhost:8000/docs`.
# HOW IT INTERACTS WITH DATAHUB:
#   Communicates with DataHub GMS via `datahub_client.py` and returns structured JSON responses
#   to frontend components (Streamlit app, CLI clients, or external API consumers).
# ==============================================================================

import uvicorn
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from datahub_client import datahub_client
from ai_grounding import answer_grounded_question

app = FastAPI(
    title="DataHub Learning Lab API",
    description="FastAPI Backend interacting with DataHub GMS REST/GraphQL APIs for metadata governance and AI grounding.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for API Requests & Responses
class AIQuestionRequest(BaseModel):
    question: str
    provider: Optional[str] = "llama_cpp"
    api_key: Optional[str] = ""
    llama_url: Optional[str] = "http://localhost:8080/v1"
    llama_model: Optional[str] = "gemma-4-E2B-it-UD-Q4_K_XL.gguf"

# ------------------------------------------------------------------------------
# 1. ROOT & HEALTH CHECK
# ------------------------------------------------------------------------------
@app.get("/", summary="Root Endpoint", tags=["System"])
def root():
    """Returns basic service health and status info."""
    gms_status = datahub_client.is_gms_online()
    return {
        "service": "DataHub Learning Lab Backend",
        "status": "online",
        "datahub_gms_connected": gms_status,
        "gms_url": settings.DATAHUB_GMS_URL,
        "docs": "http://localhost:8000/docs"
    }

# ------------------------------------------------------------------------------
# 2. SEARCH METADATA DATASETS (/search)
# ------------------------------------------------------------------------------
@app.get("/search", summary="Search Datasets", tags=["Metadata Explorer"])
def search_datasets(query: str = Query("*", description="Search query string (e.g. 'orders', 'email', '*')")):
    """
    Query DataHub search index to find datasets matching keyword, column, or description.
    """
    results = datahub_client.search_datasets(query)
    return {
        "query": query,
        "count": len(results),
        "results": results
    }

# ------------------------------------------------------------------------------
# 3. GET DATASET DETAILS (/dataset)
# ------------------------------------------------------------------------------
@app.get("/dataset", summary="Get Dataset Details", tags=["Metadata Explorer"])
def get_dataset_details(urn_or_name: str = Query(..., description="Dataset URN or table name (e.g. 'customers', 'orders')")):
    """
    Fetch complete details for a specific dataset, including platform, schema, description, owners, and tags.
    """
    dataset = datahub_client.get_dataset(urn_or_name)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{urn_or_name}' not found in DataHub catalog.")
    return dataset

# ------------------------------------------------------------------------------
# 4. GET COLUMN SCHEMA LIST (/schema)
# ------------------------------------------------------------------------------
@app.get("/schema", summary="Get Column Schema List", tags=["Metadata Explorer"])
def get_schema(urn_or_name: str = Query(..., description="Dataset URN or table name")):
    """
    Returns table column names, SQL data types, primary keys, and descriptions from DataHub metadata aspects.
    """
    schema = datahub_client.get_schema(urn_or_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema for dataset '{urn_or_name}' not found.")
    return {"dataset": urn_or_name, "columns": schema}

# ------------------------------------------------------------------------------
# 5. GET LINEAGE GRAPH (/lineage)
# ------------------------------------------------------------------------------
@app.get("/lineage", summary="Get Lineage DAG", tags=["Lineage & Governance"])
def get_lineage(urn_or_name: str = Query(..., description="Dataset URN or table name")):
    """
    Retrieves upstream input sources and downstream dependent datasets/dashboards.
    """
    lineage = datahub_client.get_lineage(urn_or_name)
    return lineage

# ------------------------------------------------------------------------------
# 6. GET OWNERS (/owners)
# ------------------------------------------------------------------------------
@app.get("/owners", summary="Get Dataset Owners", tags=["Governance"])
def get_owners(urn_or_name: str = Query(..., description="Dataset URN or table name")):
    """
    Retrieves technical and business owners registered in DataHub Ownership aspects.
    """
    owners = datahub_client.get_owners(urn_or_name)
    return {"dataset": urn_or_name, "owners": owners}

# ------------------------------------------------------------------------------
# 7. GET TAGS (/tags)
# ------------------------------------------------------------------------------
@app.get("/tags", summary="Get Dataset Tags", tags=["Governance"])
def get_tags(urn_or_name: str = Query(..., description="Dataset URN or table name")):
    """
    Retrieves global tags (e.g. PII, Revenue, Tier1) attached to dataset.
    """
    tags = datahub_client.get_tags(urn_or_name)
    return {"dataset": urn_or_name, "tags": tags}

# ------------------------------------------------------------------------------
# 8. AI ASSISTANT GROUNDED ENDPOINT (/ask)
# ------------------------------------------------------------------------------
@app.post("/ask", summary="Grounded AI Assistant Query", tags=["AI Grounding"])
def ask_ai_assistant(req: AIQuestionRequest):
    """
    Answers natural language data governance questions.
    DataHub is queried FIRST to build a context payload, which is then passed to Gemini or llama.cpp.
    """
    res = answer_grounded_question(
        question=req.question,
        provider=req.provider,
        api_key=req.api_key,
        llama_url=req.llama_url,
        llama_model=req.llama_model
    )
    return res

# ------------------------------------------------------------------------------
# 9. AUTODOC AGENT ENDPOINTS (/autodoc/scan and /autodoc/write)
# ------------------------------------------------------------------------------
class WriteMetadataRequest(BaseModel):
    urn: str
    description: str
    tags: List[str]
    owner: str

@app.get("/autodoc/scan", summary="Scan for undocumented datasets", tags=["AutoDoc"])
async def scan_undocumented():
    """
    Scans for undocumented datasets and generates recommendations using LLM.
    """
    from autodoc_agent import discover_undocumented, extract_json
    from ai_grounding import retrieve_datahub_context_for_question, call_llm
    from mcp_server import mcp
    
    undoc = await discover_undocumented()
    _, system_context = retrieve_datahub_context_for_question("")
    
    results = []
    for ds in undoc:
        urn = ds["urn"]
        name = ds["name"]
        platform = ds["platform"]
        missing = ds["missing"]
        
        # 1. Gather Schema & Lineage via MCP tools
        schema_res = await mcp.call_tool("get_schema", {"dataset_urn": urn})
        schema = schema_res.structured_content.get("result", [])
        
        lineage_res = await mcp.call_tool("get_lineage", {"dataset_urn": urn})
        lineage = lineage_res.structured_content.get("result", {})
        
        # 2. Call local LLM (Gemma 4 E2B) to generate recommendations
        prompt = f"""
Perform a metadata documentation and ownership assessment for the undocumented dataset: URN '{urn}'.
Based on the table schemas, columns, and upstream/downstream lineage graphs provided in the Grounding Context, generate:
1. A concise, accurate description for this dataset.
2. A list of relevant tags (e.g., PII, Tier1, Financial, Operations, Logistics, Catalog, Analytics, Feedback, etc.).
3. A suggested owner (based on the owners of its upstream/downstream datasets, or logical business/technical role).
4. A brief confidence note explaining the reasoning/grounding behind these choices.

Return your response in this EXACT JSON structure, and nothing else (do not wrap in markdown code blocks or add any other text):
{{
  "description": "...",
  "tags": ["tag1", "tag2"],
  "suggested_owner": "...",
  "confidence_note": "..."
}}
"""
        llm_response = call_llm(
            prompt=prompt,
            system_context=system_context,
            provider="gemini"
        )
        
        parsed_meta = extract_json(llm_response)
        
        results.append({
            "urn": urn,
            "name": name,
            "platform": platform,
            "missing": missing,
            "columns": schema,
            "upstreams": lineage.get("upstreams", []),
            "downstreams": lineage.get("downstreams", []),
            "suggested": parsed_meta,
            "raw_context": f"SCHEMA:\n{schema}\n\nLINEAGE:\n{lineage}"
        })
        
    return {"results": results}

@app.post("/autodoc/write", summary="Write generated metadata back to DataHub", tags=["AutoDoc"])
async def write_back(req: WriteMetadataRequest):
    """
    Write recommended metadata back to DataHub only if URN is approved.
    """
    from autodoc_agent import APPROVED_URNS
    from mcp_server import mcp
    
    if req.urn not in APPROVED_URNS:
        raise HTTPException(
            status_code=400,
            detail=f"URN '{req.urn}' is not in the approved list for write-back."
        )
        
    res = await mcp.call_tool("write_metadata", {
        "urn": req.urn,
        "description": req.description,
        "tags": req.tags,
        "owner": req.owner
    })
    
    return res.structured_content

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

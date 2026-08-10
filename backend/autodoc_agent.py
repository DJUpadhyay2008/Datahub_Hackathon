# ==============================================================================
# FILE: backend/autodoc_agent.py
# WHY THIS FILE EXISTS:
#   Implements the Autodoc Agent that automatically discovers undocumented datasets
#   and utilizes grounded LLM reasoning to generate descriptions, tags, and owners.
# WHAT IT DOES:
#   1. Discovers undocumented datasets (missing description, owner, or tags) via MCP tools.
#   2. Gathers schema and lineage context using MCP tools.
#   3. Generates metadata grounded in lineage context via the existing LLM prompt pattern.
#   4. Outputs all discoveries and suggestions to a local report.md (dry-run mode).
# ==============================================================================

import asyncio
import json
import os
import sys

# Ensure backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import mcp
from ai_grounding import call_llm, retrieve_datahub_context_for_question

# List of dataset URNs approved for write-back.
APPROVED_URNS = {
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.reviews,PROD)",
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.order_items,PROD)"
}

def extract_json(text: str) -> dict:
    """Helper to extract and parse JSON from the LLM response."""
    text = text.strip()
    # Remove markdown code block markers
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return {
        "description": text,
        "tags": [],
        "suggested_owner": "Unknown",
        "confidence_note": "Failed to parse structured JSON from LLM response."
    }

async def discover_undocumented() -> list:
    """Discover datasets missing description, owner, or tags using MCP tools."""
    print("🔍 Discovering undocumented datasets via MCP tools...")
    res = await mcp.call_tool("search_datasets", {"query": "*"})
    datasets = res.structured_content.get("result", [])
    
    undocumented = []
    for d in datasets:
        urn = d["urn"]
        # Check if description, owner, or tags are missing
        # Some fields might be None, empty strings, or empty lists
        desc = d.get("description")
        owners = d.get("owners", [])
        tags = d.get("tags", [])
        
        is_missing_desc = not desc or str(desc).strip() == ""
        is_missing_owner = not owners or len(owners) == 0
        is_missing_tags = not tags or len(tags) == 0
        
        if is_missing_desc or is_missing_owner or is_missing_tags:
            undocumented.append({
                "urn": urn,
                "name": d.get("name", urn),
                "platform": d.get("platform", "postgres"),
                "missing": {
                    "description": is_missing_desc,
                    "owners": is_missing_owner,
                    "tags": is_missing_tags
                }
            })
    return undocumented

async def run_autodoc():
    undoc_datasets = await discover_undocumented()
    print(f"found {len(undoc_datasets)} undocumented dataset(s).")
    
    # Retrieve the verified catalog grounding context
    _, system_context = retrieve_datahub_context_for_question("")
    
    report_lines = [
        "# DataHub Metadata Autodoc Agent Report",
        "**Status**: Dry-Run Mode (No metadata written back to DataHub)",
        f"**Undocumented Datasets Found**: {len(undoc_datasets)}",
        "",
        "---",
        ""
    ]
    
    for idx, ds in enumerate(undoc_datasets, 1):
        urn = ds["urn"]
        name = ds["name"]
        platform = ds["platform"]
        missing_fields = [k for k, v in ds["missing"].items() if v]
        
        print(f"\nProcessing [{idx}/{len(undoc_datasets)}]: {name} ({platform})")
        
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
        
        # Format dataset report section
        report_lines.append(f"## {idx}. Dataset: `{name}`")
        report_lines.append(f"- **URN**: `{urn}`")
        report_lines.append(f"- **Platform**: `{platform}`")
        report_lines.append(f"- **Missing Aspects**: {', '.join(missing_fields)}")
        report_lines.append("")
        report_lines.append("### Grounded Schema & Lineage Details")
        report_lines.append("- **Columns**:")
        for col in schema:
            report_lines.append(f"  - `{col['name']}` ({col['type']}): {col.get('description', 'N/A')}")
        report_lines.append(f"- **Upstream Lineage**: {', '.join(lineage.get('upstreams', [])) or 'None'}")
        report_lines.append(f"- **Downstream Lineage**: {', '.join(lineage.get('downstreams', [])) or 'None'}")
        report_lines.append("")
        report_lines.append("### Generated Metadata Suggestions (Dry-Run)")
        report_lines.append(f"- **Suggested Description**: {parsed_meta.get('description')}")
        report_lines.append(f"- **Suggested Tags**: {', '.join(parsed_meta.get('tags', []))}")
        report_lines.append(f"- **Suggested Owner**: `{parsed_meta.get('suggested_owner')}`")
        report_lines.append(f"- **Confidence Note**: *{parsed_meta.get('confidence_note')}*")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

    report_content = "\n".join(report_lines)
    
    # Save report to local file
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report.md")
    with open(report_path, "w") as f:
        f.write(report_content)
        
    print(f"\n🎉 Done! Autodoc report written to: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_autodoc())

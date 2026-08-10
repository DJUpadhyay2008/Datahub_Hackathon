# ==============================================================================
# FILE: backend/mcp_server.py
# WHY THIS FILE EXISTS:
#   Exposes the existing metadata functions from `datahub_client.py` as Model Context Protocol (MCP) tools.
#   Allows LLMs and AI Agents to directly call DataHub search, lineage, and schema tools.
# WHAT IT DOES:
#   1. Sets up an MCPServer using the standard python `mcp` SDK.
#   2. Imports `datahub_client` from `datahub_client.py`.
#   3. Exposes the following tools:
#      - search_datasets
#      - get_schema
#      - get_lineage
# HOW IT INTERACTS WITH DATAHUB:
#   Delegates all metadata operations directly to the datahub_client instance.
# ==============================================================================

import os
import sys
import logging
from typing import List, Dict, Any

# Ensure backend directory is in the path for importing relative modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import MCPServer
from datahub_client import datahub_client

# Configure logging to stderr (stdout is reserved for JSON-RPC transport)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("datahub-mcp-server")

# Create the MCP Server
mcp = MCPServer("DataHub MCP Server")

@mcp.tool()
def search_datasets(query: str = "*") -> List[Dict[str, Any]]:
    """
    Search across all metadata datasets.
    
    Args:
        query: The search query string (defaults to "*" to match all datasets).
    """
    logger.info(f"MCP Tool called: search_datasets(query={query!r})")
    return datahub_client.search_datasets(query)

@mcp.tool()
def get_schema(dataset_urn: str) -> List[Dict[str, Any]]:
    """
    Retrieve table column schema definitions.
    
    Args:
        dataset_urn: The unique resource name (URN) or dataset name (e.g. 'orders').
    """
    logger.info(f"MCP Tool called: get_schema(dataset_urn={dataset_urn!r})")
    return datahub_client.get_schema(dataset_urn)

@mcp.tool()
def get_lineage(dataset_urn: str) -> Dict[str, Any]:
    """
    Retrieve upstream and downstream lineage DAG for a dataset.
    
    Args:
        dataset_urn: The unique resource name (URN) or dataset name (e.g. 'orders').
    """
    logger.info(f"MCP Tool called: get_lineage(dataset_urn={dataset_urn!r})")
    return datahub_client.get_lineage(dataset_urn)

@mcp.tool()
def write_metadata(urn: str, description: str, tags: list, owner: str) -> Dict[str, Any]:
    """
    Write description, tags, and owner back to DataHub.
    
    Args:
        urn: The unique resource name (URN) or dataset name (e.g. 'orders').
        description: The description text to write.
        tags: A list of tags to associate (e.g. ['PII', 'Tier1']).
        owner: The owner string (e.g. 'alice_data_lead' or 'urn:li:corpuser:alice_data_lead').
    """
    logger.info(f"MCP Tool called: write_metadata(urn={urn!r}, description={description!r}, tags={tags!r}, owner={owner!r})")
    return datahub_client.write_metadata(urn, description, tags, owner)

if __name__ == "__main__":
    mcp.run()

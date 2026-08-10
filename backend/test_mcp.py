# ==============================================================================
# FILE: backend/test_mcp.py
# WHY THIS FILE EXISTS:
#   Validates that the MCP Server correctly registers and runs tools.
#   It invokes all three registered tools (search_datasets, get_schema, get_lineage)
#   as a direct client validation step.
# ==============================================================================

import asyncio
import json
import sys
import os

# Ensure backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import mcp

async def test_tools():
    print("=========================================")
    print("Testing DataHub MCP Server Registration & Tools")
    print("=========================================\n")
    
    # 1. Test search_datasets
    print("1. Calling search_datasets(query='orders')...")
    res_search = await mcp.call_tool("search_datasets", {"query": "orders"})
    print("Result:")
    print(json.dumps(res_search.structured_content, indent=2))
    print("\n-----------------------------------------\n")
    
    # 2. Test get_schema
    target_urn = "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)"
    print(f"2. Calling get_schema(dataset_urn='{target_urn}')...")
    res_schema = await mcp.call_tool("get_schema", {"dataset_urn": target_urn})
    print("Result:")
    print(json.dumps(res_schema.structured_content, indent=2))
    print("\n-----------------------------------------\n")
    
    # 3. Test get_lineage
    print(f"3. Calling get_lineage(dataset_urn='{target_urn}')...")
    res_lineage = await mcp.call_tool("get_lineage", {"dataset_urn": target_urn})
    print("Result:")
    print(json.dumps(res_lineage.structured_content, indent=2))
    print("\n=========================================")

if __name__ == "__main__":
    asyncio.run(test_tools())

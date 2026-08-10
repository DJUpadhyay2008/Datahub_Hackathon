# ==============================================================================
# FILE: backend/test_write_mcp.py
# WHY THIS FILE EXISTS:
#   Validates that the write_metadata MCP tool works as expected by performing
#   a round-trip write and read test.
# ==============================================================================

import asyncio
import json
import sys
import os

# Ensure backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import mcp

async def test_write():
    # Target dataset: reviews
    target_urn = "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.reviews,PROD)"
    
    print("=========================================")
    print("Testing write_metadata MCP Tool")
    print("=========================================\n")
    
    print(f"1. Reading metadata BEFORE write for dataset: {target_urn}...")
    res_before = await mcp.call_tool("search_datasets", {"query": "reviews"})
    print("Result before:")
    print(json.dumps(res_before.structured_content, indent=2))
    print("\n-----------------------------------------\n")
    
    print(f"2. Calling write_metadata on: {target_urn}...")
    res_write = await mcp.call_tool("write_metadata", {
        "urn": target_urn,
        "description": "TEST WRITE — verify only",
        "tags": ["Verified_PII"],
        "owner": "urn:li:corpuser:alice_data_lead"
    })
    print("Result write:")
    print(json.dumps(res_write.structured_content, indent=2))
    print("\n-----------------------------------------\n")
    
    print(f"3. Reading metadata AFTER write for dataset: {target_urn}...")
    res_after = await mcp.call_tool("search_datasets", {"query": "reviews"})
    print("Result after:")
    print(json.dumps(res_after.structured_content, indent=2))
    print("\n=========================================")

if __name__ == "__main__":
    asyncio.run(test_write())

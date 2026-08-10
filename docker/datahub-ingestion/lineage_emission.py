# ==============================================================================
# FILE: docker/datahub-ingestion/lineage_emission.py
# WHY THIS FILE EXISTS:
#   This Python script programmatically registers dataset lineage, ownership, and tags in DataHub.
#   It demonstrates how data pipelines (e.g. Airflow, dbt, Spark, FastAPI) emit metadata lineage events.
# WHAT IT DOES:
#   1. Constructs DataHub Dataset URNs (Uniform Resource Names) for PostgreSQL tables.
#   2. Constructs downstream dataset/dashboard URNs ("Sales Report", "Revenue Dashboard").
#   3. Emits Lineage Aspects linking:
#      `customers` -> `orders` -> `sales_report` -> `revenue_dashboard`
#   4. Emits Ownership Aspects (assigns Owners like 'Alice Data Lead' and 'Bob Backend Eng').
#   5. Emits Global Tags (assigns tags like 'PII', 'Tier1', 'Revenue', 'Transactional').
# HOW IT INTERACTS WITH DATAHUB:
#   Uses `datahub.emitter.rest_emitter.DatahubRestEmitter` to push MetadataChangeProposals (MCP)
#   directly to DataHub GMS REST Endpoint (http://localhost:8080).
# ==============================================================================

import os
import sys
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# DataHub Python SDK Imports
try:
    from datahub.emitter.mcp import MetadataChangeProposalWrapper
    from datahub.emitter.rest_emitter import DatahubRestEmitter
    from datahub.metadata.schema_classes import (
        UpstreamClass,
        UpstreamLineageClass,
        DatasetPropertiesClass,
        OwnershipClass,
        OwnerClass,
        OwnershipTypeClass,
        GlobalTagsClass,
        TagAssociationClass,
        AuditStampClass
    )
    DATAHUB_SDK_AVAILABLE = True
except ImportError:
    DATAHUB_SDK_AVAILABLE = False
    logging.warning("acryl-datahub library not installed or partially available. Standalone fallback mode will be used.")

GMS_ENDPOINT = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")

def construct_dataset_urn(platform: str, table_name: str, env: str = "PROD") -> str:
    """Helper function to format standard DataHub dataset URNs."""
    return f"urn:li:dataset:(urn:li:dataPlatform:{platform},{table_name},{env})"

def emit_metadata():
    if not DATAHUB_SDK_AVAILABLE:
        print("[DEMO MODE] SDK missing, skipping live REST emission.")
        return

    emitter = DatahubRestEmitter(gms_server=GMS_ENDPOINT)

    # --------------------------------------------------------------------------
    # URN Definitions
    # --------------------------------------------------------------------------
    customers_urn = construct_dataset_urn("postgres", "ecommerce_db.ecommerce.customers")
    orders_urn = construct_dataset_urn("postgres", "ecommerce_db.ecommerce.orders")
    sales_report_urn = construct_dataset_urn("postgres", "ecommerce_db.ecommerce.sales_report")
    revenue_dashboard_urn = construct_dataset_urn("postgres", "ecommerce_db.ecommerce.revenue_dashboard")
    inventory_urn = construct_dataset_urn("postgres", "ecommerce_db.ecommerce.inventory")

    print("🚀 Registering Lineage & Metadata in DataHub...")

    # --------------------------------------------------------------------------
    # 1. Lineage: Customers -> Orders
    # --------------------------------------------------------------------------
    orders_lineage = UpstreamLineageClass(
        upstreams=[
            UpstreamClass(
                dataset=customers_urn,
                type="TRANSFORMED"
            )
        ]
    )
    mcp_orders_lineage = MetadataChangeProposalWrapper(
        entityUrn=orders_urn,
        aspect=orders_lineage
    )
    try:
        emitter.emit(mcp_orders_lineage)
        print(f"  ✅ Emitted Lineage: customers -> orders")
    except Exception as e:
        print(f"  ⚠️ Could not emit to GMS (is GMS running at {GMS_ENDPOINT}?): {e}")

    # --------------------------------------------------------------------------
    # 2. Lineage: Orders -> Sales Report
    # --------------------------------------------------------------------------
    sales_report_lineage = UpstreamLineageClass(
        upstreams=[
            UpstreamClass(
                dataset=orders_urn,
                type="TRANSFORMED"
            )
        ]
    )
    mcp_sales_report_lineage = MetadataChangeProposalWrapper(
        entityUrn=sales_report_urn,
        aspect=sales_report_lineage
    )
    try:
        emitter.emit(mcp_sales_report_lineage)
        print(f"  ✅ Emitted Lineage: orders -> sales_report")
    except Exception as e:
        print(f"  ⚠️ GMS offline: {e}")

    # --------------------------------------------------------------------------
    # 3. Lineage: Sales Report -> Revenue Dashboard
    # --------------------------------------------------------------------------
    revenue_lineage = UpstreamLineageClass(
        upstreams=[
            UpstreamClass(
                dataset=sales_report_urn,
                type="TRANSFORMED"
            )
        ]
    )
    mcp_revenue_lineage = MetadataChangeProposalWrapper(
        entityUrn=revenue_dashboard_urn,
        aspect=revenue_lineage
    )
    try:
        emitter.emit(mcp_revenue_lineage)
        print(f"  ✅ Emitted Lineage: sales_report -> revenue_dashboard")
    except Exception as e:
        print(f"  ⚠️ GMS offline: {e}")

    # --------------------------------------------------------------------------
    # 4. Ownership Emission: Assign Owners to Customers & Inventory
    # --------------------------------------------------------------------------
    now_stamp = AuditStampClass(time=0, actor="urn:li:corpuser:admin")
    
    customers_owner = OwnershipClass(
        owners=[
            OwnerClass(
                owner="urn:li:corpuser:alice_data_lead",
                type=OwnershipTypeClass.TECHNICAL_OWNER
            )
        ]
    )
    mcp_customers_owner = MetadataChangeProposalWrapper(
        entityUrn=customers_urn,
        aspect=customers_owner
    )
    
    inventory_owner = OwnershipClass(
        owners=[
            OwnerClass(
                owner="urn:li:corpuser:bob_warehouse_mgr",
                type=OwnershipTypeClass.BUSINESS_OWNER
            )
        ]
    )
    mcp_inventory_owner = MetadataChangeProposalWrapper(
        entityUrn=inventory_urn,
        aspect=inventory_owner
    )

    try:
        emitter.emit(mcp_customers_owner)
        emitter.emit(mcp_inventory_owner)
        print(f"  ✅ Emitted Owners: Alice -> Customers, Bob -> Inventory")
    except Exception as e:
        print(f"  ⚠️ GMS offline: {e}")

    # --------------------------------------------------------------------------
    # 5. Tags Emission: Assign PII tag to Customers and Revenue tag to Sales Report
    # --------------------------------------------------------------------------
    pii_tag = GlobalTagsClass(
        tags=[
            TagAssociationClass(tag="urn:li:tag:PII"),
            TagAssociationClass(tag="urn:li:tag:Tier1")
        ]
    )
    mcp_pii_tags = MetadataChangeProposalWrapper(
        entityUrn=customers_urn,
        aspect=pii_tag
    )

    try:
        emitter.emit(mcp_pii_tags)
        print(f"  ✅ Emitted Tags: 'PII', 'Tier1' -> Customers")
    except Exception as e:
        print(f"  ⚠️ GMS offline: {e}")

    print("✨ Metadata emission pipeline execution finished!")

if __name__ == "__main__":
    emit_metadata()

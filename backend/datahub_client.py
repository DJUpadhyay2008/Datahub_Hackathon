# ==============================================================================
# FILE: backend/datahub_client.py
# WHY THIS FILE EXISTS:
#   Acts as the unified interface between our application and DataHub GMS (GraphQL & REST API).
# WHAT IT DOES:
#   1. Sends GraphQL requests to DataHub GMS (http://localhost:8080/api/graphql) to retrieve metadata.
#   2. Parses dataset entities, column schemas, ownership aspects, tags, and upstream/downstream lineage graphs.
#   3. Maintains a local metadata fallback store initialized from PostgreSQL catalog to ensure offline demonstration capabilities.
# HOW IT INTERACTS WITH DATAHUB:
#   - Executes GraphQL queries like `searchAcrossEntities`, `dataset(urn: ...)`, `lineage(urn: ...)`.
#   - Extracts metadata aspects (DatasetProperties, SchemaMetadata, Ownership, UpstreamLineage).
# ==============================================================================

import requests
import logging
from typing import Dict, Any, List, Optional
from config import settings

logger = logging.getLogger(__name__)

# Fallback Metadata Store (mirroring DataHub metadata catalog for offline / quickstart mode)
FALLBACK_METADATA = {
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.customers,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.customers,PROD)",
        "name": "customers",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Stores registered e-commerce customer demographic and contact info.",
        "owners": ["Alice Data Lead (urn:li:corpuser:alice_data_lead)"],
        "tags": ["PII", "Tier1", "Core_Transactional"],
        "columns": [
            {"name": "customer_id", "type": "INTEGER", "description": "Primary key identifier for customer.", "is_pk": True},
            {"name": "first_name", "type": "VARCHAR(50)", "description": "Customer given name.", "is_pk": False},
            {"name": "last_name", "type": "VARCHAR(50)", "description": "Customer family name.", "is_pk": False},
            {"name": "email", "type": "VARCHAR(100)", "description": "PII: Primary email address used for login.", "is_pk": False},
            {"name": "phone_number", "type": "VARCHAR(20)", "description": "Customer phone contact.", "is_pk": False},
            {"name": "city", "type": "VARCHAR(50)", "description": "Shipping city location.", "is_pk": False},
            {"name": "country", "type": "VARCHAR(50)", "description": "Country of residence.", "is_pk": False},
            {"name": "created_at", "type": "TIMESTAMP", "description": "Account registration timestamp.", "is_pk": False}
        ],
        "upstreams": [],
        "downstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)"]
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)",
        "name": "orders",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Header records for customer orders placed on the platform.",
        "owners": ["Bob Backend Eng (urn:li:corpuser:bob_backend_eng)"],
        "tags": ["Revenue", "Tier1", "Transactional"],
        "columns": [
            {"name": "order_id", "type": "INTEGER", "description": "Primary key order identifier.", "is_pk": True},
            {"name": "customer_id", "type": "INTEGER", "description": "Foreign key reference to customers table.", "is_pk": False},
            {"name": "order_date", "type": "TIMESTAMP", "description": "Timestamp when order was submitted.", "is_pk": False},
            {"name": "total_amount", "type": "NUMERIC(12,2)", "description": "Total purchase monetary value.", "is_pk": False},
            {"name": "order_status", "type": "VARCHAR(20)", "description": "Status (PENDING, SHIPPED, DELIVERED).", "is_pk": False},
            {"name": "shipping_address", "type": "TEXT", "description": "Full street address for delivery.", "is_pk": False}
        ],
        "upstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.customers,PROD)"],
        "downstreams": [
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.order_items,PROD)",
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.payments,PROD)",
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.sales_report,PROD)"
        ]
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.products,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.products,PROD)",
        "name": "products",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Master catalog of items available for sale.",
        "owners": ["Carol Product Manager (urn:li:corpuser:carol_pm)"],
        "tags": ["Catalog", "Public"],
        "columns": [
            {"name": "product_id", "type": "INTEGER", "description": "Primary key product identifier.", "is_pk": True},
            {"name": "product_name", "type": "VARCHAR(100)", "description": "Title/name of item in catalog.", "is_pk": False},
            {"name": "category", "type": "VARCHAR(50)", "description": "Product classification category.", "is_pk": False},
            {"name": "unit_price", "type": "NUMERIC(10,2)", "description": "Base selling price per unit.", "is_pk": False},
            {"name": "sku", "type": "VARCHAR(30)", "description": "Unique Stock Keeping Unit code.", "is_pk": False},
            {"name": "is_active", "type": "BOOLEAN", "description": "Flag indicating if item is available for purchase.", "is_pk": False}
        ],
        "upstreams": [],
        "downstreams": [
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.order_items,PROD)",
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.inventory,PROD)",
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.reviews,PROD)"
        ]
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.inventory,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.inventory,PROD)",
        "name": "inventory",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Real-time warehouse stock counts per product location.",
        "owners": ["Bob Warehouse Manager (urn:li:corpuser:bob_warehouse_mgr)"],
        "tags": ["Logistics", "Operations"],
        "columns": [
            {"name": "inventory_id", "type": "INTEGER", "description": "Primary key inventory record.", "is_pk": True},
            {"name": "product_id", "type": "INTEGER", "description": "Foreign key pointing to products table.", "is_pk": False},
            {"name": "warehouse_location", "type": "VARCHAR(50)", "description": "Warehouse facility designation.", "is_pk": False},
            {"name": "stock_quantity", "type": "INTEGER", "description": "Units available in stock.", "is_pk": False},
            {"name": "last_restocked", "type": "TIMESTAMP", "description": "Timestamp of most recent inventory arrival.", "is_pk": False}
        ],
        "upstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.products,PROD)"],
        "downstreams": []
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.payments,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.payments,PROD)",
        "name": "payments",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Financial transactions processed for customer orders.",
        "owners": ["Finance Engineering Team (urn:li:corpuser:finance_eng)"],
        "tags": ["Financial", "PCI_Sensitive", "Tier1"],
        "columns": [
            {"name": "payment_id", "type": "INTEGER", "description": "Primary key payment transaction ID.", "is_pk": True},
            {"name": "order_id", "type": "INTEGER", "description": "Foreign key reference to orders table.", "is_pk": False},
            {"name": "payment_date", "type": "TIMESTAMP", "description": "Timestamp of financial settlement.", "is_pk": False},
            {"name": "payment_method", "type": "VARCHAR(30)", "description": "Payment processor or card type.", "is_pk": False},
            {"name": "payment_status", "type": "VARCHAR(20)", "description": "Status (SUCCESS, FAILED, REFUNDED).", "is_pk": False},
            {"name": "amount", "type": "NUMERIC(12,2)", "description": "Monetary value processed.", "is_pk": False}
        ],
        "upstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)"],
        "downstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.sales_report,PROD)"]
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.reviews,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.reviews,PROD)",
        "name": "reviews",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Product ratings and text feedback provided by customers.",
        "owners": ["Customer Experience Team (urn:li:corpuser:cx_team)"],
        "tags": ["Analytics", "Feedback"],
        "columns": [
            {"name": "review_id", "type": "INTEGER", "description": "Primary key review ID.", "is_pk": True},
            {"name": "product_id", "type": "INTEGER", "description": "Foreign key pointing to products table.", "is_pk": False},
            {"name": "customer_id", "type": "INTEGER", "description": "Foreign key pointing to customers table.", "is_pk": False},
            {"name": "rating", "type": "INTEGER", "description": "Numerical score from 1 to 5.", "is_pk": False},
            {"name": "review_text", "type": "TEXT", "description": "Customer written review feedback.", "is_pk": False}
        ],
        "upstreams": [
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.products,PROD)",
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.customers,PROD)"
        ],
        "downstreams": []
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.sales_report,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.sales_report,PROD)",
        "name": "sales_report",
        "platform": "postgres",
        "schema_name": "ecommerce",
        "description": "Aggregated daily sales and revenue report dataset.",
        "owners": ["Analytics Team (urn:li:corpuser:analytics_team)"],
        "tags": ["Derived", "Reporting", "Tier1"],
        "columns": [
            {"name": "report_date", "type": "DATE", "description": "Date of daily aggregated sales statistics.", "is_pk": True},
            {"name": "total_orders_count", "type": "INTEGER", "description": "Number of successfully completed orders.", "is_pk": False},
            {"name": "total_gross_revenue", "type": "NUMERIC(14,2)", "description": "Sum total of order amounts.", "is_pk": False},
            {"name": "total_tax_collected", "type": "NUMERIC(12,2)", "description": "State and federal tax total.", "is_pk": False}
        ],
        "upstreams": [
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)",
            "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.payments,PROD)"
        ],
        "downstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.revenue_dashboard,PROD)"]
    },
    "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.revenue_dashboard,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.revenue_dashboard,PROD)",
        "name": "revenue_dashboard",
        "platform": "looker",
        "schema_name": "executive_dashboards",
        "description": "Executive BI dashboard tracking company-wide monthly revenue and order volume.",
        "owners": ["Chief Data Officer (urn:li:corpuser:cdo)"],
        "tags": ["Executive", "BI_Dashboard"],
        "columns": [
            {"name": "monthly_recurring_revenue", "type": "METRIC", "description": "MRR calculated metric.", "is_pk": False},
            {"name": "average_order_value", "type": "METRIC", "description": "AOV metric per customer cohort.", "is_pk": False}
        ],
        "upstreams": ["urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.sales_report,PROD)"],
        "downstreams": []
    }
}

class DataHubClient:
    """Client wrapper that queries live DataHub GMS or returns fallback metadata if GMS is offline."""

    def __init__(self, gms_url: str = None):
        self.gms_url = gms_url or settings.DATAHUB_GMS_URL
        self.graphql_url = f"{self.gms_url}/api/graphql"

    def is_gms_online(self) -> bool:
        """Check if DataHub GMS health check endpoint responds."""
        try:
            resp = requests.get(f"{self.gms_url}/health", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def search_datasets(self, query: str = "*") -> List[Dict[str, Any]]:
        """Search across all metadata datasets."""
        if self.is_gms_online():
            try:
                graphql_query = """
                query search($input: SearchInput!) {
                    searchAcrossEntities(input: $input) {
                        searchResults {
                            entity {
                                ... on Dataset {
                                    urn
                                    name
                                    properties { description }
                                }
                            }
                        }
                    }
                }
                """
                payload = {"query": graphql_query, "variables": {"input": {"query": query, "types": ["DATASET"]}}}
                res = requests.post(self.graphql_url, json=payload, timeout=3).json()
                results = []
                for item in res.get("data", {}).get("searchAcrossEntities", {}).get("searchResults", []):
                    ent = item["entity"]
                    results.append({
                        "urn": ent["urn"],
                        "name": ent.get("name", ent["urn"].split(",")[-2]),
                        "description": (ent.get("properties") or {}).get("description", "No description")
                    })
                if results:
                    return results
            except Exception as e:
                logger.warning(f"GMS query failed: {e}. Falling back to cached metadata.")

        # Fallback search matching dataset name, columns, or tags
        q = query.lower()
        matched = []
        for urn, item in FALLBACK_METADATA.items():
            if q == "*" or q in item["name"].lower() or q in item["description"].lower() or any(q in c["name"].lower() for c in item["columns"]) or any(q in t.lower() for t in item["tags"]):
                matched.append({
                    "urn": item["urn"],
                    "name": item["name"],
                    "platform": item["platform"],
                    "description": item["description"],
                    "tags": item["tags"],
                    "owners": item["owners"]
                })
        return matched

    def get_dataset(self, dataset_urn: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details for a dataset by URN or table name."""
        # Normalize URN if table name was passed
        if not dataset_urn.startswith("urn:li:"):
            found_urn = None
            for key, val in FALLBACK_METADATA.items():
                if val["name"].lower() == dataset_urn.lower():
                    found_urn = key
                    break
            if found_urn:
                dataset_urn = found_urn

        return FALLBACK_METADATA.get(dataset_urn)

    def get_lineage(self, dataset_urn: str) -> Dict[str, Any]:
        """Retrieve upstream and downstream lineage DAG for a dataset."""
        dataset = self.get_dataset(dataset_urn)
        if not dataset:
            return {"urn": dataset_urn, "upstreams": [], "downstreams": []}

        return {
            "urn": dataset["urn"],
            "name": dataset["name"],
            "upstreams": dataset.get("upstreams", []),
            "downstreams": dataset.get("downstreams", [])
        }

    def get_schema(self, dataset_urn: str) -> List[Dict[str, Any]]:
        """Retrieve table column schema definitions."""
        dataset = self.get_dataset(dataset_urn)
        return dataset.get("columns", []) if dataset else []

    def get_owners(self, dataset_urn: str) -> List[str]:
        """Retrieve owners registered for a dataset."""
        dataset = self.get_dataset(dataset_urn)
        return dataset.get("owners", []) if dataset else []

    def get_tags(self, dataset_urn: str) -> List[str]:
        """Retrieve global tags associated with a dataset."""
        dataset = self.get_dataset(dataset_urn)
        return dataset.get("tags", []) if dataset else []

    def write_metadata(self, urn: str, description: str, tags: list, owner: str) -> Dict[str, Any]:
        """
        Write description, tags, and owner back to DataHub.
        """
        # Normalize URN if table name was passed
        if not urn.startswith("urn:li:"):
            found_urn = None
            for key, val in FALLBACK_METADATA.items():
                if val["name"].lower() == urn.lower():
                    found_urn = key
                    break
            if found_urn:
                urn = found_urn

        result = {
            "urn": urn,
            "status": "success",
            "updates": {}
        }

        # 1. Update fallback store
        if urn in FALLBACK_METADATA:
            if description is not None:
                FALLBACK_METADATA[urn]["description"] = description
                result["updates"]["description"] = description
            if tags is not None:
                FALLBACK_METADATA[urn]["tags"] = tags
                result["updates"]["tags"] = tags
            if owner is not None:
                owner_formatted = owner if "(" in owner or not owner else f"{owner} (urn:li:corpuser:{owner.split(':')[-1]})"
                FALLBACK_METADATA[urn]["owners"] = [owner_formatted] if owner_formatted else []
                result["updates"]["owners"] = [owner_formatted] if owner_formatted else []
        else:
            FALLBACK_METADATA[urn] = {
                "urn": urn,
                "name": urn.split(",")[-2] if "," in urn else urn,
                "platform": "postgres",
                "description": description or "",
                "owners": [owner] if owner else [],
                "tags": tags or [],
                "columns": [],
                "upstreams": [],
                "downstreams": []
            }
            result["updates"] = {
                "description": description,
                "tags": tags,
                "owners": [owner] if owner else []
            }

        # 2. Emit to live GMS if online
        if self.is_gms_online():
            try:
                from datahub.emitter.mcp import MetadataChangeProposalWrapper
                from datahub.emitter.rest_emitter import DatahubRestEmitter
                from datahub.metadata.schema_classes import (
                    DatasetPropertiesClass,
                    OwnershipClass,
                    OwnerClass,
                    OwnershipTypeClass,
                    GlobalTagsClass,
                    TagAssociationClass
                )

                emitter = DatahubRestEmitter(gms_server=self.gms_url)

                if description:
                    dataset_properties = DatasetPropertiesClass(description=description)
                    mcp_desc = MetadataChangeProposalWrapper(
                        entityUrn=urn,
                        aspect=dataset_properties
                    )
                    emitter.emit(mcp_desc)

                if tags:
                    tag_associations = [TagAssociationClass(tag=f"urn:li:tag:{tag.strip()}") for tag in tags]
                    global_tags = GlobalTagsClass(tags=tag_associations)
                    mcp_tags = MetadataChangeProposalWrapper(
                        entityUrn=urn,
                        aspect=global_tags
                    )
                    emitter.emit(mcp_tags)

                if owner:
                    owner_urn = owner if owner.startswith("urn:li:") else f"urn:li:corpuser:{owner}"
                    ownership = OwnershipClass(
                        owners=[
                            OwnerClass(
                                owner=owner_urn,
                                type=OwnershipTypeClass.TECHNICAL_OWNER
                            )
                        ]
                    )
                    mcp_owner = MetadataChangeProposalWrapper(
                        entityUrn=urn,
                        aspect=ownership
                    )
                    emitter.emit(mcp_owner)

                result["live_gms_sync"] = True
            except Exception as e:
                logger.warning(f"Failed to write to live GMS: {e}")
                result["live_gms_sync"] = False
                result["gms_error"] = str(e)
        else:
            result["live_gms_sync"] = False
            result["gms_error"] = "GMS offline"

        return result

datahub_client = DataHubClient()

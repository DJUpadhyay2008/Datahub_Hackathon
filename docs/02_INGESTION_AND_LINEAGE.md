# 🔄 Metadata Ingestion & Lineage Emissions

## 📥 1. How Metadata Ingestion Works (Step 2)

Metadata Ingestion is the process of extracting technical and operational metadata from source databases and pushing it into DataHub.

DataHub supports two ingestion modes:
1. **Pull-based Ingestion (Crawling)**: A DataHub CLI crawler connects directly to PostgreSQL (`postgres-demo`), queries `information_schema` and `pg_catalog`, parses comments and schemas, and pushes aspects to `datahub-gms`.
2. **Push-based Ingestion (Event/API)**: Pipelines push metadata directly to DataHub GMS via REST emitter APIs during execution.

### Recipe YAML Structure (`docker/datahub-ingestion/postgres_ingestion.yml`)
```yaml
source:
  type: postgres
  config:
    host_port: "localhost:5432"
    username: "demo_user"
    password: "demo_password"
    database: "ecommerce_db"
    schema_pattern:
      allow: ["ecommerce"]
sink:
  type: "datahub-rest"
  config:
    server: "http://localhost:8080"
```

---

## 🔗 2. How Lineage Creation Works (Step 3)

Lineage documents the end-to-end flow of data across systems.

### Scenario Lineage Flow:
```
[customers] ──► [orders] ──► [sales_report] ──► [revenue_dashboard]
```

### Why Lineage Matters:
1. **Impact Analysis**: Know what reports or dashboards will break *before* deleting a column or table.
2. **Root Cause Analysis**: Track data quality bugs backward from a broken dashboard to the original source table.
3. **Regulatory Compliance**: Trace how PII customer data moves into downstream analytics data stores.

### Emitting Lineage Programmatically (`docker/datahub-ingestion/lineage_emission.py`):
```python
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import UpstreamClass, UpstreamLineageClass

emitter = DatahubRestEmitter(gms_server="http://localhost:8080")

lineage_aspect = UpstreamLineageClass(
    upstreams=[
        UpstreamClass(
            dataset="urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.customers,PROD)",
            type="TRANSFORMED"
        )
    ]
)

mcp = MetadataChangeProposalWrapper(
    entityUrn="urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD)",
    aspect=lineage_aspect
)
emitter.emit(mcp)
```

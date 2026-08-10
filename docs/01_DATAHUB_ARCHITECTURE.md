# 🏛️ DataHub Architecture & Container Service Deep Dive

## 🌟 What is DataHub?
DataHub is an open-source metadata platform designed for data discovery, data governance, lineage tracking, and data quality monitoring across modern data stacks.

---

## 🐳 DataHub Docker Container Breakdown (Step 1)

When running `docker compose up`, DataHub starts 7 core microservices:

| Container Name | Port | Purpose | Internal Interaction with DataHub |
| :--- | :--- | :--- | :--- |
| **`postgres-demo`** | `5432` | Sample E-Commerce Database | Serves transactional tables (Customers, Orders, Products, Payments, Inventory, Reviews). DataHub ingests metadata from here. |
| **`zookeeper`** | `2181` | Cluster Coordinator | Manages metadata state and leader elections for Apache Kafka. |
| **`kafka`** | `9092` | Distributed Event Streaming | Serves as the asynchronous event hub. All metadata edits publish `MetadataChangeProposal` (MCP) events to Kafka topics. |
| **`schema-registry`** | `8081` | Avro Schema Registry | Enforces Avro schema structures for Kafka metadata events. |
| **`elasticsearch`** | `9200` | Search Engine & Index | Indexes all metadata aspects (table names, column descriptions, tags, owners) to enable fast full-text search and filtering. |
| **`datahub-gms`** | `8080` | Generalized Metadata Service (GMS) | **The Core Brain of DataHub!** Exposes GraphQL & REST APIs, manages metadata persistence, processes lineage, and executes search queries. |
| **`datahub-frontend`** | `9002` | Web UI Dashboard | React-based web dashboard allowing users to visually inspect catalog, edit tags, and view lineage trees. |

---

## 🧠 What is an Aspect?
In DataHub's metadata model, entities (like a Dataset) are defined by modular **Aspects**:
* **`DatasetProperties`**: Description, custom properties, display name.
* **`SchemaMetadata`**: Columns, data types, primary keys, foreign keys.
* **`Ownership`**: List of owners and ownership types (Technical Owner, Business Owner).
* **`GlobalTags`**: Array of governance tags (e.g., `PII`, `Tier1`, `Financial`).
* **`UpstreamLineage`**: List of upstream dataset URNs feeding data into this entity.

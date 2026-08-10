# DataHub Metadata Autodoc Agent Report
**Status**: Dry-Run Mode (No metadata written back to DataHub)
**Undocumented Datasets Found**: 2

---

## 1. Dataset: `reviews`
- **URN**: `urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.reviews,PROD)`
- **Platform**: `postgres`
- **Missing Aspects**: description, owners, tags

### Grounded Schema & Lineage Details
- **Columns**:
  - `review_id` (INTEGER): Primary key review ID.
  - `product_id` (INTEGER): Foreign key pointing to products table.
  - `customer_id` (INTEGER): Foreign key pointing to customers table.
  - `rating` (INTEGER): Numerical score from 1 to 5.
  - `review_text` (TEXT): Customer written review feedback.
- **Upstream Lineage**: urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.products,PROD), urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.customers,PROD)
- **Downstream Lineage**: None

### Generated Metadata Suggestions (Dry-Run)
- **Suggested Description**: Stores customer reviews, including the rating score and written feedback, linked to specific products and the customer who submitted the review.
- **Suggested Tags**: Feedback, Catalog, Analytics, PII
- **Suggested Owner**: `Carol Product Manager or Analytics Team`
- **Confidence Note**: *The description is derived directly from the columns (review_id, rating, review_text, product_id, customer_id). The suggested tags reflect the linkage to products (Catalog), customers (PII), and its primary use case (Feedback/Analytics). The suggested owner is based on the upstream dependencies on the 'products' table (Carol Product Manager) and its nature as an analytical dataset.*

---

## 2. Dataset: `order_items`
- **URN**: `urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.order_items,PROD)`
- **Platform**: `postgres`
- **Missing Aspects**: description, owners, tags

### Grounded Schema & Lineage Details
- **Columns**:
  - `order_id` (INTEGER): Foreign key reference to orders table.
  - `product_id` (INTEGER): Foreign key pointing to products table.
  - `quantity` (INTEGER): Number of items ordered.
  - `price` (NUMERIC(10,2)): Unit price of the product at order time.
- **Upstream Lineage**: urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.orders,PROD), urn:li:dataset:(urn:li:dataPlatform:postgres,ecommerce_db.ecommerce.products,PROD)
- **Downstream Lineage**: None

### Generated Metadata Suggestions (Dry-Run)
- **Suggested Description**: Contains the line items for each customer order, detailing which products were included, the quantity ordered, and the unit price of the product at the time of the order.
- **Suggested Tags**: Transactional, Revenue, Catalog, Operations
- **Suggested Owner**: `Bob Backend Eng`
- **Confidence Note**: *The description and tags are derived directly from the schema, which links orders and products. The suggested owner is based on the upstream dependency on the 'orders' table, which is owned by Bob Backend Eng, indicating this is core transactional data managed by the backend system.*

---

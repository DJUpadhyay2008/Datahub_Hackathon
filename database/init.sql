-- ==============================================================================
-- FILE: database/init.sql
-- WHY THIS FILE EXISTS:
--   This SQL script initializes the sample PostgreSQL database representing an
--   e-commerce transactional system. It creates tables for Customers, Orders,
--   Products, Payments, Inventory, and Reviews with realistic constraints and seeds sample data.
-- WHAT IT DOES:
--   1. Drops existing tables if present to allow idempotent database resets.
--   2. Defines schema DDL (Data Definition Language) with primary keys, foreign keys, and comments.
--   3. Inserts rich sample dataset records for demonstration.
-- HOW IT INTERACTS WITH DATAHUB:
--   DataHub's PostgreSQL ingestion plugin connects to this database, reads the system
--   catalog (pg_catalog, information_schema, table comments, column types), and extracts table
--   schemas, column descriptions, and primary/foreign key relationships into DataHub metadata aspects.
-- ==============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS ecommerce;

-- Set search path
SET search_path TO ecommerce, public;

-- Drop tables if they exist (clean setup)
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ------------------------------------------------------------------------------
-- 1. CUSTOMERS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    city VARCHAR(50),
    country VARCHAR(50) DEFAULT 'USA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE customers IS 'Stores registered e-commerce customer demographic and contact info.';
COMMENT ON COLUMN customers.email IS 'PII: Customer primary email address used for login and notifications.';

-- ------------------------------------------------------------------------------
-- 2. PRODUCTS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    sku VARCHAR(30) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE products IS 'Master catalog of items available for sale.';
COMMENT ON COLUMN products.sku IS 'Stock Keeping Unit identifier for catalog operations.';

-- ------------------------------------------------------------------------------
-- 3. ORDERS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(12, 2) NOT NULL,
    order_status VARCHAR(20) DEFAULT 'PENDING',
    shipping_address TEXT NOT NULL
);

COMMENT ON TABLE orders IS 'Header records for customer orders placed on the platform.';
COMMENT ON COLUMN orders.order_status IS 'State of order (PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED).';

-- ------------------------------------------------------------------------------
-- 4. ORDER ITEMS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL
);

COMMENT ON TABLE order_items IS 'Line item details for each order link products to orders.';

-- ------------------------------------------------------------------------------
-- 5. PAYMENTS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(30) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'SUCCESS',
    amount NUMERIC(12, 2) NOT NULL
);

COMMENT ON TABLE payments IS 'Financial transactions processed for customer orders.';
COMMENT ON COLUMN payments.payment_method IS 'Method used (CREDIT_CARD, PAYPAL, STRIPE, BANK_TRANSFER).';

-- ------------------------------------------------------------------------------
-- 6. INVENTORY TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    warehouse_location VARCHAR(50) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    last_restocked TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE inventory IS 'Real-time warehouse stock counts per product location.';

-- ------------------------------------------------------------------------------
-- 7. REVIEWS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE reviews IS 'Product ratings and text feedback provided by customers.';

-- ==============================================================================
-- SEED SAMPLE DATA
-- ==============================================================================

-- Insert Customers
INSERT INTO customers (first_name, last_name, email, phone_number, city, country) VALUES
('Alice', 'Smith', 'alice.smith@example.com', '+1-555-0192', 'New York', 'USA'),
('Bob', 'Jones', 'bob.jones@example.com', '+1-555-0193', 'San Francisco', 'USA'),
('Charlie', 'Brown', 'charlie.b@example.com', '+1-555-0194', 'Chicago', 'USA'),
('Diana', 'Prince', 'diana.prince@example.com', '+1-555-0195', 'Seattle', 'USA'),
('Evan', 'Wright', 'evan.wright@example.com', '+1-555-0196', 'Austin', 'USA');

-- Insert Products
INSERT INTO products (product_name, category, unit_price, sku) VALUES
('UltraWireless Noise-Canceling Headphones', 'Electronics', 249.99, 'SKU-HEAD-001'),
('Ergonomic Mechanical Keyboard', 'Electronics', 129.50, 'SKU-KEYB-002'),
('Organic Arabica Coffee Beans 1kg', 'Groceries', 24.99, 'SKU-COFF-003'),
('Stainless Steel Thermal Water Bottle 1L', 'Home & Kitchen', 34.00, 'SKU-BOTT-004'),
('4K UltraHD Monitor 27-inch', 'Electronics', 399.99, 'SKU-MONI-005');

-- Insert Orders
INSERT INTO orders (customer_id, total_amount, order_status, shipping_address) VALUES
(1, 274.98, 'DELIVERED', '123 Broadway St, New York, NY 10001'),
(2, 129.50, 'SHIPPED', '456 Market St, San Francisco, CA 94105'),
(3, 424.98, 'DELIVERED', '789 Michigan Ave, Chicago, IL 60611'),
(1, 34.00, 'PROCESSING', '123 Broadway St, New York, NY 10001'),
(4, 399.99, 'DELIVERED', '101 Pine St, Seattle, WA 98101');

-- Insert Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 249.99),
(1, 3, 1, 24.99),
(2, 2, 1, 129.50),
(3, 3, 1, 24.99),
(3, 5, 1, 399.99),
(4, 4, 1, 34.00),
(5, 5, 1, 399.99);

-- Insert Payments
INSERT INTO payments (order_id, payment_method, payment_status, amount) VALUES
(1, 'CREDIT_CARD', 'SUCCESS', 274.98),
(2, 'STRIPE', 'SUCCESS', 129.50),
(3, 'PAYPAL', 'SUCCESS', 424.98),
(4, 'CREDIT_CARD', 'SUCCESS', 34.00),
(5, 'CREDIT_CARD', 'SUCCESS', 399.99);

-- Insert Inventory
INSERT INTO inventory (product_id, warehouse_location, stock_quantity) VALUES
(1, 'WH-EAST-A1', 45),
(2, 'WH-WEST-B2', 120),
(3, 'WH-CENTRAL-C3', 300),
(4, 'WH-EAST-A2', 85),
(5, 'WH-WEST-B1', 15);

-- Insert Reviews
INSERT INTO reviews (product_id, customer_id, rating, review_text) VALUES
(1, 1, 5, 'Amazing sound quality and active noise cancellation!'),
(2, 2, 4, 'Great tactile feedback, but slightly loud switches.'),
(3, 1, 5, 'Best coffee beans I have purchased online.'),
(5, 4, 5, 'Crisp 4K resolution and sharp text for programming work.');

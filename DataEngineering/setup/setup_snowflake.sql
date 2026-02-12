-- ============================================================================
-- Snowflake Setup Script for Data Engineering Agent
-- ============================================================================
-- This script creates the necessary database structure and sample raw data
-- to demonstrate data engineering pipelines with dbt.
--
-- Run this script in your Snowflake console or using SnowSQL:
--   snowsql -a <account> -u <user> -f setup_snowflake.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Create Warehouse, Database, and Schemas
-- ----------------------------------------------------------------------------

CREATE WAREHOUSE IF NOT EXISTS DATA_ENGINEERING_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'Warehouse for data engineering agent demo';

USE WAREHOUSE DATA_ENGINEERING_WH;

CREATE DATABASE IF NOT EXISTS DATA_ENGINEERING_DB
    COMMENT = 'Database for data engineering agent demo';

USE DATABASE DATA_ENGINEERING_DB;

-- Create schema structure following medallion architecture
CREATE SCHEMA IF NOT EXISTS RAW COMMENT = 'Raw data ingested from source systems';
CREATE SCHEMA IF NOT EXISTS STAGING COMMENT = 'Cleaned and standardized data';
CREATE SCHEMA IF NOT EXISTS INTERMEDIATE COMMENT = 'Business logic and transformations';
CREATE SCHEMA IF NOT EXISTS MARTS COMMENT = 'Final analytics-ready tables';

-- ----------------------------------------------------------------------------
-- 2. Create Raw Data Tables (simulating data ingestion)
-- ----------------------------------------------------------------------------

USE SCHEMA RAW;

-- Raw customers from CRM system
CREATE OR REPLACE TABLE raw_customers (
    _id VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email_address VARCHAR(255),
    phone VARCHAR(50),
    address_line_1 VARCHAR(255),
    city VARCHAR(100),
    state_code VARCHAR(10),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    created_timestamp VARCHAR(50),
    updated_timestamp VARCHAR(50),
    is_active VARCHAR(10),
    customer_segment VARCHAR(50),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw orders from e-commerce platform
CREATE OR REPLACE TABLE raw_orders (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    order_date VARCHAR(50),
    order_status VARCHAR(50),
    shipping_method VARCHAR(50),
    shipping_address VARCHAR(500),
    subtotal VARCHAR(20),
    tax_amount VARCHAR(20),
    shipping_cost VARCHAR(20),
    discount_amount VARCHAR(20),
    total_amount VARCHAR(20),
    currency_code VARCHAR(10),
    payment_method VARCHAR(50),
    notes TEXT,
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw order line items
CREATE OR REPLACE TABLE raw_order_items (
    order_item_id VARCHAR(50),
    order_id VARCHAR(50),
    product_id VARCHAR(50),
    product_name VARCHAR(255),
    quantity VARCHAR(10),
    unit_price VARCHAR(20),
    discount_percent VARCHAR(10),
    line_total VARCHAR(20),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw products from inventory system
CREATE OR REPLACE TABLE raw_products (
    sku VARCHAR(50),
    product_name VARCHAR(255),
    product_description TEXT,
    category_id VARCHAR(50),
    category_name VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    supplier_id VARCHAR(50),
    unit_cost VARCHAR(20),
    list_price VARCHAR(20),
    weight_kg VARCHAR(20),
    is_active VARCHAR(10),
    created_date VARCHAR(50),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw inventory levels
CREATE OR REPLACE TABLE raw_inventory (
    inventory_id VARCHAR(50),
    product_sku VARCHAR(50),
    warehouse_id VARCHAR(50),
    warehouse_name VARCHAR(100),
    quantity_on_hand VARCHAR(10),
    quantity_reserved VARCHAR(10),
    quantity_available VARCHAR(10),
    reorder_point VARCHAR(10),
    last_count_date VARCHAR(50),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw web events for clickstream analysis (simplified - no JSON)
CREATE OR REPLACE TABLE raw_web_events (
    event_id VARCHAR(100),
    session_id VARCHAR(100),
    user_id VARCHAR(50),
    event_type VARCHAR(50),
    event_timestamp VARCHAR(50),
    page_url VARCHAR(500),
    referrer_url VARCHAR(500),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    ip_address VARCHAR(50),
    country_code VARCHAR(10),
    event_category VARCHAR(100),
    event_value VARCHAR(255),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ----------------------------------------------------------------------------
-- 3. Insert Sample Raw Data
-- ----------------------------------------------------------------------------

-- Insert raw customers (with intentional data quality issues)
INSERT INTO raw_customers (_id, first_name, last_name, email_address, phone, address_line_1, city, state_code, postal_code, country, created_timestamp, updated_timestamp, is_active, customer_segment) VALUES
    ('C001', 'John', 'Smith', 'john.smith@email.com', '555-0101', '123 Main St', 'New York', 'NY', '10001', 'USA', '2023-01-15 10:30:00', '2024-01-15 14:20:00', 'true', 'Premium'),
    ('C002', 'Sarah', 'Johnson', 'SARAH.J@EMAIL.COM', '555-0102', '456 Oak Ave', 'Los Angeles', 'CA', '90001', 'USA', '2023-02-20 14:45:00', '2024-02-10 09:15:00', 'true', 'Standard'),
    ('C003', 'Michael', 'Williams', 'mike.w@email.com', NULL, '789 Pine Rd', 'Chicago', 'IL', '60601', 'USA', '2023-03-10 09:15:00', '2024-03-05 16:30:00', 'true', 'Premium'),
    ('C004', 'Emily', 'Brown', 'emily.b@email.com', '555-0104', '321 Elm St', 'Houston', 'TX', '77001', 'USA', '2023-04-05 16:20:00', '2024-01-20 11:45:00', 'false', 'Standard'),
    ('C005', 'David', 'Jones', 'david.j@email.com', '555-0105', '654 Maple Dr', 'Phoenix', 'AZ', '85001', 'USA', '2023-05-12 11:00:00', '2024-02-28 08:30:00', 'true', 'Premium'),
    ('C006', 'Lisa', 'Garcia', 'lisa.g@email.com', '555-0106', '987 Cedar Ln', 'San Diego', 'CA', '92101', 'USA', '2023-06-18 13:30:00', '2024-03-15 10:00:00', 'true', 'Standard'),
    ('C007', 'James', 'Miller', 'james.m@email.com', '555-0107', '147 Birch Blvd', 'Dallas', 'TX', '75201', 'USA', '2023-07-22 08:45:00', '2024-01-05 15:20:00', 'true', 'Premium'),
    ('C008', 'Jennifer', 'Davis', 'jen.d@email.com', '', '258 Walnut Way', 'San Jose', 'CA', '95101', 'USA', '2023-08-30 15:00:00', '2024-02-18 12:10:00', 'true', 'Standard'),
    ('C009', 'Robert', 'Martinez', 'rob.m@email.com', '555-0109', '369 Spruce St', 'Austin', 'TX', '78701', 'USA', '2023-09-14 10:15:00', '2024-03-01 09:45:00', 'true', 'Premium'),
    ('C010', 'Amanda', 'Anderson', 'amanda.a@email.com', '555-0110', '741 Willow Ave', 'Seattle', 'WA', '98101', 'USA', '2023-10-25 12:00:00', NULL, 'true', 'Standard'),
    ('C011', 'Christopher', 'Taylor', 'chris.t@email.com', '555-0111', '852 Ash Ct', 'Denver', 'CO', '80201', 'USA', '2023-11-08 14:30:00', '2024-01-30 16:00:00', 'true', 'Premium'),
    ('C012', 'Jessica', 'Thomas', 'jess.t@email.com', '555-0112', '963 Oak Park', 'Boston', 'MA', '02101', 'USA', '2023-12-01 09:00:00', '2024-02-25 11:30:00', 'true', 'Standard'),
    ('C001', 'John', 'Smith', 'johnsmith@gmail.com', '555-0101', '123 Main Street', 'New York', 'NY', '10001', 'USA', '2023-01-15 10:30:00', '2024-03-20 10:00:00', 'true', 'Premium'),
    ('C013', '', 'Unknown', 'invalid-email', '12345', '', '', 'XX', '00000', '', '2024-01-01', NULL, 'maybe', '');

-- Insert raw products
INSERT INTO raw_products (sku, product_name, product_description, category_id, category_name, subcategory, brand, supplier_id, unit_cost, list_price, weight_kg, is_active, created_date) VALUES
    ('SKU-001', 'Laptop Pro 15', 'High-performance laptop with 15-inch display', 'CAT-01', 'Electronics', 'Computers', 'TechBrand', 'SUP-001', '899.99', '1299.99', '2.1', 'true', '2023-01-01'),
    ('SKU-002', 'Wireless Mouse', 'Ergonomic wireless mouse with long battery life', 'CAT-01', 'Electronics', 'Accessories', 'TechBrand', 'SUP-001', '15.99', '29.99', '0.1', 'true', '2023-01-01'),
    ('SKU-003', 'USB-C Hub', '7-in-1 USB-C hub with HDMI and card reader', 'CAT-01', 'Electronics', 'Accessories', 'TechBrand', 'SUP-002', '25.99', '49.99', '0.15', 'true', '2023-02-01'),
    ('SKU-004', 'Mechanical Keyboard', 'RGB mechanical keyboard with Cherry MX switches', 'CAT-01', 'Electronics', 'Accessories', 'KeyMaster', 'SUP-003', '79.99', '149.99', '0.9', 'true', '2023-02-01'),
    ('SKU-005', 'Monitor 27 inch', '4K UHD monitor with HDR support', 'CAT-01', 'Electronics', 'Displays', 'ViewTech', 'SUP-004', '249.99', '399.99', '5.5', 'true', '2023-03-01'),
    ('SKU-006', 'Office Chair', 'Ergonomic office chair with lumbar support', 'CAT-02', 'Furniture', 'Seating', 'ComfortPlus', 'SUP-005', '149.99', '299.99', '15.0', 'true', '2023-03-01'),
    ('SKU-007', 'Standing Desk', 'Electric height-adjustable standing desk', 'CAT-02', 'Furniture', 'Desks', 'WorkWell', 'SUP-005', '349.99', '599.99', '35.0', 'true', '2023-04-01'),
    ('SKU-008', 'Desk Lamp', 'LED desk lamp with adjustable brightness', 'CAT-02', 'Furniture', 'Lighting', 'BrightLife', 'SUP-006', '19.99', '39.99', '0.8', 'true', '2023-04-01'),
    ('SKU-009', 'Notebook Set', 'Premium notebook set with 3 sizes', 'CAT-03', 'Office Supplies', 'Paper', 'WriteRight', 'SUP-007', '5.99', '12.99', '0.5', 'true', '2023-05-01'),
    ('SKU-010', 'Pen Pack', 'Pack of 12 premium ballpoint pens', 'CAT-03', 'Office Supplies', 'Writing', 'WriteRight', 'SUP-007', '3.99', '8.99', '0.2', 'true', '2023-05-01'),
    ('SKU-011', 'Old Laptop Model', 'Discontinued laptop model', 'CAT-01', 'Electronics', 'Computers', 'TechBrand', 'SUP-001', '599.99', '899.99', '2.5', 'false', '2022-01-01'),
    ('SKU-012', 'Mystery Product', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'true', NULL);

-- Insert raw orders
INSERT INTO raw_orders (order_id, customer_id, order_date, order_status, shipping_method, shipping_address, subtotal, tax_amount, shipping_cost, discount_amount, total_amount, currency_code, payment_method, notes) VALUES
    ('ORD-001', 'C001', '2024-01-15 10:30:00', 'completed', 'standard', '123 Main St, New York, NY 10001', '1329.98', '106.40', '9.99', '0.00', '1446.37', 'USD', 'credit_card', NULL),
    ('ORD-002', 'C002', '2024-01-20 14:45:00', 'completed', 'express', '456 Oak Ave, Los Angeles, CA 90001', '449.98', '40.50', '14.99', '22.50', '482.97', 'USD', 'paypal', 'Gift wrap requested'),
    ('ORD-003', 'C003', '2024-02-01 09:15:00', 'completed', 'standard', '789 Pine Rd, Chicago, IL 60601', '79.98', '6.40', '9.99', '0.00', '96.37', 'USD', 'credit_card', NULL),
    ('ORD-004', 'C001', '2024-02-10 16:20:00', 'completed', 'express', '123 Main St, New York, NY 10001', '599.99', '48.00', '14.99', '60.00', '602.98', 'USD', 'credit_card', 'Repeat customer discount'),
    ('ORD-005', 'C005', '2024-02-15 11:00:00', 'completed', 'standard', '654 Maple Dr, Phoenix, AZ 85001', '1299.99', '104.00', '0.00', '0.00', '1403.99', 'USD', 'credit_card', 'Free shipping promotion'),
    ('ORD-006', 'C006', '2024-02-28 13:30:00', 'shipped', 'standard', '987 Cedar Ln, San Diego, CA 92101', '329.98', '29.70', '9.99', '16.50', '353.17', 'USD', 'debit_card', NULL),
    ('ORD-007', 'C002', '2024-03-05 08:45:00', 'shipped', 'express', '456 Oak Ave, Los Angeles, CA 90001', '149.99', '13.50', '14.99', '0.00', '178.48', 'USD', 'paypal', NULL),
    ('ORD-008', 'C007', '2024-03-10 15:00:00', 'processing', 'standard', '147 Birch Blvd, Dallas, TX 75201', '899.98', '74.25', '9.99', '45.00', '939.22', 'USD', 'credit_card', 'Loyalty discount applied'),
    ('ORD-009', 'C008', '2024-03-15 10:15:00', 'processing', 'standard', '258 Walnut Way, San Jose, CA 95101', '51.97', '4.68', '9.99', '0.00', '66.64', 'USD', 'credit_card', NULL),
    ('ORD-010', 'C009', '2024-03-20 12:00:00', 'pending', 'express', '369 Spruce St, Austin, TX 78701', '1699.98', '140.25', '14.99', '85.00', '1770.22', 'USD', 'credit_card', 'VIP customer'),
    ('ORD-011', 'C010', '2024-03-22 09:30:00', 'pending', 'standard', '741 Willow Ave, Seattle, WA 98101', '549.98', '49.50', '9.99', '27.50', '581.97', 'USD', 'paypal', NULL),
    ('ORD-012', 'C011', '2024-03-25 14:00:00', 'cancelled', 'standard', '852 Ash Ct, Denver, CO 80201', '299.99', '21.00', '9.99', '0.00', '330.98', 'USD', 'credit_card', 'Customer requested cancellation'),
    ('ORD-013', 'C999', '2024-03-26', 'unknown', '', '', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'XXX', '', NULL);

-- Insert raw order items
INSERT INTO raw_order_items (order_item_id, order_id, product_id, product_name, quantity, unit_price, discount_percent, line_total) VALUES
    ('OI-001', 'ORD-001', 'SKU-001', 'Laptop Pro 15', '1', '1299.99', '0', '1299.99'),
    ('OI-002', 'ORD-001', 'SKU-002', 'Wireless Mouse', '1', '29.99', '0', '29.99'),
    ('OI-003', 'ORD-002', 'SKU-005', 'Monitor 27 inch', '1', '399.99', '0', '399.99'),
    ('OI-004', 'ORD-002', 'SKU-003', 'USB-C Hub', '1', '49.99', '0', '49.99'),
    ('OI-005', 'ORD-003', 'SKU-002', 'Wireless Mouse', '1', '29.99', '0', '29.99'),
    ('OI-006', 'ORD-003', 'SKU-003', 'USB-C Hub', '1', '49.99', '0', '49.99'),
    ('OI-007', 'ORD-004', 'SKU-007', 'Standing Desk', '1', '599.99', '0', '599.99'),
    ('OI-008', 'ORD-005', 'SKU-001', 'Laptop Pro 15', '1', '1299.99', '0', '1299.99'),
    ('OI-009', 'ORD-006', 'SKU-006', 'Office Chair', '1', '299.99', '0', '299.99'),
    ('OI-010', 'ORD-006', 'SKU-002', 'Wireless Mouse', '1', '29.99', '0', '29.99'),
    ('OI-011', 'ORD-007', 'SKU-004', 'Mechanical Keyboard', '1', '149.99', '0', '149.99'),
    ('OI-012', 'ORD-008', 'SKU-007', 'Standing Desk', '1', '599.99', '0', '599.99'),
    ('OI-013', 'ORD-008', 'SKU-006', 'Office Chair', '1', '299.99', '0', '299.99'),
    ('OI-014', 'ORD-009', 'SKU-009', 'Notebook Set', '2', '12.99', '0', '25.98'),
    ('OI-015', 'ORD-009', 'SKU-010', 'Pen Pack', '3', '8.99', '3', '26.10'),
    ('OI-016', 'ORD-010', 'SKU-001', 'Laptop Pro 15', '1', '1299.99', '0', '1299.99'),
    ('OI-017', 'ORD-010', 'SKU-005', 'Monitor 27 inch', '1', '399.99', '0', '399.99'),
    ('OI-018', 'ORD-011', 'SKU-004', 'Mechanical Keyboard', '1', '149.99', '0', '149.99'),
    ('OI-019', 'ORD-011', 'SKU-005', 'Monitor 27 inch', '1', '399.99', '0', '399.99'),
    ('OI-020', 'ORD-012', 'SKU-006', 'Office Chair', '1', '299.99', '0', '299.99');

-- Insert raw inventory
INSERT INTO raw_inventory (inventory_id, product_sku, warehouse_id, warehouse_name, quantity_on_hand, quantity_reserved, quantity_available, reorder_point, last_count_date) VALUES
    ('INV-001', 'SKU-001', 'WH-001', 'East Coast Warehouse', '45', '5', '40', '10', '2024-03-01'),
    ('INV-002', 'SKU-001', 'WH-002', 'West Coast Warehouse', '30', '3', '27', '10', '2024-03-01'),
    ('INV-003', 'SKU-002', 'WH-001', 'East Coast Warehouse', '180', '20', '160', '50', '2024-03-01'),
    ('INV-004', 'SKU-002', 'WH-002', 'West Coast Warehouse', '150', '15', '135', '50', '2024-03-01'),
    ('INV-005', 'SKU-003', 'WH-001', 'East Coast Warehouse', '100', '10', '90', '30', '2024-03-01'),
    ('INV-006', 'SKU-004', 'WH-001', 'East Coast Warehouse', '60', '5', '55', '20', '2024-03-01'),
    ('INV-007', 'SKU-005', 'WH-001', 'East Coast Warehouse', '25', '2', '23', '10', '2024-03-01'),
    ('INV-008', 'SKU-006', 'WH-002', 'West Coast Warehouse', '35', '3', '32', '15', '2024-03-01'),
    ('INV-009', 'SKU-007', 'WH-002', 'West Coast Warehouse', '20', '2', '18', '10', '2024-03-01'),
    ('INV-010', 'SKU-008', 'WH-001', 'East Coast Warehouse', '90', '5', '85', '25', '2024-03-01'),
    ('INV-011', 'SKU-009', 'WH-001', 'East Coast Warehouse', '450', '30', '420', '100', '2024-03-01'),
    ('INV-012', 'SKU-010', 'WH-001', 'East Coast Warehouse', '950', '50', '900', '200', '2024-03-01'),
    ('INV-013', 'SKU-005', 'WH-002', 'West Coast Warehouse', '5', '4', '1', '10', '2024-03-01');

-- Insert raw web events (simplified without JSON)
INSERT INTO raw_web_events (event_id, session_id, user_id, event_type, event_timestamp, page_url, referrer_url, device_type, browser, ip_address, country_code, event_category, event_value) VALUES
    ('EVT-001', 'SESS-001', 'C001', 'page_view', '2024-03-20 10:00:00', '/products/laptop-pro-15', 'https://google.com', 'desktop', 'Chrome 122', '192.168.1.1', 'US', 'Electronics', NULL),
    ('EVT-002', 'SESS-001', 'C001', 'add_to_cart', '2024-03-20 10:05:00', '/products/laptop-pro-15', '/products/laptop-pro-15', 'desktop', 'Chrome 122', '192.168.1.1', 'US', 'Electronics', 'SKU-001'),
    ('EVT-003', 'SESS-001', 'C001', 'checkout_started', '2024-03-20 10:10:00', '/checkout', '/cart', 'desktop', 'Chrome 122', '192.168.1.1', 'US', NULL, '1299.99'),
    ('EVT-004', 'SESS-001', 'C001', 'purchase', '2024-03-20 10:15:00', '/checkout/complete', '/checkout', 'desktop', 'Chrome 122', '192.168.1.1', 'US', NULL, 'ORD-010'),
    ('EVT-005', 'SESS-002', 'C002', 'page_view', '2024-03-20 11:00:00', '/products/mechanical-keyboard', 'https://bing.com', 'mobile', 'Safari 17', '192.168.1.2', 'US', 'Electronics', NULL),
    ('EVT-006', 'SESS-002', 'C002', 'page_view', '2024-03-20 11:02:00', '/products/wireless-mouse', '/products/mechanical-keyboard', 'mobile', 'Safari 17', '192.168.1.2', 'US', 'Electronics', NULL),
    ('EVT-007', 'SESS-003', NULL, 'page_view', '2024-03-20 12:00:00', '/', 'https://google.com', 'desktop', 'Firefox 123', '192.168.1.3', 'US', NULL, NULL),
    ('EVT-008', 'SESS-003', NULL, 'page_view', '2024-03-20 12:01:00', '/products', '/', 'desktop', 'Firefox 123', '192.168.1.3', 'US', NULL, NULL),
    ('EVT-009', 'SESS-004', 'C005', 'page_view', '2024-03-21 09:00:00', '/account/orders', 'https://email.com', 'tablet', 'Chrome 122', '192.168.1.4', 'US', NULL, NULL),
    ('EVT-010', 'SESS-005', 'C007', 'add_to_cart', '2024-03-21 14:00:00', '/products/standing-desk', '/products', 'desktop', 'Chrome 122', '192.168.1.5', 'US', 'Furniture', 'SKU-007');

-- ----------------------------------------------------------------------------
-- 4. Create Service Role and User (Optional - for production use)
-- ----------------------------------------------------------------------------

-- Create a role for the data engineering agent
CREATE ROLE IF NOT EXISTS DATA_ENGINEERING_ROLE
    COMMENT = 'Role for data engineering agent with read access to raw data and write access to transformation schemas';

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE DATA_ENGINEERING_WH TO ROLE DATA_ENGINEERING_ROLE;

-- Grant database access
GRANT USAGE ON DATABASE DATA_ENGINEERING_DB TO ROLE DATA_ENGINEERING_ROLE;

-- Grant schema access
GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.RAW TO ROLE DATA_ENGINEERING_ROLE;
GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE;
GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE;
GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE;

-- Grant read access to raw data
GRANT SELECT ON ALL TABLES IN SCHEMA DATA_ENGINEERING_DB.RAW TO ROLE DATA_ENGINEERING_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.RAW TO ROLE DATA_ENGINEERING_ROLE;

-- Grant full access to transformation schemas (for dbt to create tables)
GRANT ALL ON SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE;
GRANT ALL ON SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE;
GRANT ALL ON SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE;

GRANT ALL ON ALL TABLES IN SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE;

GRANT ALL ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE;

-- ----------------------------------------------------------------------------
-- 5. Verify Setup
-- ----------------------------------------------------------------------------

SELECT 'Setup Complete! Raw data loaded:' AS status;

SELECT
    'RAW.raw_customers' AS table_name, COUNT(*) AS row_count FROM DATA_ENGINEERING_DB.RAW.raw_customers
UNION ALL SELECT 'RAW.raw_products', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_products
UNION ALL SELECT 'RAW.raw_orders', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_orders
UNION ALL SELECT 'RAW.raw_order_items', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_order_items
UNION ALL SELECT 'RAW.raw_inventory', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_inventory
UNION ALL SELECT 'RAW.raw_web_events', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_web_events
ORDER BY table_name;

#!/usr/bin/env python3
"""
Setup script for the Data Engineering Agent.

This script:
1. Creates the Snowflake database, schemas, and sample raw data
2. Initializes a sample dbt project structure

Usage:
    python setup/setup.py --snowflake    # Set up Snowflake only
    python setup/setup.py --dbt          # Set up dbt project only
    python setup/setup.py --all          # Set up both (default)
    python setup/setup.py --reset        # Drop and recreate everything
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def reset_snowflake():
    """Drop and recreate the Snowflake database."""
    print("\n" + "=" * 60)
    print("Resetting Snowflake database...")
    print("=" * 60 + "\n")

    try:
        import snowflake.connector
    except ImportError:
        print("Error: snowflake-connector-python not installed.")
        print("Run: pip install snowflake-connector-python")
        return False

    required_vars = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False

    print("Connecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )
        print("Connected successfully!")
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        return False

    cursor = conn.cursor()

    print("\nDropping DATA_ENGINEERING_DB if exists...")
    try:
        cursor.execute("DROP DATABASE IF EXISTS DATA_ENGINEERING_DB")
        print("  Database dropped.")
    except Exception as e:
        print(f"  Warning: {e}")

    print("Dropping DATA_ENGINEERING_WH if exists...")
    try:
        cursor.execute("DROP WAREHOUSE IF EXISTS DATA_ENGINEERING_WH")
        print("  Warehouse dropped.")
    except Exception as e:
        print(f"  Warning: {e}")

    print("Dropping DATA_ENGINEERING_ROLE if exists...")
    try:
        cursor.execute("DROP ROLE IF EXISTS DATA_ENGINEERING_ROLE")
        print("  Role dropped.")
    except Exception as e:
        print(f"  Warning (role may be in use): {e}")

    cursor.close()
    conn.close()

    print("\nReset complete. Run setup again to recreate.")
    return True


def setup_snowflake():
    """Execute the Snowflake setup using direct SQL commands."""
    print("\n" + "=" * 60)
    print("Setting up Snowflake database and sample data...")
    print("=" * 60 + "\n")

    try:
        import snowflake.connector
    except ImportError:
        print("Error: snowflake-connector-python not installed.")
        print("Run: pip install snowflake-connector-python")
        return False

    required_vars = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these in your .env file or environment:")
        for var in missing_vars:
            print(f"  {var}=<your-value>")
        return False

    print("Connecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )
        print("Connected successfully!")
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        return False

    cursor = conn.cursor()
    errors = []

    def run_sql(sql, description):
        """Execute SQL and handle errors."""
        try:
            cursor.execute(sql)
            print(f"  OK: {description}")
            return True
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"  ERROR: {description}")
            print(f"         {error_msg}")
            errors.append((description, error_msg))
            return False

    # Step 1: Create warehouse
    print("\n1. Creating warehouse...")
    run_sql("""
        CREATE WAREHOUSE IF NOT EXISTS DATA_ENGINEERING_WH
        WAREHOUSE_SIZE = 'X-SMALL'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE
    """, "Create warehouse")

    # Step 2: Use warehouse
    print("\n2. Activating warehouse...")
    if not run_sql("USE WAREHOUSE DATA_ENGINEERING_WH", "Use warehouse"):
        print("ERROR: Cannot proceed without warehouse. Aborting.")
        cursor.close()
        conn.close()
        return False

    # Step 3: Create database
    print("\n3. Creating database...")
    run_sql("CREATE DATABASE IF NOT EXISTS DATA_ENGINEERING_DB", "Create database")
    run_sql("USE DATABASE DATA_ENGINEERING_DB", "Use database")

    # Step 4: Create schemas
    print("\n4. Creating schemas...")
    run_sql("CREATE SCHEMA IF NOT EXISTS RAW COMMENT = 'Raw data from source systems'", "Create RAW schema")
    run_sql("CREATE SCHEMA IF NOT EXISTS STAGING COMMENT = 'Cleaned and standardized data'", "Create STAGING schema")
    run_sql("CREATE SCHEMA IF NOT EXISTS INTERMEDIATE COMMENT = 'Business logic and transformations'", "Create INTERMEDIATE schema")
    run_sql("CREATE SCHEMA IF NOT EXISTS MARTS COMMENT = 'Final analytics-ready tables'", "Create MARTS schema")

    # Step 5: Create tables in RAW schema
    print("\n5. Creating raw tables...")
    run_sql("USE SCHEMA RAW", "Use RAW schema")

    run_sql("""
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
        )
    """, "Create raw_customers table")

    run_sql("""
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
        )
    """, "Create raw_orders table")

    run_sql("""
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
        )
    """, "Create raw_order_items table")

    run_sql("""
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
        )
    """, "Create raw_products table")

    run_sql("""
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
        )
    """, "Create raw_inventory table")

    run_sql("""
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
        )
    """, "Create raw_web_events table")

    # Step 6: Insert sample data
    print("\n6. Inserting sample data...")

    run_sql("""
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
        ('C013', '', 'Unknown', 'invalid-email', '12345', '', '', 'XX', '00000', '', '2024-01-01', NULL, 'maybe', '')
    """, "Insert customers data")

    run_sql("""
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
        ('SKU-012', 'Mystery Product', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'true', NULL)
    """, "Insert products data")

    run_sql("""
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
        ('ORD-013', 'C999', '2024-03-26', 'unknown', '', '', 'invalid', 'invalid', 'invalid', 'invalid', 'invalid', 'XXX', '', NULL)
    """, "Insert orders data")

    run_sql("""
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
        ('OI-020', 'ORD-012', 'SKU-006', 'Office Chair', '1', '299.99', '0', '299.99')
    """, "Insert order_items data")

    run_sql("""
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
        ('INV-013', 'SKU-005', 'WH-002', 'West Coast Warehouse', '5', '4', '1', '10', '2024-03-01')
    """, "Insert inventory data")

    run_sql("""
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
        ('EVT-010', 'SESS-005', 'C007', 'add_to_cart', '2024-03-21 14:00:00', '/products/standing-desk', '/products', 'desktop', 'Chrome 122', '192.168.1.5', 'US', 'Furniture', 'SKU-007')
    """, "Insert web_events data")

    # Step 7: Create role and grants
    print("\n7. Setting up permissions...")
    run_sql("CREATE ROLE IF NOT EXISTS DATA_ENGINEERING_ROLE", "Create role")
    run_sql("GRANT USAGE ON WAREHOUSE DATA_ENGINEERING_WH TO ROLE DATA_ENGINEERING_ROLE", "Grant warehouse usage")
    run_sql("GRANT USAGE ON DATABASE DATA_ENGINEERING_DB TO ROLE DATA_ENGINEERING_ROLE", "Grant database usage")
    run_sql("GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.RAW TO ROLE DATA_ENGINEERING_ROLE", "Grant RAW schema usage")
    run_sql("GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE", "Grant STAGING schema usage")
    run_sql("GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE", "Grant INTERMEDIATE schema usage")
    run_sql("GRANT USAGE ON SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE", "Grant MARTS schema usage")
    run_sql("GRANT SELECT ON ALL TABLES IN SCHEMA DATA_ENGINEERING_DB.RAW TO ROLE DATA_ENGINEERING_ROLE", "Grant SELECT on RAW tables")
    run_sql("GRANT SELECT ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.RAW TO ROLE DATA_ENGINEERING_ROLE", "Grant SELECT on future RAW tables")
    run_sql("GRANT ALL ON SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE", "Grant ALL on STAGING")
    run_sql("GRANT ALL ON SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE", "Grant ALL on INTERMEDIATE")
    run_sql("GRANT ALL ON SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE", "Grant ALL on MARTS")
    run_sql("GRANT ALL ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.STAGING TO ROLE DATA_ENGINEERING_ROLE", "Grant ALL on future STAGING tables")
    run_sql("GRANT ALL ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.INTERMEDIATE TO ROLE DATA_ENGINEERING_ROLE", "Grant ALL on future INTERMEDIATE tables")
    run_sql("GRANT ALL ON FUTURE TABLES IN SCHEMA DATA_ENGINEERING_DB.MARTS TO ROLE DATA_ENGINEERING_ROLE", "Grant ALL on future MARTS tables")

    # Step 8: Verify
    print("\n8. Verifying setup...")
    cursor.execute("""
        SELECT 'raw_customers' as tbl, COUNT(*) as cnt FROM DATA_ENGINEERING_DB.RAW.raw_customers
        UNION ALL SELECT 'raw_products', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_products
        UNION ALL SELECT 'raw_orders', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_orders
        UNION ALL SELECT 'raw_order_items', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_order_items
        UNION ALL SELECT 'raw_inventory', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_inventory
        UNION ALL SELECT 'raw_web_events', COUNT(*) FROM DATA_ENGINEERING_DB.RAW.raw_web_events
    """)
    print("\n  Table Row Counts:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]} rows")

    cursor.close()
    conn.close()

    if errors:
        print(f"\n  Completed with {len(errors)} error(s)")
        return False
    else:
        print("\n  All steps completed successfully!")
        return True


def reset_dbt_project():
    """Remove the existing dbt project."""
    project_dir = Path(__file__).parent.parent / "dbt_project"
    if project_dir.exists():
        print(f"Removing existing dbt project: {project_dir}")
        shutil.rmtree(project_dir)
        print("  Removed.")
    return True


def setup_dbt_project():
    """Create a sample dbt project structure."""
    print("\n" + "=" * 60)
    print("Setting up sample dbt project...")
    print("=" * 60 + "\n")

    project_dir = Path(__file__).parent.parent / "dbt_project"

    # Create directory structure
    dirs = [
        "models/staging",
        "models/intermediate",
        "models/marts/core",
        "models/marts/marketing",
        "macros",
        "tests",
        "seeds",
        "snapshots",
        "analyses",
    ]

    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
        print(f"  Created: dbt_project/{d}/")

    # Create dbt_project.yml
    dbt_project_yml = """# dbt Project Configuration
name: 'ecommerce_analytics'
version: '1.0.0'
config-version: 2

profile: 'snowflake'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  ecommerce_analytics:
    staging:
      +materialized: view
      +schema: STAGING
    intermediate:
      +materialized: ephemeral
      +schema: INTERMEDIATE
    marts:
      +materialized: table
      +schema: MARTS
"""
    (project_dir / "dbt_project.yml").write_text(dbt_project_yml)
    print("  Created: dbt_project/dbt_project.yml")

    # Create profiles.yml (dbt finds this automatically when running from project dir)
    profiles_yml = """# dbt profile configuration - uses environment variables
# dbt finds this file automatically when running from the dbt_project directory
snowflake:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE', 'DATA_ENGINEERING_ROLE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE', 'DATA_ENGINEERING_WH') }}"
      database: DATA_ENGINEERING_DB
      schema: RAW
      threads: 4
"""
    (project_dir / "profiles.yml").write_text(profiles_yml)
    print("  Created: dbt_project/profiles.yml")

    # Define all model files
    model_files = {
        "models/staging/_sources.yml": """version: 2

sources:
  - name: raw
    database: DATA_ENGINEERING_DB
    schema: RAW
    tables:
      - name: raw_customers
      - name: raw_orders
      - name: raw_order_items
      - name: raw_products
      - name: raw_inventory
      - name: raw_web_events
""",
        "models/staging/_staging.yml": """version: 2

models:
  - name: stg_customers
    columns:
      - name: customer_id
        tests: [unique, not_null]
  - name: stg_orders
    columns:
      - name: order_id
        tests: [unique, not_null]
  - name: stg_products
    columns:
      - name: product_id
        tests: [unique, not_null]
""",
        "models/staging/stg_customers.sql": """with source as (
    select * from {{ source('raw', 'raw_customers') }}
),

cleaned as (
    select
        _id as customer_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(trim(email_address)) as email,
        nullif(trim(phone), '') as phone,
        trim(city) as city,
        upper(trim(state_code)) as state,
        try_to_timestamp(created_timestamp) as created_at,
        try_to_timestamp(updated_timestamp) as updated_at,
        case lower(is_active) when 'true' then true when 'false' then false end as is_active,
        trim(customer_segment) as customer_segment
    from source
    where _id is not null and trim(first_name) != '' and email_address like '%@%'
)

select * from (
    select *, row_number() over (partition by customer_id order by updated_at desc nulls last) as rn
    from cleaned
) where rn = 1
""",
        "models/staging/stg_orders.sql": """with source as (
    select * from {{ source('raw', 'raw_orders') }}
)

select
    order_id,
    customer_id,
    try_to_timestamp(order_date) as order_date,
    lower(trim(order_status)) as order_status,
    lower(trim(shipping_method)) as shipping_method,
    try_to_decimal(subtotal, 10, 2) as subtotal,
    try_to_decimal(tax_amount, 10, 2) as tax_amount,
    try_to_decimal(shipping_cost, 10, 2) as shipping_cost,
    try_to_decimal(discount_amount, 10, 2) as discount_amount,
    try_to_decimal(total_amount, 10, 2) as total_amount,
    upper(trim(currency_code)) as currency_code,
    lower(trim(payment_method)) as payment_method
from source
where order_id is not null and try_to_decimal(total_amount, 10, 2) is not null
""",
        "models/staging/stg_products.sql": """with source as (
    select * from {{ source('raw', 'raw_products') }}
)

select
    sku as product_id,
    trim(product_name) as product_name,
    trim(category_name) as category_name,
    trim(subcategory) as subcategory,
    trim(brand) as brand,
    try_to_decimal(unit_cost, 10, 2) as unit_cost,
    try_to_decimal(list_price, 10, 2) as list_price,
    case lower(is_active) when 'true' then true when 'false' then false end as is_active
from source
where sku is not null and trim(product_name) is not null
""",
        "models/staging/stg_order_items.sql": """with source as (
    select * from {{ source('raw', 'raw_order_items') }}
)

select
    order_item_id,
    order_id,
    product_id,
    try_to_number(quantity)::integer as quantity,
    try_to_decimal(unit_price, 10, 2) as unit_price,
    try_to_decimal(line_total, 10, 2) as line_total
from source
where order_item_id is not null
""",
        "models/staging/stg_inventory.sql": """with source as (
    select * from {{ source('raw', 'raw_inventory') }}
)

select
    inventory_id,
    product_sku as product_id,
    warehouse_id,
    trim(warehouse_name) as warehouse_name,
    try_to_number(quantity_on_hand)::integer as quantity_on_hand,
    try_to_number(quantity_available)::integer as quantity_available,
    try_to_number(reorder_point)::integer as reorder_point
from source
where inventory_id is not null
""",
        "models/intermediate/int_customer_orders.sql": """with customers as (
    select * from {{ ref('stg_customers') }}
),
orders as (
    select * from {{ ref('stg_orders') }}
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.customer_segment,
    count(o.order_id) as total_orders,
    sum(o.total_amount) as lifetime_value,
    avg(o.total_amount) as avg_order_value,
    min(o.order_date) as first_order_date,
    max(o.order_date) as last_order_date
from customers c
left join orders o on c.customer_id = o.customer_id
group by 1, 2, 3, 4, 5
""",
        "models/intermediate/int_product_performance.sql": """with order_items as (
    select * from {{ ref('stg_order_items') }}
),
products as (
    select * from {{ ref('stg_products') }}
),
inventory as (
    select * from {{ ref('stg_inventory') }}
)

select
    p.product_id,
    p.product_name,
    p.category_name,
    p.unit_cost,
    p.list_price,
    coalesce(sum(oi.quantity), 0) as units_sold,
    coalesce(sum(oi.line_total), 0) as total_revenue,
    coalesce(sum(i.quantity_available), 0) as inventory_available
from products p
left join order_items oi on p.product_id = oi.product_id
left join inventory i on p.product_id = i.product_id
group by 1, 2, 3, 4, 5
""",
        "models/marts/core/dim_customers.sql": """{{ config(materialized='table') }}

with customer_orders as (
    select * from {{ ref('int_customer_orders') }}
)

select
    customer_id,
    first_name || ' ' || last_name as full_name,
    email,
    customer_segment,
    total_orders,
    lifetime_value,
    avg_order_value,
    case
        when lifetime_value >= 2000 then 'High Value'
        when lifetime_value >= 500 then 'Medium Value'
        when lifetime_value > 0 then 'Low Value'
        else 'No Orders'
    end as customer_value_tier,
    current_timestamp() as updated_at
from customer_orders
""",
        "models/marts/core/dim_products.sql": """{{ config(materialized='table') }}

with product_perf as (
    select * from {{ ref('int_product_performance') }}
)

select
    product_id,
    product_name,
    category_name,
    unit_cost,
    list_price,
    list_price - unit_cost as unit_margin,
    units_sold,
    total_revenue,
    inventory_available,
    case
        when inventory_available = 0 then 'out_of_stock'
        when inventory_available < 10 then 'low_stock'
        else 'in_stock'
    end as stock_status,
    current_timestamp() as updated_at
from product_perf
""",
        "models/marts/core/fct_orders.sql": """{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_orders') }}
),
order_items as (
    select order_id, count(*) as item_count, sum(quantity) as total_units
    from {{ ref('stg_order_items') }}
    group by 1
)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.order_status,
    o.subtotal,
    o.tax_amount,
    o.shipping_cost,
    o.discount_amount,
    o.total_amount,
    coalesce(oi.item_count, 0) as item_count,
    coalesce(oi.total_units, 0) as total_units,
    current_timestamp() as updated_at
from orders o
left join order_items oi on o.order_id = oi.order_id
""",
        "models/marts/marketing/customer_rfm.sql": """{{ config(materialized='table') }}

with metrics as (
    select * from {{ ref('int_customer_orders') }}
    where total_orders > 0
)

select
    customer_id,
    first_name,
    last_name,
    email,
    total_orders,
    lifetime_value,
    datediff('day', last_order_date, current_date()) as days_since_last_order,
    ntile(5) over (order by datediff('day', last_order_date, current_date()) desc) as recency_score,
    ntile(5) over (order by total_orders) as frequency_score,
    ntile(5) over (order by lifetime_value) as monetary_score,
    current_timestamp() as updated_at
from metrics
""",
        "macros/safe_divide.sql": """{% macro safe_divide(numerator, denominator, default=0) %}
case when {{ denominator }} = 0 then {{ default }} else {{ numerator }} / {{ denominator }} end
{% endmacro %}
""",
        "macros/generate_schema_name.sql": """{% macro generate_schema_name(custom_schema_name, node) -%}
    {#
        Override dbt's default schema naming behavior.

        By default, dbt concatenates: target_schema + '_' + custom_schema
        For example: RAW_STAGING, RAW_MARTS

        This macro changes the behavior to use the custom schema name directly:
        - If custom_schema is set (e.g., 'staging'), use 'STAGING'
        - If no custom_schema, fall back to the target schema (e.g., 'RAW')

        This ensures models end up in the correct schemas:
        - Staging models -> STAGING schema
        - Mart models -> MARTS schema
        - Models without custom schema -> RAW schema (default)
    #}
    {%- if custom_schema_name is none -%}
        {{ target.schema | upper }}
    {%- else -%}
        {{ custom_schema_name | upper }}
    {%- endif -%}
{%- endmacro %}
""",
        "tests/assert_positive_revenue.sql": """select order_id, total_amount
from {{ ref('fct_orders') }}
where order_status = 'completed' and total_amount <= 0
""",
    }

    for file_path, content in model_files.items():
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        print(f"  Created: dbt_project/{file_path}")

    print(f"\ndbt project created at: {project_dir}")
    print("\nNext steps:")
    print("  1. Ensure environment variables are set (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, etc.)")
    print("  2. Run: cd dbt_project && dbt debug")
    print("  3. Run: dbt run")

    return True


def main():
    parser = argparse.ArgumentParser(description="Setup script for the Data Engineering Agent")
    parser.add_argument("--snowflake", action="store_true", help="Set up Snowflake only")
    parser.add_argument("--dbt", action="store_true", help="Set up dbt project only")
    parser.add_argument("--all", action="store_true", help="Set up both (default)")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate everything")

    args = parser.parse_args()

    if not any([args.snowflake, args.dbt, args.all, args.reset]):
        args.all = True

    print("=" * 60)
    print("Data Engineering Agent Setup")
    print("=" * 60)

    if args.reset:
        print("\nResetting all resources...")
        reset_snowflake()
        reset_dbt_project()
        print("\nReset complete. Re-run without --reset to set up fresh.")
        return

    success = True

    if args.snowflake or args.all:
        if not setup_snowflake():
            success = False

    if args.dbt or args.all:
        if not setup_dbt_project():
            success = False

    if success:
        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Setup completed with errors. Please review above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

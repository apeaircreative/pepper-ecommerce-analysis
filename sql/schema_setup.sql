-- Create unified schemas for multi-platform e-commerce data

-- 1. Create unified customers table
CREATE OR REPLACE TABLE `pepper-analytics-2024.processed_data.unified_customers` (
    customer_id STRING,
    platform STRING,  -- 'shopify' or 'amazon'
    first_order_date DATE,
    last_order_date DATE,
    total_orders INT64,
    total_spent FLOAT64,
    country STRING,
    created_at TIMESTAMP
);

-- 2. Create unified orders table
CREATE OR REPLACE TABLE `pepper-analytics-2024.processed_data.unified_orders` (
    order_id STRING,
    platform STRING,
    order_date TIMESTAMP,
    customer_id STRING,
    total_amount FLOAT64,
    status STRING,
    shipping_address STRUCT<
        country STRING,
        state STRING,
        city STRING,
        zip_code STRING
    >,
    created_at TIMESTAMP
);

-- 3. Create unified order items table
CREATE OR REPLACE TABLE `pepper-analytics-2024.processed_data.unified_order_items` (
    order_item_id STRING,
    order_id STRING,
    product_id STRING,
    quantity INT64,
    unit_price FLOAT64,
    total_price FLOAT64,
    created_at TIMESTAMP
);

-- 4. Create unified products table
CREATE OR REPLACE TABLE `pepper-analytics-2024.processed_data.unified_products` (
    product_id STRING,
    platform STRING,
    name STRING,
    category STRING,
    brand STRING,
    price FLOAT64,
    created_at TIMESTAMP
);
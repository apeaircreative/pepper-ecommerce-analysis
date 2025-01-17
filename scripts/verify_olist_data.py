"""
Verify Olist data quality and relationships before transformation.
This is a critical step to ensure our data integration will be reliable.
"""

from google.cloud import bigquery
from typing import Dict, List
import pandas as pd
import json
from datetime import datetime

def run_quality_check(client: bigquery.Client, query: str, description: str) -> None:
    """Run a quality check query and print results."""
    try:
        print(f"\n{description}")
        print("-" * len(description))
        query_job = client.query(query)
        df = query_job.to_dataframe()
        print(df.to_string(index=False))
    except Exception as e:
        print(f"Error in {description}: {str(e)}")

def verify_data_quality():
    """Run comprehensive data quality checks on Olist data."""
    client = bigquery.Client()
    project_id = "pepper-analytics-2024"
    
    # 1. Basic Count Checks
    basic_counts = f"""
    SELECT 
        'Customers' as table_name,
        COUNT(*) as total_rows,
        COUNT(DISTINCT customer_id) as unique_ids
    FROM `{project_id}.raw_data.olist_customers`
    UNION ALL
    SELECT 
        'Orders',
        COUNT(*),
        COUNT(DISTINCT order_id)
    FROM `{project_id}.raw_data.olist_orders`
    UNION ALL
    SELECT 
        'Order Items',
        COUNT(*),
        COUNT(DISTINCT order_id)
    FROM `{project_id}.raw_data.olist_order_items`
    UNION ALL
    SELECT 
        'Products',
        COUNT(*),
        COUNT(DISTINCT product_id)
    FROM `{project_id}.raw_data.olist_products`
    """
    
    # 2. Date Range Analysis
    date_analysis = f"""
    SELECT 
        MIN(order_purchase_timestamp) as earliest_order,
        MAX(order_purchase_timestamp) as latest_order,
        COUNT(DISTINCT DATE(order_purchase_timestamp)) as unique_days
    FROM `{project_id}.raw_data.olist_orders`
    """
    
    # 3. Relationship Integrity
    relationship_check = f"""
    WITH OrderCounts AS (
        SELECT 
            o.customer_id,
            COUNT(DISTINCT o.order_id) as order_count,
            COUNT(DISTINCT oi.product_id) as unique_products,
            SUM(oi.price) as total_spent
        FROM `{project_id}.raw_data.olist_orders` o
        LEFT JOIN `{project_id}.raw_data.olist_order_items` oi
            ON o.order_id = oi.order_id
        GROUP BY o.customer_id
    )
    SELECT 
        MIN(order_count) as min_orders_per_customer,
        MAX(order_count) as max_orders_per_customer,
        AVG(order_count) as avg_orders_per_customer,
        MIN(unique_products) as min_products_per_customer,
        MAX(unique_products) as max_products_per_customer,
        AVG(unique_products) as avg_products_per_customer,
        MIN(total_spent) as min_total_spent,
        MAX(total_spent) as max_total_spent,
        AVG(total_spent) as avg_total_spent
    FROM OrderCounts
    """
    
    # 4. Missing Values Analysis
    null_check = f"""
    SELECT 
        COUNT(*) as total_orders,
        COUNTIF(order_approved_at IS NULL) as missing_approval,
        COUNTIF(order_delivered_carrier_date IS NULL) as missing_carrier_date,
        COUNTIF(order_delivered_customer_date IS NULL) as missing_delivery_date,
        COUNTIF(order_estimated_delivery_date IS NULL) as missing_estimated_date
    FROM `{project_id}.raw_data.olist_orders`
    """
    
    # 5. Order Status Distribution
    status_check = f"""
    SELECT 
        order_status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
    FROM `{project_id}.raw_data.olist_orders`
    GROUP BY order_status
    ORDER BY count DESC
    """
    
    # Run all checks
    checks = [
        (basic_counts, "Basic Count Analysis"),
        (date_analysis, "Date Range Analysis"),
        (relationship_check, "Customer-Order Relationship Analysis"),
        (null_check, "Missing Values Analysis"),
        (status_check, "Order Status Distribution")
    ]
    
    print("=== Olist Data Quality Report ===")
    print(f"Generated at: {datetime.now()}")
    print("\nRunning comprehensive quality checks...")
    
    for query, description in checks:
        run_quality_check(client, query, description)
    
    print("\n=== Quality Check Complete ===")

if __name__ == "__main__":
    verify_data_quality()

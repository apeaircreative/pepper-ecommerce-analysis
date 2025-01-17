"""
Investigate duplicate records in Olist dataset.
This script analyzes the nature of duplications in customer and order tables.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

def run_investigation():
    """Run a series of investigative queries to understand data structure."""
    client = bigquery.Client()
    project_id = "pepper-analytics-2024"
    
    # 1. Customer ID Investigation
    customer_dupes = f"""
    WITH CustomerCounts AS (
        SELECT 
            customer_unique_id,
            COUNT(DISTINCT customer_id) as unique_customer_ids,
            COUNT(*) as total_rows
        FROM `{project_id}.raw_data.olist_customers`
        GROUP BY customer_unique_id
        HAVING COUNT(*) > 1
    )
    SELECT 
        MIN(unique_customer_ids) as min_ids,
        MAX(unique_customer_ids) as max_ids,
        AVG(unique_customer_ids) as avg_ids,
        MIN(total_rows) as min_rows,
        MAX(total_rows) as max_rows,
        AVG(total_rows) as avg_rows,
        COUNT(*) as customers_with_dupes
    FROM CustomerCounts
    """
    
    # 2. Sample of Duplicated Records
    sample_dupes = f"""
    WITH RankedCustomers AS (
        SELECT 
            customer_unique_id,
            customer_id,
            customer_city,
            customer_state,
            ROW_NUMBER() OVER(PARTITION BY customer_unique_id ORDER BY customer_id) as record_num
        FROM `{project_id}.raw_data.olist_customers`
    )
    SELECT *
    FROM RankedCustomers
    WHERE customer_unique_id IN (
        SELECT customer_unique_id 
        FROM `{project_id}.raw_data.olist_customers`
        GROUP BY customer_unique_id
        HAVING COUNT(*) > 1
    )
    AND record_num <= 2
    LIMIT 10
    """
    
    # 3. Order Pattern Analysis
    order_pattern = f"""
    WITH CustomerOrders AS (
        SELECT 
            c.customer_unique_id,
            c.customer_id,
            o.order_id,
            o.order_purchase_timestamp,
            ROW_NUMBER() OVER(PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) as order_sequence
        FROM `{project_id}.raw_data.olist_customers` c
        JOIN `{project_id}.raw_data.olist_orders` o
        ON c.customer_id = o.customer_id
    )
    SELECT 
        customer_unique_id,
        customer_id,
        order_id,
        order_purchase_timestamp,
        order_sequence
    FROM CustomerOrders
    WHERE customer_unique_id IN (
        SELECT customer_unique_id
        FROM CustomerOrders
        GROUP BY customer_unique_id
        HAVING COUNT(*) > 1
    )
    ORDER BY customer_unique_id, order_sequence
    LIMIT 15
    """
    
    # 4. City/State Consistency Check
    location_check = f"""
    WITH CustomerLocations AS (
        SELECT 
            customer_unique_id,
            COUNT(DISTINCT CONCAT(customer_city, '|', customer_state)) as location_combinations
        FROM `{project_id}.raw_data.olist_customers`
        GROUP BY customer_unique_id
        HAVING COUNT(DISTINCT CONCAT(customer_city, '|', customer_state)) > 1
    )
    SELECT 
        COUNT(*) as customers_with_multiple_locations,
        AVG(location_combinations) as avg_locations_per_customer,
        MAX(location_combinations) as max_locations_per_customer
    FROM CustomerLocations
    """

    queries = [
        ("Customer Duplication Analysis", customer_dupes),
        ("Sample of Duplicated Records", sample_dupes),
        ("Order Pattern Analysis", order_pattern),
        ("Location Consistency Check", location_check)
    ]

    print("=== Olist Data Duplication Investigation ===")
    print(f"Generated at: {datetime.now()}\n")

    for title, query in queries:
        try:
            print(f"\n{title}")
            print("-" * len(title))
            query_job = client.query(query)
            df = query_job.to_dataframe()
            if not df.empty:
                print(df.to_string(index=False))
            else:
                print("No results found")
            print()
        except Exception as e:
            print(f"Error running query: {str(e)}\n")

    print("=== Investigation Complete ===")

if __name__ == "__main__":
    run_investigation()

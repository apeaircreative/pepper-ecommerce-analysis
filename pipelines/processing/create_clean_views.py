"""
Create and verify cleaned views for Olist data.
Handles deduplication and data quality checks.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

def create_dataset_if_not_exists(client: bigquery.Client, project_id: str, dataset_id: str):
    """Create dataset if it doesn't exist."""
    dataset_ref = f"{project_id}.{dataset_id}"
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_ref} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset = client.create_dataset(dataset)
        print(f"Created dataset {dataset_ref}")

def create_views():
    """Create cleaned views in BigQuery."""
    client = bigquery.Client()
    project_id = "pepper-analytics-2024"
    
    print("=== Creating Clean Views ===")
    print(f"Started at: {datetime.now()}\n")

    try:
        print("1. Ensuring dataset exists...")
        create_dataset_if_not_exists(client, project_id, "transformed_data")
        print()

        # Create customer view
        print("2. Creating customer view...")
        customer_view = f"""
        CREATE OR REPLACE VIEW `{project_id}.transformed_data.vw_customers_clean` AS
        SELECT DISTINCT
            customer_unique_id,
            FIRST_VALUE(customer_id) OVER(
                PARTITION BY customer_unique_id 
                ORDER BY customer_id
            ) as customer_id,
            customer_city,
            customer_state
        FROM `{project_id}.raw_data.olist_customers`
        """
        client.query(customer_view).result()
        print("✓ Customer view created\n")

        # Create order view
        print("3. Creating order view...")
        order_view = f"""
        CREATE OR REPLACE VIEW `{project_id}.transformed_data.vw_orders_clean` AS
        SELECT DISTINCT
            o.order_id,
            c.customer_unique_id,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_approved_at,
            o.order_delivered_carrier_date,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date
        FROM `{project_id}.raw_data.olist_orders` o
        JOIN `{project_id}.transformed_data.vw_customers_clean` c
            ON o.customer_id = c.customer_id
        """
        client.query(order_view).result()
        print("✓ Order view created\n")

        # Verify customer view
        print("4. Verifying customer view...")
        verify_customers = f"""
        SELECT 
            COUNT(*) as total_customers,
            COUNT(DISTINCT customer_unique_id) as unique_customers,
            COUNT(DISTINCT customer_id) as unique_customer_ids,
            COUNT(DISTINCT CONCAT(customer_city, customer_state)) as unique_locations
        FROM `{project_id}.transformed_data.vw_customers_clean`
        """
        customer_stats = client.query(verify_customers).to_dataframe()
        print(customer_stats.to_string(index=False))
        print()

        # Verify order view
        print("5. Verifying order view...")
        verify_orders = f"""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(DISTINCT order_id) as unique_orders,
            COUNT(DISTINCT customer_unique_id) as unique_customers,
            MIN(order_purchase_timestamp) as earliest_order,
            MAX(order_purchase_timestamp) as latest_order
        FROM `{project_id}.transformed_data.vw_orders_clean`
        """
        order_stats = client.query(verify_orders).to_dataframe()
        print(order_stats.to_string(index=False))
        print()

        print("=== View Creation Complete ===")
        print("Next steps:")
        print("1. Create unified view with TheLook")
        print("2. Add data quality monitoring")
        print("3. Document view relationships")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nDebug information:")
        print(f"Project ID: {project_id}")
        print("Make sure you have:")
        print("1. Valid BigQuery credentials")
        print("2. Permissions to create datasets")
        print("3. Raw data tables exist in raw_data dataset")

if __name__ == "__main__":
    create_views()

"""
Import TheLook sample dataset into our BigQuery project.
Using the public TheLook Ecommerce dataset.
"""

from google.cloud import bigquery
from datetime import datetime

def import_thelook_data():
    """Import TheLook tables from the public dataset."""
    client = bigquery.Client()
    project_id = "pepper-analytics-2024"

    # Create thelook_ecommerce dataset if it doesn't exist
    dataset_id = f"{project_id}.thelook_ecommerce"
    try:
        client.get_dataset(dataset_id)
        print(f"Dataset {dataset_id} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        dataset = client.create_dataset(dataset)
        print(f"Created dataset {dataset_id}")

    # List of tables to copy from the public dataset
    tables_to_copy = [
        'users',
        'orders',
        'order_items',
        'products',
        'distribution_centers',
        'inventory_items'
    ]

    print("\nCopying tables from public TheLook dataset...")
    
    for table in tables_to_copy:
        copy_table = f"""
        CREATE OR REPLACE TABLE `{project_id}.thelook_ecommerce.{table}` AS
        SELECT *
        FROM `bigquery-public-data.thelook_ecommerce.{table}`
        """
        
        try:
            print(f"\nCopying {table}...")
            query_job = client.query(copy_table)
            query_job.result()  # Wait for the job to complete
            print(f"✓ Successfully copied {table}")
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM `{project_id}.thelook_ecommerce.{table}`"
            count_job = client.query(count_query)
            count = list(count_job)[0].count
            print(f"  Rows copied: {count:,}")
            
        except Exception as e:
            print(f"Error copying {table}: {str(e)}")

    print("\nVerifying data ranges...")
    
    # Verify date ranges
    date_check = f"""
    SELECT 
        'Users' as table_name,
        MIN(created_at) as earliest_date,
        MAX(created_at) as latest_date,
        COUNT(*) as total_records
    FROM `{project_id}.thelook_ecommerce.users`
    
    UNION ALL
    
    SELECT 
        'Orders',
        MIN(created_at),
        MAX(created_at),
        COUNT(*)
    FROM `{project_id}.thelook_ecommerce.orders`
    """
    
    try:
        date_stats = client.query(date_check).to_dataframe()
        print("\nDate ranges for key tables:")
        print(date_stats.to_string(index=False))
    except Exception as e:
        print(f"Error checking dates: {str(e)}")

if __name__ == "__main__":
    print("=== Importing TheLook Dataset ===")
    print(f"Started at: {datetime.now()}\n")
    import_thelook_data()
    print("\n=== Import Complete ===")

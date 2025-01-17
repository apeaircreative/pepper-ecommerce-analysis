"""
Download and prepare Olist e-commerce data for analysis.
Focuses on core tables needed for customer and order analysis.
"""

import os
import kaggle
from google.cloud import bigquery
from typing import List, Dict
import pandas as pd

# Core tables we need for analysis
CORE_TABLES = {
    'customers': 'olist_customers_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'products': 'olist_products_dataset.csv'
}

def download_core_datasets(data_dir: str) -> None:
    """
    Download only the essential Olist datasets needed for analysis.
    
    Args:
        data_dir: Directory to store downloaded files
    """
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        print("Authenticating with Kaggle...")
        kaggle.api.authenticate()
        
        print("Downloading Olist dataset...")
        kaggle.api.dataset_download_files(
            'olistbr/brazilian-ecommerce',
            path=data_dir,
            unzip=True
        )
        
        # Keep only core files, remove others to save space
        for file in os.listdir(data_dir):
            if file.endswith('.csv') and file not in CORE_TABLES.values():
                os.remove(os.path.join(data_dir, file))
                print(f"Removed non-core file: {file}")
        
        print("\nCore files available:")
        for table, file in CORE_TABLES.items():
            if os.path.exists(os.path.join(data_dir, file)):
                print(f"✓ {table}: {file}")
            else:
                print(f"✗ {table}: {file} (MISSING)")
                
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        raise

def verify_data_quality(data_dir: str) -> Dict[str, Dict]:
    """
    Perform initial data quality checks on downloaded files.
    
    Args:
        data_dir: Directory containing the CSV files
    
    Returns:
        Dict containing data quality metrics for each table
    """
    quality_metrics = {}
    
    for table, file in CORE_TABLES.items():
        file_path = os.path.join(data_dir, file)
        if not os.path.exists(file_path):
            continue
            
        df = pd.read_csv(file_path)
        metrics = {
            'rows': len(df),
            'columns': len(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_columns': list(df.columns)
        }
        quality_metrics[table] = metrics
    
    return quality_metrics

def load_to_bigquery(data_dir: str, project_id: str) -> None:
    """
    Load verified CSV files to BigQuery raw_data dataset.
    
    Args:
        data_dir: Directory containing the CSV files
        project_id: Google Cloud project ID
    """
    client = bigquery.Client()
    dataset_id = f"{project_id}.raw_data"
    
    try:
        # Create dataset if it doesn't exist
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset, exists_ok=True)
        print(f"\nCreated/verified dataset: {dataset_id}")
        
        # Load each core table
        for table, file in CORE_TABLES.items():
            file_path = os.path.join(data_dir, file)
            if not os.path.exists(file_path):
                print(f"Skipping {table}: file not found")
                continue
                
            table_id = f"{dataset_id}.olist_{table}"
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                autodetect=True,
            )
            
            with open(file_path, "rb") as source_file:
                job = client.load_table_from_file(
                    source_file,
                    table_id,
                    job_config=job_config
                )
            
            job.result()  # Wait for job completion
            print(f"Loaded {table} to {table_id}")
            
    except Exception as e:
        print(f"Error loading to BigQuery: {e}")
        raise

def verify_bigquery_data(project_id: str) -> None:
    """
    Verify the loaded data in BigQuery with basic statistics.
    
    Args:
        project_id: Google Cloud project ID
    """
    client = bigquery.Client()
    
    for table in CORE_TABLES.keys():
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT order_id) as unique_orders,
            MIN(order_purchase_timestamp) as earliest_date,
            MAX(order_purchase_timestamp) as latest_date
        FROM `{project_id}.raw_data.olist_{table}`
        """
        
        try:
            results = client.query(query).result()
            for row in results:
                print(f"\nTable: olist_{table}")
                print(f"Total rows: {row.row_count:,}")
                print(f"Unique orders: {row.unique_orders:,}")
                print(f"Date range: {row.earliest_date} to {row.latest_date}")
        except Exception:
            print(f"Could not verify table: olist_{table}")

def main():
    """Main execution function"""
    project_id = "pepper-analytics-2024"
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'olist')
    
    print("=== Starting Olist Data Pipeline ===")
    
    # Step 1: Download core datasets
    print("\n1. Downloading core datasets...")
    download_core_datasets(data_dir)
    
    # Step 2: Verify data quality
    print("\n2. Verifying data quality...")
    quality_metrics = verify_data_quality(data_dir)
    for table, metrics in quality_metrics.items():
        print(f"\n{table.upper()}:")
        print(f"Rows: {metrics['rows']:,}")
        print(f"Columns: {metrics['columns']}")
        print("Sample columns:", ", ".join(metrics['sample_columns'][:5]))
    
    # Step 3: Load to BigQuery
    print("\n3. Loading to BigQuery...")
    load_to_bigquery(data_dir, project_id)
    
    # Step 4: Verify BigQuery data
    print("\n4. Verifying BigQuery data...")
    verify_bigquery_data(project_id)
    
    print("\n=== Pipeline Complete ===")

if __name__ == "__main__":
    main()

"""
Set up initial datasets and load into BigQuery.
"""
from google.cloud import bigquery
import pandas as pd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_olist_dataset(data_dir: str, project_id: str, dataset_id: str):
    """Load Olist dataset into BigQuery."""
    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"
    
    try:
        # Create dataset if it doesn't exist
        try:
            client.get_dataset(dataset_ref)
            logger.info(f"Dataset {dataset_ref} already exists")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset, exists_ok=True)
            logger.info(f"Created dataset {dataset_ref}")
        
        # Load each CSV file
        data_path = Path(data_dir)
        for csv_file in data_path.glob("olist_*.csv"):
            table_name = csv_file.stem
            table_ref = f"{dataset_ref}.{table_name}"
            
            # Read CSV with proper encoding
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # Load to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
            )
            
            job = client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            job.result()  # Wait for job to complete
            
            logger.info(f"Loaded {len(df)} rows into {table_ref}")
            
    except Exception as e:
        logger.error(f"Error setting up dataset: {str(e)}")
        raise

def main():
    """Main function to set up all datasets."""
    project_id = "pepper-data-analytics"  # Update with your project
    dataset_id = "olist_data"
    data_dir = "data/olist"
    
    logger.info("Starting dataset setup...")
    setup_olist_dataset(data_dir, project_id, dataset_id)
    logger.info("Dataset setup complete")

if __name__ == "__main__":
    main()

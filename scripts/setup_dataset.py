from google.cloud import bigquery

def create_dataset():
    client = bigquery.Client()
    
    # Construct dataset reference
    dataset_id = f"{client.project}.processed_data"
    
    # Create dataset
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    dataset.description = "Processed e-commerce data for analysis"
    
    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"Dataset {dataset_id} created or already exists.")
    except Exception as e:
        print(f"Error creating dataset: {e}")

if __name__ == "__main__":
    create_dataset()
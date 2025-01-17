from google.cloud import bigquery

def test_bigquery_datasets():
    # Create a client
    client = bigquery.Client()
    
    # List datasets
    print("Available datasets:")
    for dataset in client.list_datasets():
        print(f"- {dataset.dataset_id}")
    
    # Test query on TheLook dataset
    query = """
    SELECT 
        COUNT(*) as order_count,
        DATE(created_at) as order_date
    FROM `bigquery-public-data.thelook_ecommerce.orders`
    WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY order_date
    ORDER BY order_date DESC
    LIMIT 5
    """
    
    print("\nRunning test query on TheLook dataset...")
    query_job = client.query(query)
    results = query_job.result()
    
    print("\nRecent orders by date:")
    for row in results:
        print(f"Date: {row.order_date}, Orders: {row.order_count}")

if __name__ == "__main__":
    test_bigquery_datasets()
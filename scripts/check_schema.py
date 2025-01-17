from google.cloud import bigquery
from typing import Dict, Any
import json

def check_table_schema(client: bigquery.Client, table_path: str) -> None:
    """Check schema and sample data for a given table."""
    print(f"\n=== {table_path.split('.')[-1].upper()} TABLE ===")
    
    # Check schema
    print("\nSchema:")
    schema_query = f"""
    SELECT * FROM {table_path} LIMIT 1
    """
    
    try:
        query_job = client.query(schema_query)
        results = query_job.result()
        for field in results.schema:
            print(f"{field.name}: {field.field_type}")
        
        # Get row count
        count_query = f"""
        SELECT COUNT(*) as count FROM {table_path}
        """
        count_job = client.query(count_query)
        count_result = count_job.result()
        row_count = list(count_result)[0].count
        print(f"\nTotal rows: {row_count:,}")
        
        # Sample data distribution
        print("\nSample value distribution:")
        for field in results.schema:
            if field.field_type in ['STRING', 'INT64', 'FLOAT64']:
                dist_query = f"""
                SELECT 
                    {field.name},
                    COUNT(*) as count
                FROM {table_path}
                GROUP BY {field.name}
                ORDER BY count DESC
                LIMIT 3
                """
                try:
                    dist_job = client.query(dist_query)
                    dist_result = dist_job.result()
                    print(f"\n{field.name}:")
                    for row in dist_result:
                        print(f"  {row[0]}: {row[1]:,} occurrences")
                except Exception:
                    continue
                    
    except Exception as e:
        print(f"Error: {e}")

def analyze_relationships():
    client = bigquery.Client()
    
    # Tables to analyze
    tables = {
        'users': '`bigquery-public-data.thelook_ecommerce.users`',
        'orders': '`bigquery-public-data.thelook_ecommerce.orders`',
        'order_items': '`bigquery-public-data.thelook_ecommerce.order_items`'
    }
    
    # Check each table
    for table_name, table_path in tables.items():
        check_table_schema(client, table_path)
        
    # Check relationships
    print("\n=== TABLE RELATIONSHIPS ===")
    relationship_query = """
    SELECT 
        'Orders-Users' as relationship,
        COUNT(DISTINCT o.order_id) as total_orders,
        COUNT(DISTINCT o.user_id) as total_users,
        COUNT(DISTINCT oi.id) as total_items
    FROM `bigquery-public-data.thelook_ecommerce.orders` o
    LEFT JOIN `bigquery-public-data.thelook_ecommerce.users` u
        ON o.user_id = u.id
    LEFT JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi
        ON o.order_id = oi.order_id
    """
    
    try:
        query_job = client.query(relationship_query)
        results = query_job.result()
        for row in results:
            print(f"\nRelationship Summary:")
            print(f"Total Orders: {row.total_orders:,}")
            print(f"Total Users with Orders: {row.total_users:,}")
            print(f"Total Order Items: {row.total_items:,}")
    except Exception as e:
        print(f"Error checking relationships: {e}")

if __name__ == "__main__":
    analyze_relationships()
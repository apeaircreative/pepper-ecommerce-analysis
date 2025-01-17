"""
Test dataset integrity and availability.
"""
import pytest
from google.cloud import bigquery
import pandas as pd
from pathlib import Path

@pytest.fixture
def bq_client():
    """Create BigQuery client."""
    return bigquery.Client()

@pytest.fixture
def project_id():
    """Project ID for tests."""
    return "pepper-data-analytics"

@pytest.fixture
def dataset_id():
    """Dataset ID for tests."""
    return "olist_data"

def test_olist_files_exist():
    """Test that Olist files exist locally."""
    data_dir = Path("data/olist")
    required_files = [
        "olist_customers_dataset.csv",
        "olist_orders_dataset.csv",
        "olist_order_items_dataset.csv",
        "olist_products_dataset.csv"
    ]
    
    for file in required_files:
        assert (data_dir / file).exists(), f"Missing required file: {file}"

def test_bigquery_tables_exist(bq_client, project_id, dataset_id):
    """Test that tables exist in BigQuery."""
    dataset_ref = f"{project_id}.{dataset_id}"
    required_tables = [
        "olist_customers_dataset",
        "olist_orders_dataset",
        "olist_order_items_dataset",
        "olist_products_dataset"
    ]
    
    tables = list(bq_client.list_tables(dataset_ref))
    table_ids = [table.table_id for table in tables]
    
    for table in required_tables:
        assert table in table_ids, f"Missing required table: {table}"

def test_table_schemas(bq_client, project_id, dataset_id):
    """Test that table schemas match expectations."""
    # Test products table schema
    table_ref = f"{project_id}.{dataset_id}.olist_products_dataset"
    table = bq_client.get_table(table_ref)
    
    expected_columns = {
        'product_id', 'product_category_name', 'product_name_lenght',
        'product_description_lenght', 'product_photos_qty', 'product_weight_g',
        'product_length_cm', 'product_height_cm', 'product_width_cm'
    }
    
    actual_columns = {field.name for field in table.schema}
    assert expected_columns.issubset(actual_columns), "Missing required columns in products table"

def test_data_quality(bq_client, project_id, dataset_id):
    """Test basic data quality rules."""
    # Test product data quality
    query = f"""
    SELECT COUNT(*) as invalid_count
    FROM `{project_id}.{dataset_id}.olist_products_dataset`
    WHERE product_weight_g <= 0
        OR product_length_cm <= 0
        OR product_height_cm <= 0
        OR product_width_cm <= 0
    """
    
    query_job = bq_client.query(query)
    results = query_job.result()
    row = next(results)
    
    assert row.invalid_count == 0, "Found products with invalid dimensions"

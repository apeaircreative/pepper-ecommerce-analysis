"""
Tests for data collection pipeline.
"""
import pytest
import pandas as pd
from pathlib import Path
from scripts.scrapers.collect_pepper_data import (
    load_config,
    collect_data,
    validate_data,
    transform_data
)
import logging

@pytest.fixture
def logger():
    """Create test logger."""
    return logging.getLogger('test_logger')

@pytest.fixture
def sample_config():
    """Create sample configuration."""
    return {
        'shopify': {
            'base_url': 'https://www.wearpepper.com',
            'collections': {
                'bras': {'main': '/collections/bras'}
            }
        }
    }

@pytest.fixture
def sample_raw_data():
    """Create sample raw data."""
    products = pd.DataFrame([
        {
            'product_id': 123456,
            'product_title': 'Classic T-Shirt Bra',
            'variant_id': 789012,
            'sku': 'BRA035BU32AA',
            'price': 65.00,
            'size': '32AA',
            'color': 'Buff'
        }
    ])
    
    return {'products': products}

def test_load_config(tmp_path):
    """Test configuration loading."""
    # Create test config
    config_dir = tmp_path / 'config'
    config_dir.mkdir()
    config_file = config_dir / 'urls.yaml'
    
    with open(config_file, 'w') as f:
        f.write("""
shopify:
  base_url: https://www.wearpepper.com
  collections:
    bras:
      main: /collections/bras
        """)
    
    # Test loading
    config = load_config()
    assert config['shopify']['base_url'] == 'https://www.wearpepper.com'
    assert config['shopify']['collections']['bras']['main'] == '/collections/bras'

def test_validate_data(sample_raw_data, logger):
    """Test data validation."""
    results = validate_data(sample_raw_data, logger)
    
    assert 'products' in results
    assert isinstance(results['products'], dict)

def test_transform_data(sample_raw_data, logger):
    """Test data transformation."""
    transformed = transform_data(sample_raw_data, logger)
    
    assert 'products' in transformed
    assert isinstance(transformed['products'], pd.DataFrame)
    
    # Check Olist schema compatibility
    expected_columns = {
        'product_id', 'product_category_name', 'product_name_lenght',
        'product_description_lenght', 'product_photos_qty', 'product_weight_g',
        'product_length_cm', 'product_height_cm', 'product_width_cm'
    }
    assert set(transformed['products'].columns) == expected_columns

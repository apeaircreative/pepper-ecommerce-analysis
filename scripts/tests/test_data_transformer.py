"""
Tests for data transformation functionality.
"""
import pytest
import pandas as pd
from scripts.utils.data_transformer import DataTransformer

@pytest.fixture
def sample_shopify_data():
    """Create sample Shopify data for testing."""
    return pd.DataFrame([
        {
            'product_id': 123456,
            'product_title': 'Classic T-Shirt Bra',
            'variant_id': 789012,
            'sku': 'BRA035BU32AA',
            'price': 65.00,
            'size': '32AA',
            'color': 'Buff'
        },
        {
            'product_id': 123456,
            'product_title': 'Classic T-Shirt Bra',
            'variant_id': 789013,
            'sku': 'BRA035BU34B',
            'price': 65.00,
            'size': '34B',
            'color': 'Buff'
        }
    ])

def test_transform_products(sample_shopify_data):
    """Test product data transformation."""
    transformer = DataTransformer()
    result = transformer.transform_products(sample_shopify_data)
    
    # Check schema
    expected_columns = {
        'product_id', 'product_category_name', 'product_name_lenght',
        'product_description_lenght', 'product_photos_qty', 'product_weight_g',
        'product_length_cm', 'product_height_cm', 'product_width_cm'
    }
    assert set(result.columns) == expected_columns
    
    # Check data
    assert len(result) == 2
    assert result['product_category_name'].unique() == ['fashion_lingerie']
    assert all(result['product_name_lenght'] == len('Classic T-Shirt Bra'))

def test_transform_order_items(sample_shopify_data):
    """Test order items data transformation."""
    transformer = DataTransformer()
    result = transformer.transform_order_items(sample_shopify_data)
    
    # Check schema
    expected_columns = {
        'order_id', 'order_item_id', 'product_id', 'seller_id',
        'shipping_limit_date', 'price', 'freight_value'
    }
    assert set(result.columns) == expected_columns
    
    # Check data
    assert len(result) == 2
    assert all(result['seller_id'] == 'pepper_direct')
    assert all(result['price'] == 65.00)
    assert all(result['order_item_id'] == 1)

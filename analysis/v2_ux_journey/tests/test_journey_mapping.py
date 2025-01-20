"""
Test suite for the JourneyMapper class using Pepper's data structure.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..core.journey_mapping import JourneyMapper
from ..utils.data_loader import load_pepper_data, validate_columns

class TestJourneyMapper:
    @pytest.fixture
    def sample_data(self):
        """Create sample Pepper order and product data."""
        orders_data = {
            'id': [f'order_{i}' for i in range(1, 11)],
            'customer_id': ['cust_1', 'cust_1', 'cust_2', 'cust_2', 'cust_2',
                          'cust_3', 'cust_3', 'cust_4', 'cust_4', 'cust_4'],
            'status': ['complete', 'complete', 'complete', 'returned', 'complete',
                      'complete', 'complete', 'complete', 'complete', 'complete'],
            'created_at': [
                '2024-12-01', '2024-12-15', '2024-12-01', '2024-12-05',
                '2024-12-10', '2024-12-01', '2024-12-15', '2024-12-01',
                '2024-12-15', '2024-12-30'
            ],
            'product_id': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
        }
        
        products_data = {
            'product_id': list(range(1, 6)),
            'name': [
                'Classic All You Bra - Black',
                'Mesh All You Bra - Sand',
                'Signature Lace Bra - Flora',
                'Ultimate T-Shirt Bra - Black',
                'Strapless Bra - Buff'
            ],
            'sku': [
                'BRA001BL34AA',
                'BRA002SD36A',
                'BRA003FL32B',
                'BRA004BL34A',
                'BRA005BU38AA'
            ],
            'retail_price': [55.0, 65.0, 45.0, 65.0, 60.0],
            'category': [
                'Classic', 'Mesh', 'Signature', 'T-Shirt', 'Strapless'
            ]
        }
        
        orders_df = pd.DataFrame(orders_data)
        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
        orders_df['is_return'] = orders_df['status'] == 'returned'
        
        products_df = pd.DataFrame(products_data)
        
        return orders_df, products_df
    
    def test_data_preparation(self, sample_data):
        """Test data preparation and size extraction."""
        orders_df, products_df = sample_data
        mapper = JourneyMapper(orders_df, products_df)
        
        # Check size extraction
        assert 'size' in mapper.products.columns
        assert 'band_size' in mapper.products.columns
        assert 'cup_size' in mapper.products.columns
        
        # Verify specific size extraction
        first_product = mapper.products.iloc[0]
        assert first_product['size'] == '34AA'
        assert first_product['band_size'] == '34'
        assert first_product['cup_size'] == 'AA'
        
        # Check style extraction
        assert 'style' in mapper.products.columns
        assert mapper.products.iloc[0]['style'] == 'Classic All You Bra'
    
    def test_entry_point_identification(self, sample_data):
        """Test entry point analysis with Pepper products."""
        orders_df, products_df = sample_data
        mapper = JourneyMapper(orders_df, products_df)
        
        entry_points = mapper.identify_entry_points()
        
        # Check structure
        assert isinstance(entry_points, dict)
        assert all(isinstance(v, float) for v in entry_points.values())
        
        # Verify frequencies sum to approximately 100%
        assert abs(sum(entry_points.values()) - 100.0) < 0.1
        
        # Check specific entry points
        assert 'Classic All You Bra' in entry_points
        assert 'Signature Lace Bra' in entry_points
    
    def test_confidence_progression(self, sample_data):
        """Test confidence score calculation."""
        orders_df, products_df = sample_data
        mapper = JourneyMapper(orders_df, products_df)
        
        confidence_scores = mapper.map_confidence_progression()
        
        # Check structure
        assert isinstance(confidence_scores, dict)
        assert all(isinstance(scores, list) for scores in confidence_scores.values())
        
        # Verify score ranges
        for scores in confidence_scores.values():
            assert all(0 <= score <= 1 for score in scores)
        
        # Check specific cases
        user_scores = confidence_scores.get('cust_2')
        assert user_scores is not None
        assert len(user_scores) > 1  # Multiple purchases
        
        # Return should lower confidence
        assert user_scores[1] < user_scores[0]  # After return
    
    def test_category_flow(self, sample_data):
        """Test bra style transition analysis."""
        orders_df, products_df = sample_data
        mapper = JourneyMapper(orders_df, products_df)
        
        flow_patterns = mapper.analyze_category_flow()
        
        # Check structure
        assert isinstance(flow_patterns, dict)
        for transitions in flow_patterns.values():
            assert isinstance(transitions, list)
            assert all(isinstance(t, tuple) and len(t) == 2 for t in transitions)
        
        # Verify probabilities
        for transitions in flow_patterns.values():
            probs = [prob for _, prob in transitions]
            assert all(0 <= p <= 1 for p in probs)
            assert sum(probs) <= 1.0
    
    def test_edge_cases(self, sample_data):
        """Test edge cases and error handling."""
        orders_df, products_df = sample_data
        
        # Test with single purchase customer
        single_order = orders_df.iloc[[0]]
        mapper = JourneyMapper(single_order, products_df)
        
        confidence_scores = mapper.map_confidence_progression()
        assert 'cust_1' not in confidence_scores  # Should skip single purchase
        
        # Test with empty data
        empty_orders = orders_df.iloc[0:0]
        mapper = JourneyMapper(empty_orders, products_df)
        
        assert len(mapper.identify_entry_points()) == 0
        assert len(mapper.map_confidence_progression()) == 0
        assert len(mapper.analyze_category_flow()) == 0
    
    def test_performance(self, sample_data):
        """Test performance with larger dataset."""
        orders_df, products_df = sample_data
        
        # Create larger dataset
        large_orders = pd.concat([orders_df] * 100, ignore_index=True)
        large_orders['customer_id'] = large_orders.index.map(lambda x: f'cust_{x}')
        
        mapper = JourneyMapper(large_orders, products_df)
        
        # Ensure methods complete in reasonable time
        import time
        
        start = time.time()
        mapper.identify_entry_points()
        assert time.time() - start < 2.0  # Should complete within 2 seconds
        
        start = time.time()
        mapper.map_confidence_progression()
        assert time.time() - start < 5.0  # Should complete within 5 seconds

def test_data_quality():
    """Test with actual Pepper data files."""
    try:
        orders_df, products_df = load_pepper_data("data/pepper")
        mapper = JourneyMapper(orders_df, products_df)
        
        # Basic data quality checks
        assert not orders_df.empty
        assert not products_df.empty
        assert orders_df['created_at'].dtype == 'datetime64[ns]'
        assert all(col in products_df.columns 
                  for col in ['product_id', 'name', 'sku', 'retail_price'])
        
        # Test core functionality with real data
        entry_points = mapper.identify_entry_points()
        confidence_scores = mapper.map_confidence_progression()
        flow_patterns = mapper.analyze_category_flow()
        
        assert len(entry_points) > 0
        assert len(confidence_scores) > 0
        assert len(flow_patterns) > 0
        
    except Exception as e:
        pytest.fail(f"Failed with real data: {str(e)}")

def test_column_validation():
    """Test column validation functionality."""
    required_cols = ['id', 'customer_id', 'status']
    df = pd.DataFrame({'id': [1], 'status': ['complete']})
    
    with pytest.raises(ValueError) as exc_info:
        validate_columns(df, required_cols, "Test")
    assert "Missing required columns" in str(exc_info.value)

if __name__ == '__main__':
    pytest.main(['-v'])
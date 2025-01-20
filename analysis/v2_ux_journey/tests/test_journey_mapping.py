"""
Test suite for the JourneyMapper class using Pepper's data structure.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..core.journey_mapping import JourneyMapper, JourneyStage
from ..utils.data_loader import load_pepper_data, validate_columns

@pytest.fixture(autouse=True)
def setup_module():
    """Setup any state specific to the execution of the given module."""
    pd.set_option('mode.chained_assignment', None)
    yield
    pd.reset_option('mode.chained_assignment')

class TestJourneyMapper:
    @pytest.fixture
    def sample_data(self):
        """Create sample Pepper order and product data."""
        orders_data = {
            'id': [f'order_{i}' for i in range(1, 16)],
            'customer_id': [
                # First Purchase (1 order)
                'cust_new',
                # Size Exploration (2 orders, same style)
                'cust_size', 'cust_size',
                # Style Exploration (3 orders, different styles, some returns)
                'cust_style', 'cust_style', 'cust_style',
                # Confidence Building (4 orders, consistent size)
                'cust_conf', 'cust_conf', 'cust_conf', 'cust_conf',
                # Brand Loyal (5+ orders, high confidence)
                'cust_loyal', 'cust_loyal', 'cust_loyal', 'cust_loyal', 'cust_loyal'
            ],
            'status': [
                # First Purchase
                'complete',
                # Size Exploration (1 return)
                'returned', 'complete',
                # Style Exploration (1 return)
                'complete', 'returned', 'complete',
                # Confidence Building (no returns)
                'complete', 'complete', 'complete', 'complete',
                # Brand Loyal (no returns)
                'complete', 'complete', 'complete', 'complete', 'complete'
            ],
            'created_at': [
                # Timestamps ensuring proper order
                '2024-12-01',
                '2024-12-01', '2024-12-15',
                '2024-12-01', '2024-12-05', '2024-12-10',
                '2024-12-01', '2024-12-10', '2024-12-20', '2024-12-30',
                '2024-12-01', '2024-12-10', '2024-12-20', '2024-12-25', '2024-12-30'
            ],
            'product_id': [
                1,  # First Purchase
                1, 1,  # Size Exploration (same style)
                1, 2, 3,  # Style Exploration (different styles)
                4, 4, 4, 4,  # Confidence Building (consistent)
                5, 5, 5, 5, 5  # Brand Loyal (very consistent)
            ]
        }
        
        products_data = {
            'product_id': list(range(1, 6)),
            'name': [
                'Classic All You Bra - Black',
                'Signature Lace Bra - Sand',  # Changed to match test expectation
                'Mesh All You Bra - Flora',
                'Ultimate T-Shirt Bra - Black',
                'Strapless Bra - Buff'
            ],
            'sku': [
                'BRA001BL34AA',
                'BRA002SD34AA',  # Same size as first
                'BRA003FL36B',   # Different size
                'BRA004BL34AA',  # Back to original size
                'BRA005BU34AA'   # Consistent size
            ],
            'retail_price': [55.0, 65.0, 45.0, 65.0, 60.0],
            'category': ['Classic', 'Signature', 'Mesh', 'T-Shirt', 'Strapless']
        }
        
        # Convert to DataFrames
        orders_df = pd.DataFrame(orders_data)
        products_df = pd.DataFrame(products_data)
        
        # Add returned column based on status
        orders_df['returned'] = orders_df['status'].str.lower() == 'returned'
        
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
        total_freq = sum(entry_points.values())
        assert 0.99 <= total_freq <= 1.01, f"Total frequency {total_freq} is not close to 1.0"
        
        # Print debug information
        print("\nEntry points found:", entry_points)
        print("\nAvailable product names:", products_df['name'].tolist())
        
        # Check specific entry points (at least one should be present)
        expected_products = [
            'Classic All You Bra - Black',
            'Signature Lace Bra - Sand',
            'Mesh All You Bra - Flora'
        ]
        found_products = [name for name in expected_products if name in entry_points]
        assert len(found_products) > 0, f"None of the expected products {expected_products} found in entry points {entry_points}"
        
        # Check that frequencies make sense
        for name, freq in entry_points.items():
            assert 0.0 <= freq <= 1.0, f"Invalid frequency {freq} for product {name}"
    
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
        loyal_scores = confidence_scores.get('cust_loyal')
        assert loyal_scores is not None
        assert len(loyal_scores) > 1  # Multiple purchases
        assert loyal_scores[-1] > 0.7  # High confidence for loyal customer
        
        new_scores = confidence_scores.get('cust_new')
        assert new_scores is not None
        assert len(new_scores) == 1  # Single purchase
        
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
        mapper = JourneyMapper(orders_df, products_df)
        
        # Test non-existent customer
        stage, score = mapper.determine_journey_stage('non_existent_customer')
        assert stage == JourneyStage.FIRST_PURCHASE
        assert score == 0.0
        
        # Test customer with single order
        stage, score = mapper.determine_journey_stage('cust_new')
        assert stage == JourneyStage.FIRST_PURCHASE
        assert 0.0 <= score <= 1.0
        
        # Test customer with all returns
        stage, score = mapper.determine_journey_stage('cust_size')
        assert stage == JourneyStage.SIZE_EXPLORATION
        assert 0.0 <= score <= 1.0
    
    def test_performance(self, sample_data):
        """Test performance with larger dataset."""
        orders_df, products_df = sample_data
        
        # Create a larger dataset by duplicating existing data
        large_orders = pd.concat([orders_df] * 100, ignore_index=True)
        large_orders['customer_id'] = large_orders.index.map(lambda x: f'cust_{x}')
        
        # Measure performance
        import time
        start_time = time.time()
        
        mapper = JourneyMapper(large_orders, products_df)
        
        # Test entry point identification
        entry_points = mapper.identify_entry_points()
        assert isinstance(entry_points, dict)
        
        # Test journey stage determination
        stage, score = mapper.determine_journey_stage('cust_0')
        assert isinstance(stage, JourneyStage)
        assert 0.0 <= score <= 1.0
        
        # Verify execution time
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Performance test took {execution_time:.2f} seconds"

    def test_journey_stages(self, sample_data):
        """Test journey stage determination for different customer profiles."""
        orders_df, products_df = sample_data
        mapper = JourneyMapper(orders_df, products_df)
        
        # Test each customer profile
        assert mapper.determine_journey_stage('cust_new')[0] == JourneyStage.FIRST_PURCHASE
        assert mapper.determine_journey_stage('cust_size')[0] == JourneyStage.SIZE_EXPLORATION
        assert mapper.determine_journey_stage('cust_style')[0] == JourneyStage.STYLE_EXPLORATION
        assert mapper.determine_journey_stage('cust_conf')[0] == JourneyStage.CONFIDENCE_BUILDING
        assert mapper.determine_journey_stage('cust_loyal')[0] == JourneyStage.BRAND_LOYAL

    def test_confidence_score_calculation(self, sample_data):
        """Test confidence score calculation logic."""
        orders_df, products_df = sample_data
        mapper = JourneyMapper(orders_df, products_df)
        
        # Brand loyal customer should have highest confidence
        loyal_stage, loyal_score = mapper.determine_journey_stage('cust_loyal')
        style_stage, style_score = mapper.determine_journey_stage('cust_style')
        
        # Loyal customer should have higher confidence than style explorer
        assert loyal_score > style_score
        
        # All scores should be between 0 and 1
        for customer_id in orders_df['customer_id'].unique():
            _, score = mapper.determine_journey_stage(customer_id)
            assert 0.0 <= score <= 1.0

@pytest.mark.skip(reason="Requires actual Pepper data files")
def test_data_quality():
    """Test with actual Pepper data files."""
    try:
        orders_df, products_df = load_pepper_data('data/pepper')
        
        # Verify basic data quality
        assert len(orders_df) > 0, "Orders DataFrame is empty"
        assert len(products_df) > 0, "Products DataFrame is empty"
        
        # Check required columns
        required_order_cols = ['customer_id', 'product_id', 'created_at', 'returned']
        required_product_cols = ['product_id', 'name', 'sku']
        
        validate_columns(orders_df, required_order_cols, 'Orders')
        validate_columns(products_df, required_product_cols, 'Products')
        
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")

def test_column_validation():
    """Test column validation functionality."""
    required_cols = ['id', 'customer_id', 'status']
    df = pd.DataFrame({'id': [1], 'status': ['complete']})
    
    with pytest.raises(ValueError) as exc_info:
        validate_columns(df, required_cols, "Test")
    assert "Missing required columns" in str(exc_info.value)

if __name__ == '__main__':
    # Run tests with verbose output, show locals on failure, and generate coverage report
    pytest.main([
        '-v',  # verbose output
        '--showlocals',  # show local variables on failures
        '--cov=core',  # measure code coverage for core module
        '--cov-report=term-missing',  # show lines missing coverage
        'test_journey_mapping.py'
    ])
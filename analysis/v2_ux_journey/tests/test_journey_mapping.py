"""
Test Suite for Journey Mapping Analysis

This module contains comprehensive tests for the customer journey mapping functionality,
following best practices for data analysis testing.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..core.journey_mapping import JourneyMapper

class TestJourneyMapper(unittest.TestCase):
    """Test cases for JourneyMapper class."""
    
    def setUp(self):
        """
        Set up test data that represents a realistic subset of customer journeys.
        """
        # Sample orders data
        self.orders = pd.DataFrame({
            'customer_id': ['C1', 'C1', 'C2', 'C2', 'C2', 'C3'],
            'order_id': ['O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
            'product_id': ['P1', 'P2', 'P1', 'P3', 'P2', 'P1'],
            'size': ['M', 'M', 'L', 'L', 'L', 'S'],
            'order_date': pd.date_range('2025-01-01', periods=6),
            'is_return': [False, False, False, True, False, False]
        })
        
        # Sample products data
        self.products = pd.DataFrame({
            'product_id': ['P1', 'P2', 'P3'],
            'category': ['Tops', 'Bottoms', 'Dresses'],
            'style': ['Casual', 'Formal', 'Casual'],
            'size_range': ['S,M,L', 'S,M,L', 'S,M,L']
        })
        
        self.mapper = JourneyMapper(self.orders, self.products)
    
    def test_entry_point_identification(self):
        """Test accurate identification of customer entry points."""
        entry_points = self.mapper.identify_entry_points()
        
        # Test entry point distribution
        self.assertIn('P1', entry_points)
        self.assertEqual(len(entry_points), 1)  # Only P1 is an entry point
        self.assertAlmostEqual(entry_points['P1'], 1.0)  # 100% of customers
        
    def test_confidence_progression(self):
        """Test confidence score calculation and progression."""
        confidence_scores = self.mapper.map_confidence_progression()
        
        # Test confidence tracking
        self.assertIn('C1', confidence_scores)
        self.assertTrue(len(confidence_scores['C1']) >= 2)  # At least 2 points
        self.assertTrue(all(0 <= score <= 1 for score in confidence_scores['C1']))
        
    def test_category_flow(self):
        """Test category transition analysis."""
        category_flows = self.mapper.analyze_category_flow()
        
        # Test category transitions
        self.assertIn('Tops', category_flows)
        self.assertTrue(any('Bottoms' in [cat for cat, _ in flows] 
                          for flows in category_flows.values()))
        
    def test_edge_cases(self):
        """Test handling of edge cases and unusual patterns."""
        # Single purchase customer
        single_orders = pd.DataFrame({
            'customer_id': ['C4'],
            'order_id': ['O7'],
            'product_id': ['P1'],
            'size': ['M'],
            'order_date': [pd.Timestamp('2025-01-07')],
            'is_return': [False]
        })
        
        mapper = JourneyMapper(single_orders, self.products)
        confidence = mapper.map_confidence_progression()
        
        self.assertIn('C4', confidence)
        self.assertEqual(len(confidence['C4']), 1)
        
    def test_data_quality(self):
        """Test handling of data quality issues."""
        # Missing size
        orders_missing_size = self.orders.copy()
        orders_missing_size.loc[0, 'size'] = None
        
        mapper = JourneyMapper(orders_missing_size, self.products)
        confidence = mapper.map_confidence_progression()
        
        self.assertTrue(all(score >= 0 for scores in confidence.values() 
                          for score in scores))
        
    def test_performance(self):
        """Test performance with larger datasets."""
        # Generate larger test dataset
        n_customers = 1000
        n_orders = 5000
        
        large_orders = pd.DataFrame({
            'customer_id': [f'C{i}' for i in range(n_orders)],
            'order_id': [f'O{i}' for i in range(n_orders)],
            'product_id': np.random.choice(['P1', 'P2', 'P3'], n_orders),
            'size': np.random.choice(['S', 'M', 'L'], n_orders),
            'order_date': pd.date_range('2025-01-01', periods=n_orders),
            'is_return': np.random.choice([True, False], n_orders, p=[0.1, 0.9])
        })
        
        mapper = JourneyMapper(large_orders, self.products)
        
        # Test processing time
        import time
        start_time = time.time()
        mapper.identify_entry_points()
        end_time = time.time()
        
        self.assertLess(end_time - start_time, 5.0)  # Should process in <5s

if __name__ == '__main__':
    unittest.main()
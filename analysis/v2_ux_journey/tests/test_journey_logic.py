"""
Test Journey Mapping Logic

This module contains tests for the journey mapping functionality.
"""

import unittest
import pandas as pd
import numpy as np
from ..core.journey_mapping import JourneyMapper

class TestJourneyMapper(unittest.TestCase):
    """Test cases for JourneyMapper class."""
    
    def setUp(self):
        """Set up test data."""
        self.orders = pd.DataFrame({
            'customer_id': ['C1', 'C1', 'C2', 'C2', 'C2'],
            'product_id': ['P1', 'P2', 'P3', 'P1', 'P4'],
            'order_date': pd.date_range(start='2025-01-01', periods=5)
        })
        
        self.products = pd.DataFrame({
            'product_id': ['P1', 'P2', 'P3', 'P4'],
            'category': ['Sports', 'Classic', 'Lace', 'Strapless']
        })
        
        self.mapper = JourneyMapper(self.orders, self.products)
        
    def test_identify_entry_points(self):
        """Test entry point identification."""
        entry_points = self.mapper.identify_entry_points()
        self.assertIn('P1', entry_points)
        self.assertIn('P3', entry_points)
        
    def test_confidence_progression(self):
        """Test confidence progression mapping."""
        progression = self.mapper.map_confidence_progression()
        self.assertTrue(len(progression) > 0)
        
    def test_category_flow(self):
        """Test category flow analysis."""
        flow = self.mapper.analyze_category_flow()
        self.assertIn('Sports', flow)
        
if __name__ == '__main__':
    unittest.main()

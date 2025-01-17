"""
Test Shopify scraper functionality.
"""
import unittest
from pathlib import Path
import pandas as pd
from scripts.utils.shopify_utils import ShopifyScraper

class TestShopifyScraper(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.config_path = Path("scripts/scrapers/config/urls.yaml")
        self.scraper = ShopifyScraper(str(self.config_path))
        
    def test_sku_validation(self):
        """Test SKU validation patterns."""
        # Valid SKUs
        self.assertTrue(self.scraper.validate_sku("BRA035BU32AA")['valid'])
        self.assertTrue(self.scraper.validate_sku("ZGW01BL32A")['valid'])
        self.assertTrue(self.scraper.validate_sku("SAY01SD34AA")['valid'])
        self.assertTrue(self.scraper.validate_sku("LUB01FA36B")['valid'])
        
        # Invalid SKUs
        self.assertFalse(self.scraper.validate_sku("INVALID123")['valid'])
        self.assertFalse(self.scraper.validate_sku("")['valid'])
        
    def test_price_validation(self):
        """Test price validation."""
        # Valid prices
        self.assertTrue(self.scraper.validate_price("BRA035BU32AA", 65.00))
        self.assertTrue(self.scraper.validate_price("SAY01SD34AA", 60.00))
        
        # Invalid prices
        self.assertFalse(self.scraper.validate_price("BRA035BU32AA", 70.00))
        self.assertFalse(self.scraper.validate_price("SAY01SD34AA", 55.00))
        
    def test_size_validation(self):
        """Test size format validation."""
        test_data = {
            'sku': ['BRA035BU32AA'],
            'price': [65.00],
            'size': ['32AA'],
            'color': ['Buff']
        }
        df = pd.DataFrame(test_data)
        
        valid_df = self.scraper.validate_data(df)
        self.assertEqual(len(valid_df), 1)
        
        # Test invalid size
        test_data['size'] = ['32C']  # Invalid cup size
        df = pd.DataFrame(test_data)
        valid_df = self.scraper.validate_data(df)
        self.assertEqual(len(valid_df), 0)
        
if __name__ == '__main__':
    unittest.main()

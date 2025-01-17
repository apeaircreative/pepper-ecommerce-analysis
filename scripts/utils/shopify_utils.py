"""
Utility functions for interacting with Shopify API.
"""
import requests
import yaml
from pathlib import Path
import logging
from typing import Dict, List, Optional
import time
from datetime import datetime

class ShopifyScraper:
    """Scrape data from Shopify store."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        self.logger = logging.getLogger('shopify_scraper')
        self.logger.info("Initializing Shopify scraper")
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.logger.info(f"Loaded configuration from {config_path}")
        
        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Pepper Analytics/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.rate_limits = self.config['shopify']['rate_limits']
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def _handle_rate_limits(self):
        """Handle rate limiting."""
        time.sleep(1 / self.rate_limits['requests_per_second'])
    
    def get_collection_products(self, collection_path: str) -> List[Dict]:
        """Get products from a collection."""
        self.logger.info(f"Fetching products from collection: {collection_path}")
        
        try:
            url = f"{self.config['shopify']['base_url']}{collection_path}/products.json"
            response = self.session.get(url)
            response.raise_for_status()
            
            products = response.json()['products']
            self.logger.info(f"Found {len(products)} products in collection")
            
            # Extract relevant fields
            processed_products = []
            for product in products:
                for variant in product['variants']:
                    processed_products.append({
                        'product_id': product['id'],
                        'title': product['title'],
                        'variant_id': variant['id'],
                        'sku': variant['sku'],
                        'price': float(variant['price']),
                        'weight': float(variant.get('weight', 0)),
                        'width': float(variant.get('width', 0)),
                        'height': float(variant.get('height', 0)),
                        'length': float(variant.get('length', 0))
                    })
            
            return processed_products
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching products: {str(e)}")
            raise
    
    def get_orders(self, params: Dict) -> List[Dict]:
        """Get orders with pagination."""
        try:
            url = f"{self.config['shopify']['base_url']}{self.config['shopify']['endpoints']['orders']}"
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            orders = response.json()['orders']
            
            # Process orders to extract relevant fields
            processed_orders = []
            for order in orders:
                processed_order = {
                    'id': order['id'],
                    'customer_id': order['customer']['id'],
                    'created_at': order['created_at'],
                    'processed_at': order['processed_at'],
                    'financial_status': order['financial_status'],
                    'fulfillment_status': order['fulfillment_status'],
                    'total_price': float(order['total_price']),
                    'subtotal_price': float(order['subtotal_price']),
                    'total_tax': float(order['total_tax']),
                    'total_shipping_price': float(order['total_shipping_price_set']['shop_money']['amount']),
                    'billing_address': order.get('billing_address', {}),
                    'shipping_address': order.get('shipping_address', {}),
                    'line_items': [
                        {
                            'product_id': item['product_id'],
                            'variant_id': item['variant_id'],
                            'title': item['title'],
                            'quantity': item['quantity'],
                            'price': float(item['price']),
                            'sku': item['sku']
                        }
                        for item in order['line_items']
                    ]
                }
                processed_orders.append(processed_order)
            
            self._handle_rate_limits()
            return processed_orders
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching orders: {str(e)}")
            raise
    
    def get_customers(self, params: Dict) -> List[Dict]:
        """Get customers with pagination."""
        # Will implement when we move to customer collection
        pass

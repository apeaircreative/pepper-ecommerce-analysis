"""
Transform collected data to match TheLook schema for Shopify analytics simulation.
"""
import pandas as pd
import numpy as np
from typing import Dict
import logging

class DataTransformer:
    """Transform Pepper data to match TheLook schema."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Default measurements for bras (based on typical measurements)
        self.default_measurements = {
            'product_weight_g': 150,    # Average bra weight
            'product_length_cm': 25,    # Length when laid flat
            'product_height_cm': 15,    # Height when laid flat
            'product_width_cm': 5       # Width/depth when folded
        }
        
        # Category mapping
        self.category_mapping = {
            'Bras': 'Intimates',
            'Wireless': 'Intimates',
            'Strapless': 'Intimates',
            'Sports': 'Athletic'
        }
    
    def transform_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform product data to match TheLook schema."""
        # Create DataFrame with TheLook schema
        transformed = pd.DataFrame({
            'id': df['product_id'],
            'brand': 'Pepper',  # All products are Pepper brand
            'category': df['title'].apply(self._map_category),
            'name': df['title'],
            'retail_price': df['price'],
            'department': 'Womens',
            'sku': df['sku'],
            'distribution_center_id': 1,  # Default as we have one source
            'cost': df['price'].apply(lambda x: x * 0.4),  # Estimated COGS
            'product_weight_g': df['weight'].replace(0, self.default_measurements['product_weight_g']),
            'product_length_cm': df['length'].replace(0, self.default_measurements['product_length_cm']),
            'product_height_cm': df['height'].replace(0, self.default_measurements['product_height_cm']),
            'product_width_cm': df['width'].replace(0, self.default_measurements['product_width_cm'])
        })
        
        # Add inventory fields
        transformed['inventory_item_id'] = df['variant_id']
        transformed['inventory_quantity'] = 100  # Default stock level
        transformed['inventory_location'] = 'MAIN_WAREHOUSE'
        
        return transformed
    
    def _map_category(self, title: str) -> str:
        """Map product title to TheLook category."""
        for key, value in self.category_mapping.items():
            if key.lower() in title.lower():
                return value
        return 'Intimates'  # Default category
    
    def transform_order_items(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform order items to match TheLook schema."""
        transformed = pd.DataFrame({
            'id': df['variant_id'],
            'order_id': None,  # Will be populated when we have order data
            'user_id': None,   # Will be populated when we have customer data
            'product_id': df['product_id'],
            'inventory_item_id': df['variant_id'],
            'status': 'Complete',
            'sale_price': df['price'],
            'shipping_cost': 0,  # Will update when we have shipping data
            'created_at': pd.Timestamp.now(),  # Will update with actual order dates
            'shipped_at': None,
            'delivered_at': None,
            'returned_at': None
        })
        
        return transformed

    def transform_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform order data to match TheLook schema."""
        # For simulated data, we already have the items in separate rows
        transformed = df.copy()
        
        # Ensure all required columns are present
        required_columns = [
            'order_id', 'user_id', 'product_id', 'status',
            'sale_price', 'shipping_cost', 'created_at',
            'shipped_at', 'delivered_at', 'returned_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in transformed.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert timestamps
        date_columns = ['created_at', 'shipped_at', 'delivered_at', 'returned_at']
        for col in date_columns:
            if col in transformed.columns:
                transformed[col] = pd.to_datetime(transformed[col])
        
        return transformed[required_columns]

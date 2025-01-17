"""
Simulate realistic e-commerce data for development and testing.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Tuple

class DataSimulator:
    """Generate realistic e-commerce data."""
    
    def __init__(self):
        """Initialize simulator with default parameters."""
        self.order_patterns = {
            'weekday_distribution': {
                0: 0.15,  # Monday
                1: 0.15,  # Tuesday
                2: 0.15,  # Wednesday
                3: 0.15,  # Thursday
                4: 0.20,  # Friday
                5: 0.10,  # Saturday
                6: 0.10   # Sunday
            },
            'hour_distribution': {
                'peak': [10, 11, 12, 13, 14, 15, 16],  # Peak shopping hours
                'regular': [9, 17, 18, 19, 20],        # Regular hours
                'low': [0, 1, 2, 3, 4, 5, 6, 7, 8, 21, 22, 23]  # Low activity
            }
        }
        
        self.shipping_rules = {
            'base_rate': 5.99,
            'free_threshold': 75.00,
            'tax_rate': 0.08
        }
    
    def generate_orders(self, products_df: pd.DataFrame, 
                       num_days: int = 30,
                       orders_per_day: int = 20) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate realistic order data using actual products."""
        
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=num_days)
        
        # Generate orders
        orders = []
        order_items = []
        
        for _ in range(num_days * orders_per_day):
            # Generate order date
            date = self._generate_realistic_date(start_date, end_date)
            
            # Generate items in order (1-3 items)
            num_items = np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])
            
            # Select random products
            order_products = products_df.sample(n=num_items)
            
            # Calculate order totals
            subtotal = order_products['retail_price'].sum()
            shipping = 0 if subtotal >= self.shipping_rules['free_threshold'] else self.shipping_rules['base_rate']
            tax = subtotal * self.shipping_rules['tax_rate']
            total = subtotal + shipping + tax
            
            # Generate order record
            order_id = str(uuid.uuid4())
            customer_id = str(uuid.uuid4())
            
            order = {
                'id': order_id,
                'user_id': customer_id,
                'status': np.random.choice(
                    ['complete', 'shipped', 'pending'],
                    p=[0.7, 0.2, 0.1]
                ),
                'created_at': date,
                'total_amount': total,
                'subtotal': subtotal,
                'shipping': shipping,
                'tax': tax
            }
            orders.append(order)
            
            # Generate order items
            for _, product in order_products.iterrows():
                item = {
                    'order_id': order_id,
                    'user_id': customer_id,
                    'product_id': product['id'],
                    'inventory_item_id': product['inventory_item_id'],
                    'status': order['status'],
                    'sale_price': product['retail_price'],
                    'shipping_cost': shipping / num_items,
                    'created_at': date,
                    'shipped_at': date + timedelta(days=1) if order['status'] in ['complete', 'shipped'] else None,
                    'delivered_at': date + timedelta(days=3) if order['status'] == 'complete' else None,
                    'returned_at': None
                }
                order_items.append(item)
        
        # Convert to DataFrames
        orders_df = pd.DataFrame(orders)
        items_df = pd.DataFrame(order_items)
        
        return orders_df, items_df
    
    def _generate_realistic_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generate a realistic order timestamp."""
        # Generate random date
        days = (end_date - start_date).days
        random_days = np.random.randint(0, days + 1)
        date = start_date + timedelta(days=random_days)
        
        # Adjust for day of week probability
        while True:
            weekday = date.weekday()
            if np.random.random() <= self.order_patterns['weekday_distribution'][weekday]:
                break
            random_days = np.random.randint(0, days + 1)
            date = start_date + timedelta(days=random_days)
        
        # Add hour based on time distribution
        if date.hour in self.order_patterns['hour_distribution']['peak']:
            hour_weight = 0.6
        elif date.hour in self.order_patterns['hour_distribution']['regular']:
            hour_weight = 0.3
        else:
            hour_weight = 0.1
            
        if np.random.random() <= hour_weight:
            return date
        
        # If hour is rejected, try peak hours
        hour = np.random.choice(self.order_patterns['hour_distribution']['peak'])
        return date.replace(hour=hour)

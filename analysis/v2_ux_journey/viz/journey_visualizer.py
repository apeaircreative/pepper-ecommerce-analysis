"""
Journey Mapping Module for Pepper Data Analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class JourneyMapper:
    """Maps and analyzes customer purchase journeys for Pepper products."""
    
    def __init__(self, orders_df: pd.DataFrame, products_df: pd.DataFrame):
        """Initialize with Pepper order and product data."""
        self.orders = orders_df.copy()
        self.products = products_df.copy()
        self._prepare_data()
        
    def _prepare_data(self):
        """
        Prepare data for analysis.
        
        Raises:
            ValueError: If required columns are missing after preparation
        """
        # Validate input columns first
        required_input_cols = {
            'orders': ['customer_id', 'created_at', 'product_id', 'status'],
            'products': ['product_id', 'name', 'sku', 'retail_price']
        }
        
        missing_order_cols = set(required_input_cols['orders']) - set(self.orders.columns)
        missing_product_cols = set(required_input_cols['products']) - set(self.products.columns)
        
        if missing_order_cols or missing_product_cols:
            raise ValueError(
                f"Missing required input columns: "
                f"Orders: {missing_order_cols}, Products: {missing_product_cols}"
            )
        
        # Convert dates to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(self.orders['created_at']):
            self.orders['created_at'] = pd.to_datetime(self.orders['created_at'])
        
        # Rename user_id to customer_id if it exists
        if 'user_id' in self.orders.columns:
            self.orders = self.orders.rename(columns={'user_id': 'customer_id'})
        
        # Extract size from SKU (e.g., 'BRA028FO38AA' -> '38AA')
        size_pattern = r'(\d{2}[A-Z]{1,2})$'
        self.products['size'] = self.products['sku'].str.extract(size_pattern)
        
        # Extract band and cup sizes
        self.products['band_size'] = self.products['size'].str.extract(r'(\d{2})')
        self.products['cup_size'] = self.products['size'].str.extract(r'[0-9]{2}([A-Z]{1,2})')
        
        # Create product style from name
        self.products['style'] = self.products['name'].str.split(' - ').str[0]
        
        # Validate derived columns exist
        required_derived_cols = {
            'products': ['style', 'size', 'band_size', 'cup_size']
        }
        
        missing_derived_cols = set(required_derived_cols['products']) - set(self.products.columns)
        if missing_derived_cols:
            raise ValueError(
                f"Failed to create derived columns: {missing_derived_cols}"
            )
        
    def identify_entry_points(self) -> Dict[str, float]:
        """Identify common entry point products."""
        # Get first purchase for each customer
        first_purchases = (self.orders.sort_values('created_at')
                         .groupby('customer_id')
                         .first()
                         .reset_index())
        
        # Map to product styles
        first_purchase_styles = pd.merge(
            first_purchases,
            self.products[['product_id', 'style']],
            left_on='product_id',
            right_on='product_id',
            how='left'
        )['style']
        
        # Calculate frequencies
        style_counts = first_purchase_styles.value_counts()
        total_customers = len(first_purchases)
        
        return (style_counts / total_customers * 100).to_dict()
        
    def map_confidence_progression(self) -> Dict[str, List[float]]:
        """Maps confidence development over time."""
        confidence_scores = {}
        
        for customer_id in self.orders['customer_id'].unique():
            # Get customer's purchase history
            customer_orders = self.orders[
                self.orders['customer_id'] == customer_id
            ].sort_values('created_at')
            
            if len(customer_orders) < 2:  # Skip customers with single purchase
                continue
                
            scores = []
            for i in range(len(customer_orders)):
                history = customer_orders.iloc[:i+1]
                
                # Get product details
                purchase_details = pd.merge(
                    history,
                    self.products[['product_id', 'band_size', 'cup_size', 'style']],
                    left_on='product_id',
                    right_on='product_id',
                    how='left'
                )
                
                size_consistency = self._calculate_size_consistency(purchase_details)
                return_rate = self._calculate_return_rate(history)
                frequency_score = self._calculate_frequency_score(history)
                
                confidence = (
                    0.4 * size_consistency +
                    0.3 * (1 - return_rate) +
                    0.3 * frequency_score
                )
                
                scores.append(min(max(confidence, 0), 1))
                
            confidence_scores[customer_id] = scores
            
        return confidence_scores
    
    def _calculate_size_consistency(self, history: pd.DataFrame) -> float:
        """Calculate size consistency score."""
        if len(history) <= 1:
            return 0.5
            
        band_consistency = (
            history['band_size'].value_counts().iloc[0] / len(history)
        )
        
        cup_consistency = (
            history['cup_size'].value_counts().iloc[0] / len(history)
        )
        
        return (band_consistency + cup_consistency) / 2
    
    def _calculate_return_rate(self, history: pd.DataFrame) -> float:
        """Calculate return rate."""
        if len(history) == 0:
            return 0.0
        return (history['status'] == 'returned').mean()
    
    def _calculate_frequency_score(self, history: pd.DataFrame) -> float:
        """Calculate purchase frequency score."""
        if len(history) <= 1:
            return 0.5
            
        dates = history['created_at'].sort_values()
        days_between = (dates.diff().mean().days)
        
        return max(0, min(1, (365 - days_between) / (365 - 30)))
        
    def analyze_category_flow(self) -> Dict[str, List[Tuple[str, float]]]:
        """Analyzes bra style transition patterns."""
        style_transitions = {}
        
        for customer_id in self.orders['customer_id'].unique():
            customer_orders = self.orders[
                self.orders['customer_id'] == customer_id
            ].sort_values('created_at')
            
            if len(customer_orders) < 2:
                continue
                
            purchase_styles = pd.merge(
                customer_orders,
                self.products[['product_id', 'style']],
                left_on='product_id',
                right_on='product_id',
                how='left'
            )['style']
            
            for i in range(len(purchase_styles)-1):
                from_style = purchase_styles.iloc[i]
                to_style = purchase_styles.iloc[i+1]
                
                if from_style not in style_transitions:
                    style_transitions[from_style] = {}
                    
                if to_style not in style_transitions[from_style]:
                    style_transitions[from_style][to_style] = 0
                    
                style_transitions[from_style][to_style] += 1
                
        flow_patterns = {}
        for from_style, transitions in style_transitions.items():
            total = sum(transitions.values())
            
            significant_transitions = [
                (to_style, count/total)
                for to_style, count in transitions.items()
                if count/total >= 0.1
            ]
            
            if significant_transitions:
                flow_patterns[from_style] = sorted(
                    significant_transitions,
                    key=lambda x: x[1],
                    reverse=True
                )
                
        return flow_patterns
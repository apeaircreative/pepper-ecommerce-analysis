"""
Journey Mapping Module

This module implements customer journey analysis focusing on
post-purchase behavior and confidence development.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class JourneyMapper:
    """Maps customer journey patterns and confidence development."""
    
    def __init__(self, orders: pd.DataFrame, products: pd.DataFrame):
        """
        Initialize with order and product data.
        
        Args:
            orders: DataFrame with order history
            products: DataFrame with product details
        """
        self.orders = orders
        self.products = products
        self.journeys = {}
        self.patterns = {}
        
    def identify_entry_points(self) -> Dict[str, float]:
        """
        Returns distribution of entry points.
        
        Methodology:
        1. Group orders by customer
        2. Identify first purchase for each customer
        3. Calculate product frequency distribution
        4. Filter for significant patterns
        
        Returns:
            Dict[product_id, frequency_ratio]
        """
        # Get first purchase for each customer
        first_purchases = (self.orders.sort_values('order_date')
                          .groupby('customer_id')
                          .first()
                          .reset_index())
        
        # Calculate product frequency
        entry_counts = first_purchases['product_id'].value_counts()
        total_customers = len(first_purchases)
        
        # Convert to ratios and filter significant patterns
        entry_ratios = {
            product: count/total_customers 
            for product, count in entry_counts.items()
            if count/total_customers >= 0.1  # Filter for products used by >10% of customers
        }
        
        return entry_ratios
        
    def map_confidence_progression(self) -> Dict[str, List[float]]:
        """
        Maps confidence development over time.
        
        Methodology:
        1. Track purchase sequence for each customer
        2. Calculate confidence scores based on:
            - Size consistency (40%)
            - Return rate (30%)
            - Purchase frequency (30%)
        3. Map progression over time
        
        Returns:
            Dict[customer_id, confidence_scores]
        """
        confidence_scores = {}
        
        for customer_id in self.orders['customer_id'].unique():
            # Get customer's purchase history
            customer_orders = self.orders[
                self.orders['customer_id'] == customer_id
            ].sort_values('order_date')
            
            # Calculate running confidence scores
            scores = []
            for i in range(len(customer_orders)):
                history = customer_orders.iloc[:i+1]
                
                # Size consistency (40%)
                size_consistency = self._calculate_size_consistency(history)
                
                # Return rate (30%)
                return_rate = self._calculate_return_rate(history)
                
                # Purchase frequency (30%)
                frequency_score = self._calculate_frequency_score(history)
                
                # Weighted confidence score
                confidence = (
                    0.4 * size_consistency +
                    0.3 * (1 - return_rate) +
                    0.3 * frequency_score
                )
                
                scores.append(min(max(confidence, 0), 1))  # Clamp between 0 and 1
            
            confidence_scores[customer_id] = scores
        
        return confidence_scores
    
    def _calculate_size_consistency(self, history: pd.DataFrame) -> float:
        """Calculate size consistency score."""
        if len(history) <= 1:
            return 0.5  # Neutral score for single purchase
            
        sizes = history['size'].value_counts()
        return float(sizes.iloc[0]) / len(history)
    
    def _calculate_return_rate(self, history: pd.DataFrame) -> float:
        """Calculate return rate."""
        if len(history) == 0:
            return 0.0
        return history['is_return'].mean()
    
    def _calculate_frequency_score(self, history: pd.DataFrame) -> float:
        """Calculate purchase frequency score."""
        if len(history) <= 1:
            return 0.5  # Neutral score for single purchase
            
        # Calculate average days between purchases
        dates = history['order_date'].sort_values()
        days_between = (dates.diff().mean().days)
        
        # Convert to score (30 days = 1.0, 365 days = 0.0)
        return max(0, min(1, (365 - days_between) / (365 - 30)))
        
    def analyze_category_flow(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        Analyzes category transition patterns.
        
        Methodology:
        1. Map product IDs to categories
        2. Create sequence of category transitions
        3. Calculate transition probabilities
        4. Filter significant patterns
        
        Returns:
            Dict[from_category, List[(to_category, probability)]]
        """
        # Create product to category mapping
        product_categories = dict(zip(self.products['product_id'], 
                                    self.products['category']))
        
        # Initialize transition counts
        transitions = {}
        
        # Analyze transitions for each customer
        for customer_id in self.orders['customer_id'].unique():
            customer_orders = self.orders[
                self.orders['customer_id'] == customer_id
            ].sort_values('order_date')
            
            # Map to categories
            categories = [product_categories[pid] 
                         for pid in customer_orders['product_id']]
            
            # Count transitions
            for i in range(len(categories)-1):
                from_cat = categories[i]
                to_cat = categories[i+1]
                
                if from_cat not in transitions:
                    transitions[from_cat] = {}
                
                if to_cat not in transitions[from_cat]:
                    transitions[from_cat][to_cat] = 0
                    
                transitions[from_cat][to_cat] += 1
        
        # Calculate probabilities
        flow_patterns = {}
        for from_cat, to_cats in transitions.items():
            total = sum(to_cats.values())
            
            # Convert to probability and filter significant patterns
            significant_transitions = [
                (to_cat, count/total)
                for to_cat, count in to_cats.items()
                if count/total >= 0.1  # Filter transitions occurring >10% of time
            ]
            
            if significant_transitions:
                flow_patterns[from_cat] = sorted(
                    significant_transitions,
                    key=lambda x: x[1],
                    reverse=True
                )
        
        return flow_patterns
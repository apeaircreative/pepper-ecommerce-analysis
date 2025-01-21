"""
Journey Mapping Module

This module implements customer journey analysis focusing on
post-purchase behavior and confidence development.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class JourneyStage(Enum):
    """Customer journey stages in their size confidence development."""
    FIRST_PURCHASE = "First Purchase"
    SIZE_EXPLORATION = "Size Exploration"
    STYLE_EXPLORATION = "Style Exploration"
    CONFIDENCE_BUILDING = "Confidence Building"
    BRAND_LOYAL = "Brand Loyal"

class JourneyMapper:
    """Maps customer journey patterns and confidence development."""
    
    # Stage transition thresholds
    STYLE_THRESHOLD = 2  # Number of different styles tried
    CONFIDENCE_THRESHOLD = 0.7  # Confidence score to reach confidence building
    LOYALTY_THRESHOLD = 5  # Number of successful purchases for loyalty
    
    def __init__(self, orders: pd.DataFrame, products: pd.DataFrame):
        """
        Initialize with order and product data.
        
        Args:
            orders: DataFrame with order history
            products: DataFrame with product details
        
        Raises:
            ValueError: If orders or products are not DataFrames
        """
        if not isinstance(orders, pd.DataFrame) or not isinstance(products, pd.DataFrame):
            raise ValueError("Orders and products must be DataFrames")
        
        self.orders = orders.copy()
        self.products = products.copy()
        self.journeys = {}
        self.patterns = {}
        self._prepare_data()
        
    def _prepare_data(self):
        """
        Prepare data for analysis.
        
        This method extracts size information from SKUs, adds size columns to products,
        merges orders with products, and converts dates.
        
        Raises:
            Exception: If an error occurs during data preparation
        """
        logger.debug("Starting data preparation")
        
        # Extract size information from SKU
        def extract_size_info(sku):
            """
            Extract size components from SKU (e.g., BRA001BL34AA -> 34, AA)
            
            Args:
                sku: SKU string
            
            Returns:
                Tuple of (band_size, cup_size) or (None, None) if not a string
            """
            if not isinstance(sku, str):
                return None, None
            match = re.search(r'(\d{2})([A-Z]+)$', sku)
            if match:
                return match.group(1), match.group(2)
            return None, None
            
        try:
            # Add size columns to products
            self.products['band_size'], self.products['cup_size'] = zip(
                *self.products['sku'].apply(extract_size_info)
            )
            self.products['size'] = self.products.apply(
                lambda x: f"{x['band_size']}{x['cup_size']}" if x['band_size'] and x['cup_size'] else None,
                axis=1
            )
            
            # Add style column (use product name without color)
            self.products['style'] = self.products['name'].str.extract(r'(.*?)(?:\s*-\s*[A-Za-z]+)?$')[0]
            
            # Merge orders with products
            self.orders = pd.merge(
                self.orders,
                self.products[['product_id', 'name', 'size', 'band_size', 'cup_size', 'category', 'style']],
                on='product_id',
                how='left',
                suffixes=('', '_product')
            )
            
            # Convert dates
            self.orders['created_at'] = pd.to_datetime(self.orders['created_at'])
            
            logger.debug("Data preparation complete")
            logger.debug(f"Orders columns: {self.orders.columns}")
            logger.debug(f"Products columns: {self.products.columns}")
        except Exception as e:
            logger.error(f"Error during data preparation: {str(e)}")
            raise

    def determine_journey_stage(self, customer_id: str) -> Tuple[JourneyStage, float]:
        """
        Determine customer's current journey stage.
        
        Args:
            customer_id: Unique customer identifier
        
        Returns:
            Tuple of (JourneyStage, confidence_score)
        
        Raises:
            ValueError: If customer_id is not a string
        """
        if not isinstance(customer_id, str):
            raise ValueError("Customer ID must be a string")
        
        logger.debug(f"Determining journey stage for customer {customer_id}")
        
        # Get customer's purchase history
        customer_orders = self.orders[
            self.orders['customer_id'] == customer_id
        ].sort_values('created_at')
        
        if len(customer_orders) == 0:
            logger.debug("No orders found")
            return JourneyStage.FIRST_PURCHASE, 0.0
            
        # Calculate confidence score
        confidence = self._calculate_confidence_score(customer_orders)
        logger.debug(f"Confidence score: {confidence}")
        
        # Count completed and returned orders
        completed_orders = customer_orders[~customer_orders['returned']]
        returned_orders = customer_orders[customer_orders['returned']]
        completed_count = len(completed_orders)
        returned_count = len(returned_orders)
        
        # Handle initial stages
        if completed_count == 0:
            logger.debug("All orders returned")
            return JourneyStage.SIZE_EXPLORATION, 0.0
        elif completed_count == 1 and returned_count == 0:
            logger.debug("Single completed order, no returns")
            return JourneyStage.FIRST_PURCHASE, confidence
            
        # Check for style exploration first if customer has multiple completed orders
        if completed_count >= 2:
            unique_styles = completed_orders['style'].nunique()
            logger.debug(f"Unique styles: {unique_styles}")
            if unique_styles >= self.STYLE_THRESHOLD:
                logger.debug("Multiple styles -> Style Exploration")
                return JourneyStage.STYLE_EXPLORATION, confidence
            
        # Check for size exploration
        if returned_count > 0:
            logger.debug("Has returns -> Size Exploration")
            return JourneyStage.SIZE_EXPLORATION, confidence
            
        # Check for brand loyalty
        if completed_count >= self.LOYALTY_THRESHOLD and confidence > self.CONFIDENCE_THRESHOLD:
            logger.debug("Many orders with high confidence -> Brand Loyal")
            return JourneyStage.BRAND_LOYAL, confidence
            
        # Default to confidence building if confidence is high
        if confidence > self.CONFIDENCE_THRESHOLD:
            logger.debug("High confidence -> Confidence Building")
            return JourneyStage.CONFIDENCE_BUILDING, confidence
            
        logger.debug("Default to Size Exploration")
        return JourneyStage.SIZE_EXPLORATION, confidence

    def _calculate_confidence_score(self, customer_orders: pd.DataFrame) -> float:
        """
        Calculate customer's confidence score based on purchase history.
        
        Args:
            customer_orders: DataFrame of customer's orders
        
        Returns:
            Confidence score between 0 and 1
        
        Raises:
            ValueError: If customer_orders is not a DataFrame
        """
        if not isinstance(customer_orders, pd.DataFrame):
            raise ValueError("Customer orders must be a DataFrame")
        
        if len(customer_orders) == 0:
            return 0.0
            
        # Only consider completed orders for confidence
        completed_orders = customer_orders[~customer_orders['returned']]
        if len(completed_orders) == 0:
            return 0.0
            
        # Calculate size consistency (40%)
        band_consistency = completed_orders['band_size'].nunique() == 1
        cup_consistency = completed_orders['cup_size'].nunique() == 1
        size_consistency = (band_consistency and cup_consistency)
        
        # Calculate return rate (30%)
        return_rate = customer_orders['returned'].mean()
        
        # Calculate purchase frequency score (30%)
        date_range = (customer_orders['created_at'].max() - customer_orders['created_at'].min()).days
        frequency_score = min(1.0, len(completed_orders) / (date_range / 30 + 1))  # Orders per month
        
        # Weight factors
        weights = {
            'consistency': 0.4,
            'returns': 0.3,
            'frequency': 0.3
        }
        
        # Calculate weighted score
        score = (
            size_consistency * weights['consistency'] +
            (1 - return_rate) * weights['returns'] +
            frequency_score * weights['frequency']
        )
        
        return min(max(score, 0.0), 1.0)

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
        
        Raises:
            Exception: If an error occurs during confidence progression mapping
        """
        logger.debug("Starting confidence progression mapping")
        confidence_scores = {}
        
        try:
            for customer_id in self.orders['customer_id'].unique():
                # Get customer's purchase history
                customer_orders = self.orders[
                    self.orders['customer_id'] == customer_id
                ].sort_values('created_at')
                
                # Calculate running confidence scores
                scores = []
                for i in range(len(customer_orders)):
                    history = customer_orders.iloc[:i+1]
                    score = self._calculate_confidence_score(history)
                    scores.append(score)
                
                confidence_scores[customer_id] = scores
                logger.debug(f"Customer {customer_id} scores: {scores}")
        except Exception as e:
            logger.error(f"Error during confidence progression mapping: {str(e)}")
            raise
        
        return confidence_scores

    def identify_entry_points(self) -> Dict[str, float]:
        """
        Returns distribution of entry points.
        
        Methodology:
        1. Group orders by customer
        2. Identify first purchase for each customer
        3. Calculate product frequency distribution
        4. Filter for significant patterns
        
        Returns:
            Dict[style_name, frequency_ratio]
        
        Raises:
            Exception: If an error occurs during entry point identification
        """
        logger.debug("Starting entry point identification")
        
        try:
            # Get first purchase for each customer (exclude returns)
            first_purchases = (
                self.orders[~self.orders['returned']]
                .sort_values('created_at')
                .groupby('customer_id')
                .first()
                .reset_index()
            )
            
            logger.debug(f"Found {len(first_purchases)} first purchases")
            logger.debug(f"First purchases columns: {first_purchases.columns}")
            logger.debug(f"First purchases data:\n{first_purchases[['customer_id', 'name', 'product_id']]}")
            
            # Calculate frequency distribution of product names
            name_counts = first_purchases['name'].value_counts()
            total_customers = len(first_purchases)
            
            # Convert to frequency ratios
            entry_points = {
                name: count / total_customers
                for name, count in name_counts.items()
            }
            
            logger.debug(f"Entry points identified: {entry_points}")
        except Exception as e:
            logger.error(f"Error during entry point identification: {str(e)}")
            raise
        
        return entry_points

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
        
        Raises:
            Exception: If an error occurs during category flow analysis
        """
        try:
            # Create product to category mapping
            product_categories = dict(zip(self.products['product_id'], 
                                        self.products['category']))
            
            # Initialize transition counts
            transitions = {}
            
            # Analyze transitions for each customer
            for customer_id in self.orders['customer_id'].unique():
                customer_orders = self.orders[
                    self.orders['customer_id'] == customer_id
                ].sort_values('created_at')
                
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
        except Exception as e:
            logger.error(f"Error during category flow analysis: {str(e)}")
            raise
        
        return flow_patterns

    def analyze_journey_patterns(self) -> Dict[str, Dict[str, float]]:
        """Analyze customer journeys to identify common paths and transitions.
        
        Returns:
            A dictionary where keys are customer IDs and values are dictionaries of
            transition probabilities between journey stages.
        """
        logger.debug("Starting journey pattern analysis")
        transition_counts = {}
        
        for customer_id in self.orders['customer_id'].unique():
            customer_orders = self.orders[self.orders['customer_id'] == customer_id]
            stages = customer_orders['journey_stage'].tolist()
            
            for i in range(len(stages) - 1):
                from_stage = stages[i]
                to_stage = stages[i + 1]
                
                if from_stage not in transition_counts:
                    transition_counts[from_stage] = {}
                
                if to_stage not in transition_counts[from_stage]:
                    transition_counts[from_stage][to_stage] = 0
                
                transition_counts[from_stage][to_stage] += 1
        
        # Convert counts to probabilities
        transition_probabilities = {}
        for from_stage, to_stages in transition_counts.items():
            total = sum(to_stages.values())
            transition_probabilities[from_stage] = {
                to_stage: count / total for to_stage, count in to_stages.items()
            }
        
        logger.debug(f"Transition probabilities: {transition_probabilities}")
        return transition_probabilities

    def predict_confidence(self, customer_orders: pd.DataFrame) -> float:
        """Predict future confidence score based on historical purchase data.
        
        Args:
            customer_orders: DataFrame of customer's orders
        
        Returns:
            Predicted confidence score between 0 and 1
        """
        logger.debug("Predicting confidence based on historical data")
        if len(customer_orders) == 0:
            return 0.0
        
        # Calculate average confidence score from past orders
        scores = []
        for index, order in customer_orders.iterrows():
            score = self._calculate_confidence_score(customer_orders.iloc[:index + 1])
            scores.append(score)
        
        predicted_score = sum(scores) / len(scores)
        logger.debug(f"Predicted confidence score: {predicted_score}")
        return min(max(predicted_score, 0.0), 1.0)
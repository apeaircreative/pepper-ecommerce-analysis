"""
Data Loading Module for Pepper Analysis

Handles loading and preprocessing of Pepper's Shopify data.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

def validate_columns(df: pd.DataFrame, required_cols: list, context: str) -> None:
    """
    Validate that required columns exist in DataFrame.
    
    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        context: Context for error message (e.g., 'Orders' or 'Products')
        
    Raises:
        ValueError: If required columns are missing
    """
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {context} data: {missing_cols}"
        )

def load_pepper_data(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and preprocess Pepper's order and product data.
    Args:
        data_dir: Directory containing the data files
        
    Returns:
        Tuple of (orders_df, products_df)
        
    Raises:
        ValueError: If required columns are missing or data format is invalid
        FileNotFoundError: If data files are not found
    """
    try:
        # Find most recent data files
        orders_file = sorted(
            Path(data_dir).glob("simulated_orders_*.csv")
        )[-1]
        
        order_items_file = sorted(
            Path(data_dir).glob("transformed_order_items_*.csv")
        )[-1]
        
        products_file = sorted(
            Path(data_dir).glob("transformed_bra_products_*.csv")
        )[-1]
        
        # Load data
        orders_df = pd.read_csv(orders_file)
        order_items_df = pd.read_csv(order_items_file)
        products_df = pd.read_csv(products_file)
        
        # Convert dates in order_items
        date_columns = ['created_at', 'shipped_at', 'delivered_at', 'returned_at']
        for col in date_columns:
            if col in order_items_df.columns:
                order_items_df[col] = pd.to_datetime(order_items_df[col])
        
        # Add is_return based on returned_at date
        order_items_df['is_return'] = ~order_items_df['returned_at'].isna()
        
        # Join orders with order items
        orders_df = orders_df.merge(
            order_items_df[['order_id', 'product_id', 'is_return', 'returned_at']],
            left_on='id',
            right_on='order_id',
            how='left'
        )
        
        # Map columns to expected names
        order_column_map = {
            'user_id': 'customer_id',
            'order_date': 'created_at'
        }
        
        product_column_map = {
            'id': 'product_id'
        }
        
        # Rename columns if they exist
        for old_col, new_col in order_column_map.items():
            if old_col in orders_df.columns and new_col not in orders_df.columns:
                orders_df = orders_df.rename(columns={old_col: new_col})
                
        for old_col, new_col in product_column_map.items():
            if old_col in products_df.columns and new_col not in products_df.columns:
                products_df = products_df.rename(columns={old_col: new_col})
        
        # Define required columns
        required_order_cols = [
            'id', 'customer_id', 'status', 'created_at', 'product_id'
        ]
        required_product_cols = [
            'product_id', 'name', 'sku', 'retail_price'
        ]
        
        # Validate columns
        validate_columns(orders_df, required_order_cols, "Orders")
        validate_columns(products_df, required_product_cols, "Products")
        
        # Basic data cleaning
        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
        orders_df['status'] = orders_df['status'].str.lower()
        
        return orders_df, products_df
        
    except IndexError:
        raise FileNotFoundError(
            f"No data files found in {data_dir}. "
            "Expected files matching patterns: "
            "'simulated_orders_*.csv', 'transformed_order_items_*.csv', "
            "and 'transformed_bra_products_*.csv'"
        )
"""
Collect product data from Pepper's Shopify store.
"""
import os
import yaml
import pandas as pd
from datetime import datetime
from typing import Optional

import sys
sys.path.append('../..')  # Add parent directory to path
from utils.shopify_utils import ShopifyAPI

def load_config(config_path: str = '../config/urls.yaml') -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def collect_products(output_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Collect product data from Pepper's Shopify store.
    
    Args:
        output_dir: Optional directory to save data
        
    Returns:
        DataFrame with product data
    """
    # Load configuration
    config = load_config()
    shopify_config = config['shopify']
    
    # Initialize API client
    client = ShopifyAPI(
        base_url=shopify_config['base_url'],
        rate_limit=config['rate_limits']['shopify']['requests_per_minute']
    )
    
    # Collect products
    products = client.get_all_products(
        max_pages=config['collection']['max_pages']
    )
    
    # Convert to DataFrame
    df = client.products_to_df(products)
    
    # Save if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pepper_products_{timestamp}.csv'
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f'Saved product data to {filepath}')
    
    return df

if __name__ == '__main__':
    # If run directly, save to data/external/pepper
    output_dir = '../../data/external/pepper'
    collect_products(output_dir)

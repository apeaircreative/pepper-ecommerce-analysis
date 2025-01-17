"""
Collect product data from Pepper's Amazon store.
"""
import os
import yaml
import pandas as pd
from datetime import datetime
from typing import Optional

import sys
sys.path.append('../..')
from utils.amazon_utils import AmazonScraper

def load_config(config_path: str = '../config/urls.yaml') -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def collect_amazon_products(output_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Collect Pepper product data from Amazon.
    
    Args:
        output_dir: Optional directory to save data
        
    Returns:
        DataFrame with product data
    """
    # Load configuration
    config = load_config()
    amazon_config = config['amazon']
    
    # Initialize scraper
    scraper = AmazonScraper(
        headers={'User-Agent': config['collection']['headers']['user_agent']},
        rate_limit=config['rate_limits']['amazon']['requests_per_minute']
    )
    
    # Collect products from all search URLs
    all_products = []
    for search_url in amazon_config['search_urls']:
        products = scraper.search_products(
            search_url=search_url,
            max_pages=config['collection']['max_pages']
        )
        all_products.extend(products)
    
    # Convert to DataFrame
    df = scraper.to_dataframe(all_products)
    
    # Remove duplicates by ASIN
    df = df.drop_duplicates(subset=['asin'])
    
    # Save if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pepper_amazon_{timestamp}.csv'
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f'Saved Amazon data to {filepath}')
    
    return df

if __name__ == '__main__':
    # If run directly, save to data/external/pepper
    output_dir = '../../data/external/pepper'
    collect_amazon_products(output_dir)

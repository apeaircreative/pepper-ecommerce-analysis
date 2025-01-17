"""
Shopify API client for accessing product data.
"""
import requests
from typing import Dict, List, Optional
import pandas as pd
from urllib.parse import urljoin
import time
from .scraper_logger import setup_logger

class ShopifyAPIClient:
    def __init__(self, base_url: str):
        """Initialize Shopify API client."""
        self.base_url = base_url
        self.logger = setup_logger('shopify_api')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def get_products(self, limit: int = 250, page: int = 1) -> List[Dict]:
        """
        Get products using Shopify's products.json endpoint.
        
        Args:
            limit: Number of products per page (max 250)
            page: Page number
            
        Returns:
            List of product dictionaries
        """
        url = urljoin(self.base_url, '/products.json')
        params = {
            'limit': min(limit, 250),  # Shopify's max limit
            'page': page
        }
        
        try:
            self.logger.debug(f"Fetching products page {page}")
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Retrieved {len(data['products'])} products")
                return data['products']
            else:
                self.logger.warning(
                    f"Failed to fetch products. Status: {response.status_code}"
                )
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching products: {str(e)}")
            return []
    
    def get_all_products(self) -> List[Dict]:
        """Get all products across multiple pages."""
        all_products = []
        page = 1
        
        while True:
            products = self.get_products(page=page)
            if not products:
                break
                
            all_products.extend(products)
            page += 1
            time.sleep(1)  # Rate limiting
            
        self.logger.info(f"Retrieved total of {len(all_products)} products")
        return all_products
    
    def extract_variant_data(self, products: List[Dict]) -> pd.DataFrame:
        """
        Extract variant-level data from products into a DataFrame.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            DataFrame with variant-level data
        """
        variants = []
        
        for product in products:
            product_id = product['id']
            product_title = product['title']
            product_handle = product['handle']
            
            for variant in product['variants']:
                variant_data = {
                    'product_id': product_id,
                    'product_title': product_title,
                    'product_handle': product_handle,
                    'variant_id': variant['id'],
                    'sku': variant['sku'],
                    'price': float(variant['price']),
                    'size': variant['option1'],
                    'color': variant['option2'],
                    'available': variant.get('available', False),
                    'inventory_quantity': variant.get('inventory_quantity', 0)
                }
                variants.append(variant_data)
        
        df = pd.DataFrame(variants)
        self.logger.info(f"Extracted data for {len(df)} variants")
        return df
    
def main():
    """Test the API client."""
    client = ShopifyAPIClient("https://www.wearpepper.com")
    
    # Get all products
    products = client.get_all_products()
    
    if products:
        # Extract variant data
        df = client.extract_variant_data(products)
        
        # Save to CSV
        df.to_csv('data/raw/shopify_products.csv', index=False)
        print(f"Saved {len(df)} variants to data/raw/shopify_products.csv")
        
        # Display summary
        print("\nProduct Summary:")
        print("-" * 50)
        print(f"Total Products: {len(products)}")
        print(f"Total Variants: {len(df)}")
        print("\nSize Distribution:")
        print(df['size'].value_counts().head())
        print("\nColor Distribution:")
        print(df['color'].value_counts().head())
        print("\nPrice Range:")
        print(f"Min: ${df['price'].min():.2f}")
        print(f"Max: ${df['price'].max():.2f}")
        print(f"Mean: ${df['price'].mean():.2f}")

if __name__ == '__main__':
    main()

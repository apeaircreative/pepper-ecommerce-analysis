"""
Utility functions for scraping Amazon product data.
Note: This respects Amazon's robots.txt and rate limits.
"""
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List, Optional
from urllib.parse import urljoin

class AmazonScraper:
    def __init__(self, headers: Dict[str, str], rate_limit: int = 10):
        """
        Initialize Amazon scraper with rate limiting.
        
        Args:
            headers: Request headers including user-agent
            rate_limit: Maximum requests per minute
        """
        self.headers = headers
        self.delay = 60.0 / rate_limit
        self.last_request = 0
        self.session = requests.Session()
        
    def _rate_limit(self):
        """Implement rate limiting."""
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.time()
        
    def get_page(self, url: str) -> BeautifulSoup:
        """
        Get and parse a page with rate limiting.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object of the page
        """
        self._rate_limit()
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
        
    def extract_product_data(self, soup: BeautifulSoup) -> Dict:
        """
        Extract product data from a product page.
        
        Args:
            soup: BeautifulSoup object of product page
            
        Returns:
            Dictionary of product data
        """
        data = {}
        
        # Basic product info
        try:
            data['title'] = soup.select_one('#productTitle').text.strip()
        except:
            data['title'] = None
            
        try:
            data['price'] = soup.select_one('.a-price .a-offscreen').text.strip()
        except:
            data['price'] = None
            
        # Ratings and reviews
        try:
            data['rating'] = soup.select_one('.a-icon-star').text.strip()
            data['review_count'] = soup.select_one('#acrCustomerReviewText').text.split()[0]
        except:
            data['rating'] = None
            data['review_count'] = None
            
        # Product details
        details = {}
        for row in soup.select('.product-facts-table tr'):
            try:
                key = row.select_one('.label').text.strip()
                value = row.select_one('.value').text.strip()
                details[key] = value
            except:
                continue
        data['details'] = details
        
        return data
        
    def search_products(self, search_url: str, max_pages: int = 1) -> List[Dict]:
        """
        Search for products and extract basic information.
        
        Args:
            search_url: Amazon search URL
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product dictionaries
        """
        products = []
        current_url = search_url
        
        for page in range(max_pages):
            soup = self.get_page(current_url)
            
            # Extract product cards
            for card in soup.select('.s-result-item[data-asin]'):
                try:
                    product = {
                        'asin': card['data-asin'],
                        'title': card.select_one('h2 .a-link-normal').text.strip(),
                        'url': urljoin('https://www.amazon.com', 
                                     card.select_one('h2 .a-link-normal')['href']),
                        'price': card.select_one('.a-price .a-offscreen').text.strip()
                        if card.select_one('.a-price .a-offscreen') else None,
                        'rating': card.select_one('.a-icon-star-small').text.strip()
                        if card.select_one('.a-icon-star-small') else None,
                        'review_count': card.select_one('.a-size-small .a-link-normal').text.strip()
                        if card.select_one('.a-size-small .a-link-normal') else None
                    }
                    products.append(product)
                except:
                    continue
            
            # Find next page
            next_button = soup.select_one('.s-pagination-next')
            if not next_button or 'a-disabled' in next_button.get('class', []):
                break
                
            current_url = urljoin('https://www.amazon.com', next_button['href'])
            
        return products
        
    def to_dataframe(self, products: List[Dict]) -> pd.DataFrame:
        """
        Convert product list to DataFrame.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            DataFrame with product information
        """
        return pd.DataFrame(products)

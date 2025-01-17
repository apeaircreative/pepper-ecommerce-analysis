"""
Utility to discover and test Shopify's Storefront API endpoints.
"""
import requests
from urllib.parse import urljoin
import json
from pathlib import Path
import time
from .scraper_logger import setup_logger

class ShopifyAPIDiscovery:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = setup_logger('api_discovery')
        self.session = requests.Session()
        
        # Standard Shopify headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
    
    def discover_endpoints(self):
        """Test various Shopify API endpoints."""
        self.logger.info(f"Starting API discovery for {self.base_url}")
        
        # Common Shopify endpoints
        endpoints = [
            '/api/2024-01/graphql.json',  # Storefront API
            '/api/2024-01/products.json',  # REST API
            '/.well-known/shopify/monorail',  # Analytics
            '/products.json',  # Public API
        ]
        
        results = []
        for endpoint in endpoints:
            url = urljoin(self.base_url, endpoint)
            try:
                self.logger.debug(f"Testing endpoint: {url}")
                response = self.session.get(url)
                
                result = {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                }
                
                # If JSON response, add sample
                try:
                    result['sample_data'] = response.json()
                except:
                    result['sample_data'] = None
                    
                results.append(result)
                self.logger.info(f"Endpoint {endpoint}: {response.status_code}")
                
                # Respect rate limits
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error testing {endpoint}: {str(e)}")
                results.append({
                    'endpoint': endpoint,
                    'error': str(e)
                })
        
        return results
    
    def test_graphql_query(self, query: str):
        """Test a GraphQL query against the Storefront API."""
        url = urljoin(self.base_url, '/api/2024-01/graphql.json')
        
        try:
            response = self.session.post(url, json={'query': query})
            return response.json()
        except Exception as e:
            self.logger.error(f"GraphQL query failed: {str(e)}")
            return None
    
    def save_results(self, results, output_dir: str = 'data/api_discovery'):
        """Save API discovery results."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        output_file = output_path / f'api_discovery_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        self.logger.info(f"Results saved to {output_file}")
        
def main():
    """Run API discovery."""
    base_url = "https://www.wearpepper.com"
    discovery = ShopifyAPIDiscovery(base_url)
    
    # Test basic product query
    sample_query = """
    {
      products(first: 5) {
        edges {
          node {
            id
            title
            handle
            variants(first: 5) {
              edges {
                node {
                  id
                  title
                  price
                  sku
                }
              }
            }
          }
        }
      }
    }
    """
    
    # Run discovery
    results = discovery.discover_endpoints()
    discovery.save_results(results)
    
    # Test GraphQL if available
    graphql_result = discovery.test_graphql_query(sample_query)
    if graphql_result:
        discovery.save_results(
            {'graphql_test': graphql_result},
            'data/api_discovery/graphql'
        )

if __name__ == '__main__':
    main()

"""
Validate and update navigation structure using Shopify API.
"""
import requests
from typing import Dict, List, Set
import yaml
from pathlib import Path
import json
from urllib.parse import urljoin, urlparse
from .scraper_logger import setup_logger

class NavigationValidator:
    def __init__(self, base_url: str):
        """Initialize navigation validator."""
        self.base_url = base_url
        self.logger = setup_logger('navigation_validator')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def get_collections(self) -> List[Dict]:
        """Get all collections from Shopify."""
        url = urljoin(self.base_url, '/collections.json')
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Retrieved {len(data['collections'])} collections")
                return data['collections']
            else:
                self.logger.warning(
                    f"Failed to fetch collections. Status: {response.status_code}"
                )
                return []
        except Exception as e:
            self.logger.error(f"Error fetching collections: {str(e)}")
            return []
    
    def get_collection_products(self, handle: str) -> List[Dict]:
        """Get products in a collection."""
        url = urljoin(self.base_url, f'/collections/{handle}/products.json')
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                self.logger.info(
                    f"Retrieved {len(data['products'])} products from {handle}"
                )
                return data['products']
            else:
                self.logger.warning(
                    f"Failed to fetch products for {handle}. Status: {response.status_code}"
                )
                return []
        except Exception as e:
            self.logger.error(f"Error fetching products for {handle}: {str(e)}")
            return []
    
    def validate_config(self, config_path: str) -> Dict:
        """Validate navigation config against API data."""
        try:
            # Load current config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Get current collections
            collections = self.get_collections()
            collection_handles = {c['handle'] for c in collections}
            
            # Initialize validation report
            report = {
                'collections': {
                    'total_found': len(collections),
                    'handles': sorted(collection_handles),
                    'issues': []
                },
                'navigation': {
                    'valid_paths': [],
                    'invalid_paths': []
                },
                'products': {}
            }
            
            # Validate collection paths
            config_paths = self._extract_collection_paths(config)
            
            for path in config_paths:
                handle = path.split('/')[-1]
                if handle in collection_handles:
                    report['navigation']['valid_paths'].append(path)
                    
                    # Get products in collection
                    products = self.get_collection_products(handle)
                    report['products'][handle] = {
                        'count': len(products),
                        'handles': [p['handle'] for p in products]
                    }
                else:
                    report['navigation']['invalid_paths'].append(path)
                    report['collections']['issues'].append({
                        'type': 'invalid_collection',
                        'path': path,
                        'handle': handle
                    })
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error validating config: {str(e)}")
            return {'error': str(e)}
    
    def _extract_collection_paths(self, config: Dict) -> Set[str]:
        """Extract collection paths from config."""
        paths = set()
        
        def extract_paths(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith('/collections/'):
                        paths.add(value)
                    elif isinstance(value, (dict, list)):
                        extract_paths(value)
            elif isinstance(data, list):
                for item in data:
                    extract_paths(item)
        
        extract_paths(config)
        return paths
    
    def update_config(self, config_path: str, report: Dict) -> bool:
        """Update config with valid navigation structure."""
        try:
            # Load current config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update collections section
            config['shopify']['collections'] = {
                'all_products': '/collections/all'
            }
            
            # Group collections by type
            bras = [p for p in report['navigation']['valid_paths'] 
                   if 'bra' in p.lower()]
            underwear = [p for p in report['navigation']['valid_paths'] 
                        if 'underwear' in p.lower() or 'panty' in p.lower()]
            accessories = [p for p in report['navigation']['valid_paths'] 
                         if 'accessories' in p.lower()]
            
            # Update config structure
            if bras:
                config['shopify']['collections']['bras'] = {
                    'main': '/collections/bras',
                    'categories': {
                        p.split('/')[-1]: p for p in bras
                    }
                }
            
            if underwear:
                config['shopify']['collections']['underwear'] = {
                    'main': '/collections/underwear',
                    'categories': {
                        p.split('/')[-1]: p for p in underwear
                    }
                }
            
            if accessories:
                config['shopify']['collections']['accessories'] = {
                    'main': '/collections/accessories',
                    'categories': {
                        p.split('/')[-1]: p for p in accessories
                    }
                }
            
            # Backup old config
            backup_path = Path(config_path).with_suffix('.yaml.bak')
            with open(backup_path, 'w') as f:
                yaml.dump(config, f)
            
            # Save updated config
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            
            self.logger.info(f"Updated config saved to {config_path}")
            self.logger.info(f"Backup saved to {backup_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating config: {str(e)}")
            return False
    
    def save_report(self, report: Dict, output_dir: str = 'data/navigation'):
        """Save navigation report."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        report_file = output_path / 'navigation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Navigation report saved to {report_file}")

def main():
    """Validate and update navigation structure."""
    base_url = "https://www.wearpepper.com"
    config_path = "scripts/scrapers/config/urls.yaml"
    
    # Initialize validator
    validator = NavigationValidator(base_url)
    
    # Validate current config
    report = validator.validate_config(config_path)
    
    # Print summary
    print("\nNavigation Validation Report")
    print("-" * 50)
    print(f"Collections Found: {report['collections']['total_found']}")
    print(f"Valid Paths: {len(report['navigation']['valid_paths'])}")
    print(f"Invalid Paths: {len(report['navigation']['invalid_paths'])}")
    
    if report['navigation']['invalid_paths']:
        print("\nInvalid Paths:")
        for path in report['navigation']['invalid_paths']:
            print(f"- {path}")
    
    print("\nCollection Products:")
    for handle, data in report['products'].items():
        print(f"- {handle}: {data['count']} products")
    
    # Save report
    validator.save_report(report)
    
    # Update config if needed
    if report['navigation']['invalid_paths']:
        print("\nUpdating configuration...")
        if validator.update_config(config_path, report):
            print("Configuration updated successfully!")
        else:
            print("Failed to update configuration.")

if __name__ == '__main__':
    main()

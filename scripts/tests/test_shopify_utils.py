"""
Tests for Shopify utilities.
"""
import pytest
from unittest.mock import Mock, patch
from scripts.utils.shopify_utils import ShopifyScraper
import yaml

@pytest.fixture
def mock_config(tmp_path):
    """Create mock config file."""
    config = {
        'shopify': {
            'base_url': 'https://www.wearpepper.com',
            'rate_limit': 30,
            'collections': {
                'all_products': '/collections/all'
            }
        }
    }
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    return str(config_file)

def test_shopify_scraper_initialization(mock_config):
    """Test ShopifyScraper initialization."""
    scraper = ShopifyScraper(mock_config)
    assert scraper.logger is not None
    assert 'https://www.wearpepper.com' in scraper.config['shopify']['base_url']

@patch('requests.get')
def test_get_products(mock_get, mock_config):
    """Test product retrieval."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '''
    <div class="product-card">
        <h2>Test Product</h2>
        <span class="price">$60.00</span>
        <div class="variant" data-sku="TEST-001"></div>
    </div>
    '''
    mock_get.return_value = mock_response
    
    scraper = ShopifyScraper(mock_config)
    products = scraper.get_products()
    assert len(products) > 0

@patch('requests.get')
def test_get_collections(mock_get, mock_config):
    """Test collections retrieval."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '''
    <div class="collection-list">
        <a href="/collections/test">Test Collection</a>
    </div>
    '''
    mock_get.return_value = mock_response
    
    scraper = ShopifyScraper(mock_config)
    collections = scraper.get_collections()
    assert len(collections) > 0

"""
Tests for navigation validator.
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import yaml
import json
from scripts.utils.navigation_validator import NavigationValidator

@pytest.fixture
def mock_collections_response():
    """Mock collections API response."""
    return {
        'collections': [
            {'handle': 'bras', 'title': 'All Bras'},
            {'handle': 'underwear', 'title': 'Underwear'},
            {'handle': 'accessories', 'title': 'Accessories'}
        ]
    }

@pytest.fixture
def mock_products_response():
    """Mock products API response."""
    return {
        'products': [
            {
                'handle': 'classic-bra',
                'title': 'Classic Bra',
                'variants': [
                    {'sku': 'BRA001-30A-BLK', 'price': '60.00'},
                    {'sku': 'BRA001-32A-BLK', 'price': '60.00'}
                ]
            }
        ]
    }

@pytest.fixture
def sample_config():
    """Sample navigation config."""
    return {
        'shopify': {
            'collections': {
                'all_products': '/collections/all',
                'bras': {
                    'main': '/collections/bras',
                    'categories': {
                        'underwire': '/collections/underwire-bras',
                        'wireless': '/collections/wireless-bras'
                    }
                }
            }
        }
    }

def test_init():
    """Test validator initialization."""
    validator = NavigationValidator('https://test.com')
    assert validator.base_url == 'https://test.com'
    assert validator.logger is not None

@patch('requests.Session.get')
def test_get_collections(mock_get, mock_collections_response):
    """Test collections retrieval."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_collections_response
    
    validator = NavigationValidator('https://test.com')
    collections = validator.get_collections()
    
    assert len(collections) == 3
    assert collections[0]['handle'] == 'bras'

@patch('requests.Session.get')
def test_get_collection_products(mock_get, mock_products_response):
    """Test collection products retrieval."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_products_response
    
    validator = NavigationValidator('https://test.com')
    products = validator.get_collection_products('bras')
    
    assert len(products) == 1
    assert products[0]['handle'] == 'classic-bra'

def test_extract_collection_paths(sample_config):
    """Test path extraction from config."""
    validator = NavigationValidator('https://test.com')
    paths = validator._extract_collection_paths(sample_config)
    
    # We expect 4 paths:
    # 1. /collections/all
    # 2. /collections/bras
    # 3. /collections/underwire-bras
    # 4. /collections/wireless-bras
    assert len(paths) == 4
    assert '/collections/all' in paths
    assert '/collections/bras' in paths
    assert '/collections/underwire-bras' in paths
    assert '/collections/wireless-bras' in paths

@patch('requests.Session.get')
def test_validate_config(mock_get, tmp_path, mock_collections_response, 
                        mock_products_response, sample_config):
    """Test config validation."""
    # Setup mock responses
    def mock_response(*args, **kwargs):
        mock = Mock()
        mock.status_code = 200
        if 'collections.json' in args[0]:
            mock.json.return_value = mock_collections_response
        else:
            mock.json.return_value = mock_products_response
        return mock
    
    mock_get.side_effect = mock_response
    
    # Create temp config file
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config, f)
    
    # Run validation
    validator = NavigationValidator('https://test.com')
    report = validator.validate_config(str(config_file))
    
    assert report['collections']['total_found'] == 3
    # We expect 3 invalid paths:
    # 1. /collections/underwire-bras
    # 2. /collections/wireless-bras
    # 3. /collections/all
    assert len(report['navigation']['invalid_paths']) == 3
    assert '/collections/underwire-bras' in report['navigation']['invalid_paths']
    assert '/collections/wireless-bras' in report['navigation']['invalid_paths']
    assert '/collections/all' in report['navigation']['invalid_paths']

@patch('requests.Session.get')
def test_update_config(mock_get, tmp_path, mock_collections_response, sample_config):
    """Test config update."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_collections_response
    
    # Create temp config file
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config, f)
    
    # Create mock report
    report = {
        'navigation': {
            'valid_paths': ['/collections/bras'],
            'invalid_paths': [
                '/collections/underwire-bras',
                '/collections/wireless-bras'
            ]
        }
    }
    
    # Update config
    validator = NavigationValidator('https://test.com')
    success = validator.update_config(str(config_file), report)
    
    assert success
    
    # Verify updated config
    with open(config_file, 'r') as f:
        updated_config = yaml.safe_load(f)
    
    assert 'underwire' not in updated_config['shopify']['collections']['bras']['categories']
    assert 'bras' in updated_config['shopify']['collections']['bras']['categories']

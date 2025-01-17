"""
Tests for data quality validation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from scripts.utils.data_quality import DataQualityValidator

@pytest.fixture
def sample_data():
    """Create sample product data."""
    return pd.DataFrame({
        'product_id': ['1', '1', '2', '2'],
        'product_title': ['Classic Bra', 'Classic Bra', 
                         'Wireless Bra', 'Wireless Bra'],
        'variant_id': ['v1', 'v2', 'v3', 'v4'],
        'sku': ['BRA001-30A-BLK', 'BRA001-32A-BLK',
                'BRA002-30A-BLK', 'BRA002-32A-BLK'],
        'price': [60.00, 60.00, 65.00, 65.00],
        'size': ['30A', '32A', '30A', '32A'],
        'color': ['Black', 'Black', 'Black', 'Black']
    })

@pytest.fixture
def invalid_data():
    """Create invalid product data."""
    return pd.DataFrame({
        'product_id': ['1', '1'],
        'product_title': ['Test Bra', 'Test Bra'],
        'variant_id': ['v1', 'v1'],  # Duplicate
        'sku': ['INVALID', 'TEST'],  # Invalid SKUs
        'price': [-10.00, 300.00],   # Invalid prices
        'size': ['XXL', '50Z'],      # Invalid sizes
        'color': ['', np.nan]        # Missing colors
    })

def test_init():
    """Test validator initialization."""
    validator = DataQualityValidator()
    assert validator.logger is not None
    assert 'size_patterns' in validator.rules
    assert 'price_ranges' in validator.rules
    assert 'required_fields' in validator.rules

def test_validate_valid_dataset(sample_data, tmp_path):
    """Test validation of valid dataset."""
    validator = DataQualityValidator()
    df, report = validator.validate_dataset(sample_data)
    
    assert len(report['issues']) == 0
    assert report['total_records'] == 4
    assert report['summary']['products']['total'] == 2
    
    # Check price stats
    price_stats = report['summary']['products']['price_stats']
    assert price_stats['min'] == 60.00
    assert price_stats['max'] == 65.00
    assert price_stats['mean'] == 62.50
    
    # Check variants summary
    variants = report['summary']['variants']
    assert variants['total'] == 4
    assert len(variants['sizes']) == 2
    assert len(variants['colors']) == 1

def test_validate_invalid_dataset(invalid_data, tmp_path):
    """Test validation of invalid dataset."""
    validator = DataQualityValidator()
    df, report = validator.validate_dataset(invalid_data)
    
    # Check issues
    assert len(report['issues']) > 0
    
    # Find specific issues
    issues_by_type = {i['type']: i for i in report['issues']}
    
    # Check price issues
    assert 'invalid_prices' in issues_by_type
    price_issues = issues_by_type['invalid_prices']
    assert price_issues['count'] == 2
    
    # Check duplicate issues
    assert 'duplicate_variants' in issues_by_type
    dup_issues = issues_by_type['duplicate_variants']
    assert dup_issues['count'] == 2

def test_save_report(tmp_path):
    """Test report saving."""
    # Create sample report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_records': 4,
        'issues': [],
        'summary': {
            'products': {
                'total': 2,
                'price_stats': {
                    'min': 60.00,
                    'max': 65.00,
                    'mean': 62.50,
                    'median': 62.50
                }
            }
        }
    }
    
    # Clean output directory
    output_dir = Path('data/quality_reports')
    if output_dir.exists():
        for f in output_dir.glob('quality_report_*.json'):
            f.unlink()
    
    # Save report
    validator = DataQualityValidator()
    validator._save_report(report)
    
    # Check file exists
    report_files = list(output_dir.glob('quality_report_*.json'))
    assert len(report_files) == 1
    
    # Verify content
    with open(report_files[0], 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report['total_records'] == 4
    assert saved_report['summary']['products']['total'] == 2

def test_main_function(sample_data, tmp_path, monkeypatch):
    """Test main function."""
    # Mock pandas read_csv
    def mock_read_csv(*args, **kwargs):
        return sample_data
    
    monkeypatch.setattr(pd, 'read_csv', mock_read_csv)
    
    # Redirect stdout to capture print statements
    import io
    import sys
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    # Run main
    from scripts.utils.data_quality import main
    main()
    
    # Get printed output
    output = captured_output.getvalue()
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    
    # Verify output
    assert 'Data Quality Report' in output
    assert 'Total Records: 4' in output
    assert 'Total Products: 2' in output
    assert 'No issues found!' in output

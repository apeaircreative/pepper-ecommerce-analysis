"""
Data quality validation utilities.
"""
import pandas as pd
from typing import Dict
import logging

class DataQualityValidator:
    """Validate data quality based on business rules."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define validation rules
        self.rules = {
            'bra_products': {
                'required_fields': [
                    'product_id', 'title', 'variant_id', 'sku',
                    'price', 'weight', 'width', 'height', 'length'
                ],
                'numeric_ranges': {
                    'price': (20, 100),  # Typical Pepper bra price range
                    'weight': (50, 500),  # Weight in grams
                    'width': (5, 50),    # Width in cm
                    'height': (5, 50),   # Height in cm
                    'length': (5, 50)    # Length in cm
                }
            },
            'orders': {
                'required_fields': [
                    'id', 'customer_id', 'created_at', 'financial_status',
                    'total_price', 'subtotal_price', 'line_items'
                ],
                'numeric_ranges': {
                    'total_price': (20, 1000),     # Expected order total range
                    'total_tax': (0, 100),         # Tax amount range
                    'total_shipping_price': (0, 50) # Shipping cost range
                },
                'status_values': [
                    'pending', 'processing', 'shipped',
                    'delivered', 'cancelled', 'returned'
                ],
                'address_fields': [
                    'first_name', 'last_name', 'address1',
                    'city', 'province', 'country', 'zip'
                ]
            }
        }
    
    def validate_dataset(self, df: pd.DataFrame, dataset_type: str = 'bra_products') -> Dict:
        """Validate dataset against rules."""
        results = {
            'total_records': len(df),
            'validation_results': {},
            'status': 'passed'
        }
        
        # Get rules for dataset type
        type_rules = self.rules[dataset_type]
        
        # Check required fields
        missing_fields = [
            field for field in type_rules['required_fields'] 
            if field not in df.columns
        ]
        
        if missing_fields:
            results['validation_results']['missing_fields'] = missing_fields
            results['status'] = 'failed'
        
        # Check numeric ranges if applicable
        if 'numeric_ranges' in type_rules:
            range_violations = {}
            for field, (min_val, max_val) in type_rules['numeric_ranges'].items():
                if field not in df.columns:
                    continue
                
                invalid_values = df[
                    (df[field] < min_val) | (df[field] > max_val)
                ]
                
                if len(invalid_values) > 0:
                    range_violations[field] = {
                        'invalid_count': len(invalid_values),
                        'min_found': float(df[field].min()),
                        'max_found': float(df[field].max()),
                        'expected_range': (min_val, max_val)
                    }
            
            if range_violations:
                results['validation_results']['range_violations'] = range_violations
                results['status'] = 'failed'
        
        # Check status values if applicable
        if dataset_type == 'orders' and 'status_values' in type_rules:
            invalid_statuses = df[
                ~df['financial_status'].isin(type_rules['status_values'])
            ]
            
            if len(invalid_statuses) > 0:
                results['validation_results']['invalid_statuses'] = {
                    'count': len(invalid_statuses),
                    'values': invalid_statuses['financial_status'].unique().tolist()
                }
                results['status'] = 'failed'
        
        # Check address completeness if applicable
        if dataset_type == 'orders' and 'address_fields' in type_rules:
            missing_address_fields = {
                'shipping': [],
                'billing': []
            }
            
            for address_type in ['shipping_address', 'billing_address']:
                if address_type in df.columns:
                    required_fields = type_rules['address_fields']
                    addresses = df[address_type].apply(pd.Series)
                    
                    missing = [
                        field for field in required_fields 
                        if field not in addresses.columns or addresses[field].isna().any()
                    ]
                    
                    if missing:
                        missing_address_fields[address_type.split('_')[0]] = missing
            
            if any(missing_address_fields.values()):
                results['validation_results']['missing_address_fields'] = missing_address_fields
                results['status'] = 'failed'
        
        return results

def main():
    """Run data quality validation on latest product data."""
    # Load latest product data
    try:
        df = pd.read_csv('data/raw/shopify_products.csv')
        
        # Run validation
        validator = DataQualityValidator()
        results = validator.validate_dataset(df)
        
        # Print summary
        print("\nData Quality Report")
        print("-" * 50)
        print(f"Total Records: {results['total_records']}")
        print(f"Status: {results['status']}")
        
        if results['status'] == 'failed':
            print("\nIssues Found:")
            for issue_type, issue_details in results['validation_results'].items():
                if issue_type == 'missing_fields':
                    print(f"- Missing fields: {issue_details}")
                elif issue_type == 'range_violations':
                    for field, details in issue_details.items():
                        print(f"- Range violation in {field}: {details['invalid_count']} occurrences")
                elif issue_type == 'duplicates':
                    for field, count in issue_details.items():
                        if count > 0:
                            print(f"- Duplicate {field}: {count} occurrences")
                elif issue_type == 'invalid_statuses':
                    print(f"- Invalid statuses: {issue_details['count']} occurrences")
                elif issue_type == 'missing_address_fields':
                    for address_type, fields in issue_details.items():
                        print(f"- Missing address fields in {address_type}: {fields}")
        else:
            print("\nNo issues found!")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()

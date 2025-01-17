"""
Validate Pepper product data against known patterns and rules.
"""
import re
from typing import Dict, List, Optional, Union
import pandas as pd

class ProductValidator:
    def __init__(self):
        """Initialize validator with known patterns and rules."""
        self.sku_patterns = {
            'zero_g': r'^(BRA035|ZGW01)',
            'signature': r'^SAY01',
            'lift_up': r'^LUB01'
        }
        
        self.size_matrix = {
            'band_sizes': range(30, 43, 2),  # 30, 32, 34, 36, 38, 40, 42
            'cup_sizes': ['AA', 'A', 'B']
        }
        
        self.price_ranges = {
            'zero_g': (65.00, 65.00),
            'signature': (60.00, 60.00),
            'lift_up': (65.00, 65.00)
        }
        
    def validate_sku(self, sku: str) -> Dict[str, Union[bool, str]]:
        """
        Validate SKU format and extract product line.
        
        Args:
            sku: Product SKU to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'product_line': None,
            'errors': []
        }
        
        for line, pattern in self.sku_patterns.items():
            if re.match(pattern, sku):
                result['valid'] = True
                result['product_line'] = line
                return result
                
        result['errors'].append(f"Invalid SKU pattern: {sku}")
        return result
        
    def validate_size(self, band: str, cup: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate size combination.
        
        Args:
            band: Band size (30-42)
            cup: Cup size (AA-B)
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        try:
            band_int = int(band)
            if band_int not in self.size_matrix['band_sizes']:
                result['valid'] = False
                result['errors'].append(f"Invalid band size: {band}")
        except ValueError:
            result['valid'] = False
            result['errors'].append(f"Band size must be numeric: {band}")
            
        if cup not in self.size_matrix['cup_sizes']:
            result['valid'] = False
            result['errors'].append(f"Invalid cup size: {cup}")
            
        return result
        
    def validate_price(self, sku: str, price: float) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate price for product line.
        
        Args:
            sku: Product SKU
            price: Price to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        sku_validation = self.validate_sku(sku)
        if not sku_validation['valid']:
            result['valid'] = False
            result['errors'].extend(sku_validation['errors'])
            return result
            
        product_line = sku_validation['product_line']
        min_price, max_price = self.price_ranges[product_line]
        
        if not min_price <= price <= max_price:
            result['valid'] = False
            result['errors'].append(
                f"Invalid price {price} for {product_line}. "
                f"Expected range: {min_price}-{max_price}"
            )
            
        return result
        
    def validate_product_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate entire product dataset.
        
        Args:
            df: DataFrame with product data
            
        Returns:
            DataFrame with validation results
        """
        results = []
        
        for _, row in df.iterrows():
            sku = row['Variant SKU']
            price = float(row['Variant Price'])
            size = row['Option1 Value']  # Assuming Option1 is Size
            
            # Split size into band and cup
            band = re.match(r'(\d+)', size).group(1)
            cup = size[len(band):]
            
            # Run all validations
            sku_valid = self.validate_sku(sku)
            size_valid = self.validate_size(band, cup)
            price_valid = self.validate_price(sku, price)
            
            results.append({
                'sku': sku,
                'valid': all([sku_valid['valid'], 
                            size_valid['valid'], 
                            price_valid['valid']]),
                'errors': (sku_valid.get('errors', []) + 
                         size_valid.get('errors', []) + 
                         price_valid.get('errors', []))
            })
            
        return pd.DataFrame(results)

if __name__ == '__main__':
    # Example usage
    validator = ProductValidator()
    
    # Test SKU validation
    print(validator.validate_sku('BRA035BU32AA'))  # Valid Zero-G
    print(validator.validate_sku('SAY01BL32A'))    # Valid Signature
    print(validator.validate_sku('INVALID'))       # Invalid SKU

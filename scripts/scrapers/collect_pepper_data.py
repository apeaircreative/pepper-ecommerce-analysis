"""
Collect specific Pepper product data for comparison with Olist dataset.
Focus on bras collection for direct comparison with Olist's fashion category.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import yaml
import logging
from typing import Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts.utils.shopify_utils import ShopifyScraper
from scripts.utils.data_quality import DataQualityValidator
from scripts.utils.data_transformer import DataTransformer

def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'data_collection_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_config() -> Dict:
    """Load configuration from YAML."""
    config_path = project_root / 'config' / 'urls.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path) as f:
        return yaml.safe_load(f)

def save_data(df: pd.DataFrame, filename: str):
    """Save collected data with timestamp."""
    data_dir = project_root / 'data' / 'pepper'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = data_dir / f'{filename}_{timestamp}.csv'
    
    df.to_csv(output_file, index=False)
    return output_file

def collect_bra_data(config: Dict, logger: logging.Logger) -> pd.DataFrame:
    """Collect bra product data for comparison."""
    scraper = ShopifyScraper(str(project_root / 'config' / 'urls.yaml'))
    
    try:
        # Focus on bras collection
        logger.info("Collecting bra products data...")
        bra_collection = config['shopify']['collections']['bras']['main']
        products = scraper.get_collection_products(bra_collection)
        
        if not products:
            logger.error("No products found in bras collection")
            return pd.DataFrame()
        
        # Extract relevant fields for comparison
        df = pd.DataFrame(products)
        relevant_fields = [
            'product_id', 'title', 'variant_id', 'sku',
            'price', 'weight', 'width', 'height', 'length'
        ]
        
        df = df[relevant_fields].copy()
        logger.info(f"Collected {len(df)} bra products")
        
        return df
        
    except Exception as e:
        logger.error(f"Error collecting bra data: {str(e)}")
        raise

def validate_data(df: pd.DataFrame, logger: logging.Logger) -> Dict:
    """Validate collected data."""
    validator = DataQualityValidator()
    
    try:
        logger.info("Validating bra product data...")
        validation_report = validator.validate_dataset(df, 'bra_products')
        logger.info("Validation complete")
        return validation_report
        
    except Exception as e:
        logger.error(f"Error validating data: {str(e)}")
        raise

def transform_to_olist_schema(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Transform data to match Olist schema for comparison."""
    transformer = DataTransformer()
    
    try:
        logger.info("Transforming data to Olist schema...")
        transformed_df = transformer.transform_products(df)
        logger.info("Transformation complete")
        return transformed_df
        
    except Exception as e:
        logger.error(f"Error transforming data: {str(e)}")
        raise

def main():
    """Main execution function."""
    # Setup
    logger = setup_logging()
    logger.info("Starting focused data collection process...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Collect bra product data
        raw_data = collect_bra_data(config, logger)
        
        # Save raw data
        raw_file = save_data(raw_data, 'raw_bra_products')
        logger.info(f"Saved raw data to {raw_file}")
        
        # Validate data
        validation_results = validate_data(raw_data, logger)
        
        # Save validation report
        reports_dir = project_root / 'data' / 'quality_reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f'validation_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            yaml.dump(validation_results, f)
        
        logger.info(f"Saved validation report to {report_file}")
        
        # Transform to Olist schema
        transformed_data = transform_to_olist_schema(raw_data, logger)
        
        # Save transformed data
        transformed_file = save_data(transformed_data, 'transformed_bra_products')
        logger.info(f"Saved transformed data to {transformed_file}")
        
        logger.info("Data collection process complete")
        
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

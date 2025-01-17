"""
Collect order data from Pepper's Shopify store.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import yaml
import logging
from typing import Dict, List, Optional
import time

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
    log_file = log_dir / f'order_collection_{timestamp}.log'
    
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

def save_data(df: pd.DataFrame, filename: str) -> Path:
    """Save collected data with timestamp."""
    data_dir = project_root / 'data' / 'pepper'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = data_dir / f'{filename}_{timestamp}.csv'
    
    df.to_csv(output_file, index=False)
    return output_file

def collect_orders(config: Dict, logger: logging.Logger, 
                  start_date: Optional[datetime] = None) -> pd.DataFrame:
    """Collect order data from Shopify."""
    scraper = ShopifyScraper(str(project_root / 'config' / 'urls.yaml'))
    
    try:
        # Default to last 30 days if no start date provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        
        logger.info(f"Collecting orders since {start_date}")
        
        # Get orders with pagination
        orders = []
        page = 1
        while True:
            params = {
                'limit': 250,  # Max allowed by Shopify
                'page': page,
                'created_at_min': start_date.isoformat(),
                'status': 'any'
            }
            
            page_orders = scraper.get_orders(params)
            if not page_orders:
                break
                
            orders.extend(page_orders)
            logger.info(f"Collected {len(page_orders)} orders from page {page}")
            
            page += 1
            time.sleep(1)  # Rate limiting
        
        if not orders:
            logger.error("No orders found in specified date range")
            return pd.DataFrame()
        
        # Extract relevant fields
        df = pd.DataFrame(orders)
        relevant_fields = [
            'id', 'customer_id', 'created_at', 'processed_at',
            'financial_status', 'fulfillment_status', 'total_price',
            'subtotal_price', 'total_tax', 'total_shipping_price_set',
            'billing_address', 'shipping_address', 'line_items'
        ]
        
        df = df[relevant_fields].copy()
        logger.info(f"Collected {len(df)} orders")
        
        return df
        
    except Exception as e:
        logger.error(f"Error collecting orders: {str(e)}")
        raise

def validate_orders(df: pd.DataFrame, logger: logging.Logger) -> Dict:
    """Validate collected order data."""
    validator = DataQualityValidator()
    
    try:
        logger.info("Validating order data...")
        validation_report = validator.validate_dataset(df, 'orders')
        logger.info("Validation complete")
        return validation_report
        
    except Exception as e:
        logger.error(f"Error validating orders: {str(e)}")
        raise

def transform_to_thelook_schema(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Transform order data to match TheLook schema."""
    transformer = DataTransformer()
    
    try:
        logger.info("Transforming orders to TheLook schema...")
        transformed_df = transformer.transform_orders(df)
        logger.info("Transformation complete")
        return transformed_df
        
    except Exception as e:
        logger.error(f"Error transforming orders: {str(e)}")
        raise

def main():
    """Main execution function."""
    # Setup
    logger = setup_logging()
    logger.info("Starting order data collection process...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Collect order data
        raw_data = collect_orders(config, logger)
        
        # Save raw data
        raw_file = save_data(raw_data, 'raw_orders')
        logger.info(f"Saved raw data to {raw_file}")
        
        # Validate data
        validation_results = validate_orders(raw_data, logger)
        
        # Save validation report
        reports_dir = project_root / 'data' / 'quality_reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f'order_validation_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            yaml.dump(validation_results, f)
        
        logger.info(f"Saved validation report to {report_file}")
        
        # Transform to TheLook schema
        transformed_data = transform_to_thelook_schema(raw_data, logger)
        
        # Save transformed data
        transformed_file = save_data(transformed_data, 'transformed_orders')
        logger.info(f"Saved transformed data to {transformed_file}")
        
        logger.info("Order collection process complete")
        
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Generate simulated order data using real product data.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging
import glob

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts.utils.data_simulator import DataSimulator
from scripts.utils.data_transformer import DataTransformer

def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'order_simulation_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_latest_product_data() -> pd.DataFrame:
    """Load the most recent transformed product data."""
    data_dir = project_root / 'data' / 'pepper'
    product_files = glob.glob(str(data_dir / 'transformed_bra_products_*.csv'))
    
    if not product_files:
        raise FileNotFoundError("No transformed product data found")
    
    # Get most recent file
    latest_file = max(product_files)
    return pd.read_csv(latest_file)

def save_data(df: pd.DataFrame, filename: str) -> Path:
    """Save data with timestamp."""
    data_dir = project_root / 'data' / 'pepper'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = data_dir / f'{filename}_{timestamp}.csv'
    
    df.to_csv(output_file, index=False)
    return output_file

def main():
    """Main execution function."""
    logger = setup_logging()
    logger.info("Starting order data simulation...")
    
    try:
        # Load product data
        products_df = load_latest_product_data()
        logger.info(f"Loaded {len(products_df)} products")
        
        # Initialize simulator
        simulator = DataSimulator()
        
        # Generate orders
        orders_df, items_df = simulator.generate_orders(
            products_df,
            num_days=30,
            orders_per_day=20
        )
        
        logger.info(f"Generated {len(orders_df)} orders with {len(items_df)} items")
        
        # Save data
        orders_file = save_data(orders_df, 'simulated_orders')
        items_file = save_data(items_df, 'simulated_order_items')
        
        logger.info(f"Saved orders to {orders_file}")
        logger.info(f"Saved order items to {items_file}")
        
        # Transform to TheLook schema
        transformer = DataTransformer()
        transformed_items = transformer.transform_orders(items_df)
        
        # Save transformed data
        transformed_file = save_data(
            transformed_items,
            'transformed_order_items'
        )
        logger.info(f"Saved transformed data to {transformed_file}")
        
        logger.info("Order simulation complete")
        
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

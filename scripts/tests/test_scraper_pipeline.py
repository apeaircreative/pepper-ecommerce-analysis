"""
End-to-end test of the scraping pipeline.
"""
import sys
from pathlib import Path
import pandas as pd
import yaml
from scripts.utils.shopify_utils import ShopifyScraper

def test_single_collection():
    """Test scraping a single collection."""
    print("Starting end-to-end test of scraping pipeline...")
    
    # Initialize scraper
    config_path = "scripts/scrapers/config/urls.yaml"
    scraper = ShopifyScraper(config_path)
    
    # Load config to get collection URL
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Test with bras collection (main product line)
    collection_url = config['shopify']['collections']['bras']['main']
    print(f"\nScraping collection: {collection_url}")
    
    # Collect data
    df = scraper.scrape_collection(collection_url)
    print(f"\nInitial data collected: {len(df)} records")
    
    if len(df) == 0:
        print("No data collected. Exiting...")
        return False
    
    # Validate data
    valid_df = scraper.validate_data(df)
    print(f"Valid records: {len(valid_df)} ({len(valid_df)/len(df)*100:.1f}%)")
    
    # Data quality checks
    if len(valid_df) > 0:
        print("\nData Quality Summary:")
        print("-" * 50)
        
        # Product lines distribution
        print("\nProduct Lines Distribution:")
        product_lines = valid_df['sku'].apply(
            lambda x: scraper.validate_sku(x)['product_line']
        ).value_counts()
        for line, count in product_lines.items():
            print(f"- {line}: {count} variants")
        
        # Size distribution
        print("\nSize Distribution:")
        size_dist = valid_df['size'].value_counts()
        print(f"- Most common sizes: {', '.join(size_dist.head(3).index)}")
        print(f"- Least common sizes: {', '.join(size_dist.tail(3).index)}")
        
        # Price points
        print("\nPrice Points:")
        price_stats = valid_df.groupby(
            valid_df['sku'].apply(lambda x: scraper.validate_sku(x)['product_line'])
        )['price'].agg(['mean', 'min', 'max'])
        print(price_stats)
        
        # Save results
        output_dir = Path("data/test_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        valid_df.to_csv(output_dir / "test_scrape_results.csv", index=False)
        print(f"\nResults saved to: {output_dir}/test_scrape_results.csv")
    
    return len(valid_df) > 0

if __name__ == "__main__":
    success = test_single_collection()
    sys.exit(0 if success else 1)

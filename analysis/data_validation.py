"""
Data validation and seasonality analysis.
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

def validate_data():
    """Validate data quality and analyze seasonality."""
    conn = sqlite3.connect('analysis/pepper_analysis.db')
    
    # Data completeness check
    completeness_query = """
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) as missing_status,
        SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END) as missing_dates,
        SUM(CASE WHEN sale_price IS NULL THEN 1 ELSE 0 END) as missing_prices,
        MIN(date(created_at)) as earliest_date,
        MAX(date(created_at)) as latest_date
    FROM transformed_order_items;
    """
    
    # Status distribution
    status_query = """
    SELECT 
        status,
        COUNT(*) as count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
    FROM transformed_order_items
    GROUP BY status
    ORDER BY count DESC;
    """
    
    # Monthly trends
    seasonality_query = """
    WITH size_patterns AS (
        SELECT id, sku,
        CASE 
            WHEN (
                (substr(sku, -3) LIKE '30A%' OR substr(sku, -3) LIKE '30B%' OR
                 substr(sku, -3) LIKE '32A%' OR substr(sku, -3) LIKE '32B%' OR
                 substr(sku, -3) LIKE '34A%' OR substr(sku, -3) LIKE '34B%' OR
                 substr(sku, -3) LIKE '36A%' OR substr(sku, -3) LIKE '36B%')
            ) THEN 'Core'
            ELSE 'Extended'
        END as segment
        FROM transformed_products
    )
    SELECT 
        sp.segment,
        strftime('%Y-%m', created_at) as month,
        COUNT(DISTINCT o.order_id) as orders,
        COUNT(DISTINCT o.user_id) as customers,
        ROUND(SUM(o.sale_price), 2) as revenue
    FROM transformed_order_items o
    JOIN size_patterns sp ON o.product_id = sp.id
    GROUP BY sp.segment, month
    ORDER BY month, sp.segment;
    """
    
    # User purchase history
    user_history_query = """
    WITH size_patterns AS (
        SELECT id, sku,
        CASE 
            WHEN (
                (substr(sku, -3) LIKE '30A%' OR substr(sku, -3) LIKE '30B%' OR
                 substr(sku, -3) LIKE '32A%' OR substr(sku, -3) LIKE '32B%' OR
                 substr(sku, -3) LIKE '34A%' OR substr(sku, -3) LIKE '34B%' OR
                 substr(sku, -3) LIKE '36A%' OR substr(sku, -3) LIKE '36B%')
            ) THEN 'Core'
            ELSE 'Extended'
        END as segment
        FROM transformed_products
    )
    SELECT 
        o.user_id,
        COUNT(DISTINCT o.order_id) as total_orders,
        GROUP_CONCAT(DISTINCT sp.segment) as segments_purchased,
        MIN(date(o.created_at)) as first_purchase,
        MAX(date(o.created_at)) as last_purchase,
        COUNT(DISTINCT strftime('%Y-%m', o.created_at)) as purchase_months
    FROM transformed_order_items o
    JOIN size_patterns sp ON o.product_id = sp.id
    GROUP BY o.user_id
    HAVING total_orders > 1
    ORDER BY total_orders DESC
    LIMIT 10;
    """
    
    # Run analyses
    print("\nData Completeness Check:")
    completeness = pd.read_sql(completeness_query, conn)
    print(completeness.to_string(index=False))
    
    print("\nOrder Status Distribution:")
    status_dist = pd.read_sql(status_query, conn)
    print(status_dist.to_string(index=False))
    
    print("\nMonthly Trends:")
    seasonality = pd.read_sql(seasonality_query, conn)
    print(seasonality.to_string(index=False))
    
    print("\nTop Multi-Purchase Customers:")
    user_history = pd.read_sql(user_history_query, conn)
    print(user_history.to_string(index=False))
    
    # Save results
    results_file = Path('analysis/data_validation_results.md')
    with open(results_file, 'w') as f:
        f.write("# Data Validation Results\n")
        f.write(f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n\n")
        
        f.write("## Data Completeness\n")
        f.write(completeness.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Order Status Distribution\n")
        f.write(status_dist.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Monthly Trends\n")
        f.write(seasonality.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Multi-Purchase Customer Analysis\n")
        f.write(user_history.to_markdown(index=False))
    
    conn.close()

if __name__ == "__main__":
    validate_data()

"""
Initial market segmentation analysis for Pepper.
"""
import pandas as pd
import sqlite3
from pathlib import Path

def analyze_segments():
    """Run initial segment analysis."""
    # Connect to database
    conn = sqlite3.connect('analysis/pepper_analysis.db')
    
    # Product distribution query
    segment_query = """
    WITH size_patterns AS (
        SELECT id, sku, retail_price,
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
        segment,
        COUNT(*) as product_count,
        ROUND(AVG(retail_price), 2) as avg_price,
        COUNT(DISTINCT id) as unique_styles
    FROM size_patterns
    GROUP BY segment
    ORDER BY product_count DESC;
    """
    
    # Revenue analysis query
    revenue_query = """
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
        COUNT(DISTINCT o.order_id) as orders,
        COUNT(DISTINCT o.user_id) as customers,
        ROUND(SUM(o.sale_price), 2) as revenue,
        ROUND(AVG(o.sale_price), 2) as aov
    FROM transformed_order_items o
    JOIN size_patterns sp ON o.product_id = sp.id
    GROUP BY sp.segment
    ORDER BY revenue DESC;
    """
    
    # Run analyses
    print("\nProduct Distribution by Segment:")
    segment_dist = pd.read_sql(segment_query, conn)
    print(segment_dist.to_string(index=False))
    
    print("\nRevenue Analysis by Segment:")
    revenue_dist = pd.read_sql(revenue_query, conn)
    print(revenue_dist.to_string(index=False))
    
    # Save results
    results_file = Path('analysis/segment_analysis_results.md')
    with open(results_file, 'w') as f:
        f.write("# Market Segmentation Analysis Results\n")
        f.write("**Date**: January 17, 2025\n\n")
        
        f.write("## Product Distribution\n")
        f.write(segment_dist.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Revenue Analysis\n")
        f.write(revenue_dist.to_markdown(index=False))
    
    conn.close()

if __name__ == "__main__":
    analyze_segments()

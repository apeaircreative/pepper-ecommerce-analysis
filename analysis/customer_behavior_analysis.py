"""
Customer behavior analysis focusing on returns and lifetime value.
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

def analyze_customer_behavior():
    """Analyze return rates and customer lifetime value by segment."""
    conn = sqlite3.connect('analysis/pepper_analysis.db')
    
    # Return rate analysis
    returns_query = """
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
        COUNT(DISTINCT o.order_id) as total_orders,
        SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END) as returns,
        ROUND(100.0 * SUM(CASE WHEN o.status = 'returned' THEN 1 ELSE 0 END) / 
              COUNT(DISTINCT o.order_id), 2) as return_rate
    FROM transformed_order_items o
    JOIN size_patterns sp ON o.product_id = sp.id
    GROUP BY sp.segment
    ORDER BY return_rate DESC;
    """
    
    # Customer lifetime value analysis
    clv_query = """
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
    ),
    customer_orders AS (
        SELECT 
            o.user_id,
            sp.segment,
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(o.sale_price) as total_spent,
            MIN(o.created_at) as first_order,
            MAX(o.created_at) as last_order,
            ROUND(JULIANDAY(MAX(o.created_at)) - JULIANDAY(MIN(o.created_at))) as days_between_orders
        FROM transformed_order_items o
        JOIN size_patterns sp ON o.product_id = sp.id
        GROUP BY o.user_id, sp.segment
    )
    SELECT 
        segment,
        COUNT(DISTINCT user_id) as customers,
        ROUND(AVG(order_count), 2) as avg_orders_per_customer,
        ROUND(AVG(total_spent), 2) as avg_customer_spend,
        ROUND(AVG(CASE WHEN order_count > 1 THEN days_between_orders END), 2) as avg_days_between_orders
    FROM customer_orders
    GROUP BY segment
    ORDER BY avg_customer_spend DESC;
    """
    
    # Purchase frequency analysis
    frequency_query = """
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
        COUNT(DISTINCT o.user_id) as total_customers,
        SUM(CASE WHEN orders = 1 THEN 1 ELSE 0 END) as one_time_buyers,
        SUM(CASE WHEN orders = 2 THEN 1 ELSE 0 END) as two_time_buyers,
        SUM(CASE WHEN orders >= 3 THEN 1 ELSE 0 END) as loyal_customers,
        ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) / 
              COUNT(DISTINCT o.user_id), 2) as retention_rate
    FROM (
        SELECT user_id, COUNT(DISTINCT order_id) as orders
        FROM transformed_order_items
        GROUP BY user_id
    ) o
    JOIN transformed_order_items oi ON o.user_id = oi.user_id
    JOIN size_patterns sp ON oi.product_id = sp.id
    GROUP BY sp.segment
    ORDER BY retention_rate DESC;
    """
    
    # Run analyses
    print("\nReturn Rate Analysis:")
    returns_dist = pd.read_sql(returns_query, conn)
    print(returns_dist.to_string(index=False))
    
    print("\nCustomer Lifetime Value Analysis:")
    clv_dist = pd.read_sql(clv_query, conn)
    print(clv_dist.to_string(index=False))
    
    print("\nPurchase Frequency Analysis:")
    frequency_dist = pd.read_sql(frequency_query, conn)
    print(frequency_dist.to_string(index=False))
    
    # Save results
    results_file = Path('analysis/customer_behavior_results.md')
    with open(results_file, 'w') as f:
        f.write("# Customer Behavior Analysis Results\n")
        f.write(f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n\n")
        
        f.write("## Return Rate Analysis\n")
        f.write(returns_dist.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Customer Lifetime Value Analysis\n")
        f.write(clv_dist.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Purchase Frequency Analysis\n")
        f.write(frequency_dist.to_markdown(index=False))
    
    conn.close()

if __name__ == "__main__":
    analyze_customer_behavior()

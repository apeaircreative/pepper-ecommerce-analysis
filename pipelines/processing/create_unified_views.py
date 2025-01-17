"""
Create unified views combining TheLook and Olist data.
This creates standardized views for cross-platform analysis.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

def create_unified_views():
    """Create unified views combining both platforms."""
    client = bigquery.Client()
    project_id = "pepper-analytics-2024"

    # Create unified customer view
    unified_customers = f"""
    CREATE OR REPLACE VIEW `{project_id}.transformed_data.vw_unified_customers` AS
    
    -- TheLook Customers
    SELECT
        CAST(id AS STRING) as customer_id,  -- Cast to STRING to match Olist
        'thelook' as platform,
        first_name,
        last_name,
        email,
        age,
        gender,
        city,
        state,
        country,
        created_at as registration_date,
        NULL as last_order_date  -- Will update this in a separate step
    FROM `{project_id}.thelook_ecommerce.users`
    
    UNION ALL
    
    -- Olist Customers
    SELECT
        c.customer_unique_id as customer_id,  -- Already STRING
        'olist' as platform,
        NULL as first_name,
        NULL as last_name,
        NULL as email,
        NULL as age,
        NULL as gender,
        c.customer_city as city,
        c.customer_state as state,
        'Brazil' as country,
        MIN(o.order_purchase_timestamp) as registration_date,
        MAX(o.order_purchase_timestamp) as last_order_date
    FROM `{project_id}.transformed_data.vw_customers_clean` c
    LEFT JOIN `{project_id}.transformed_data.vw_orders_clean` o
        ON c.customer_unique_id = o.customer_unique_id
    GROUP BY 
        c.customer_unique_id,
        c.customer_city,
        c.customer_state
    """

    # Create unified order view
    unified_orders = f"""
    CREATE OR REPLACE VIEW `{project_id}.transformed_data.vw_unified_orders` AS
    
    -- TheLook Orders
    SELECT
        CAST(o.order_id AS STRING) as order_id,
        CAST(o.user_id AS STRING) as customer_id,
        'thelook' as platform,
        o.status,
        o.created_at as order_date,
        o.shipped_at as shipped_date,
        o.delivered_at as delivered_date,
        NULL as estimated_delivery_date,
        o.num_of_item as items_count,
        SUM(i.sale_price) as order_amount
    FROM `{project_id}.thelook_ecommerce.orders` o
    LEFT JOIN `{project_id}.thelook_ecommerce.order_items` i
        ON o.order_id = i.order_id
    GROUP BY 
        o.order_id,
        o.user_id,
        o.status,
        o.created_at,
        o.shipped_at,
        o.delivered_at,
        o.num_of_item
    
    UNION ALL
    
    -- Olist Orders
    SELECT
        o.order_id,  -- Already STRING
        o.customer_unique_id as customer_id,  -- Already STRING
        'olist' as platform,
        o.order_status as status,
        o.order_purchase_timestamp as order_date,
        o.order_delivered_carrier_date as shipped_date,
        o.order_delivered_customer_date as delivered_date,
        o.order_estimated_delivery_date,
        COUNT(i.order_item_id) as items_count,
        SUM(i.price) as order_amount
    FROM `{project_id}.transformed_data.vw_orders_clean` o
    LEFT JOIN `{project_id}.raw_data.olist_order_items` i
        ON o.order_id = i.order_id
    GROUP BY 
        o.order_id,
        o.customer_unique_id,
        o.order_status,
        o.order_purchase_timestamp,
        o.order_delivered_carrier_date,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date
    """

    # Verify unified customer view
    verify_customers = f"""
    SELECT 
        platform,
        COUNT(*) as total_customers,
        COUNT(DISTINCT customer_id) as unique_customers,
        MIN(registration_date) as earliest_registration,
        MAX(registration_date) as latest_registration,
        COUNT(DISTINCT CONCAT(city, '|', state)) as unique_locations
    FROM `{project_id}.transformed_data.vw_unified_customers`
    GROUP BY platform
    ORDER BY platform
    """

    # Verify unified order view
    verify_orders = f"""
    SELECT 
        platform,
        COUNT(*) as total_orders,
        COUNT(DISTINCT order_id) as unique_orders,
        COUNT(DISTINCT customer_id) as unique_customers,
        MIN(order_date) as earliest_order,
        MAX(order_date) as latest_order,
        AVG(items_count) as avg_items_per_order,
        AVG(order_amount) as avg_order_amount
    FROM `{project_id}.transformed_data.vw_unified_orders`
    GROUP BY platform
    ORDER BY platform
    """

    print("=== Creating Unified Views ===")
    print(f"Started at: {datetime.now()}\n")

    try:
        print("1. Creating unified customer view...")
        client.query(unified_customers).result()
        print("✓ Unified customer view created\n")

        print("2. Creating unified order view...")
        client.query(unified_orders).result()
        print("✓ Unified order view created\n")

        print("3. Verifying unified customer view...")
        customer_stats = client.query(verify_customers).to_dataframe()
        print(customer_stats.to_string(index=False))
        print()

        print("4. Verifying unified order view...")
        order_stats = client.query(verify_orders).to_dataframe()
        print(order_stats.to_string(index=False))
        print()

        print("=== View Creation Complete ===")
        print("\nNext steps:")
        print("1. Create customer segmentation analysis")
        print("2. Analyze order patterns across platforms")
        print("3. Set up monitoring for data quality")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nDebug information:")
        print(f"Project ID: {project_id}")
        print("Make sure you have:")
        print("1. Access to both TheLook and Olist datasets")
        print("2. Permissions to create views")
        print("3. All source views exist")

if __name__ == "__main__":
    create_unified_views()

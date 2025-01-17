from google.cloud import bigquery

def create_unified_views():
    client = bigquery.Client()
    
    # Create view for customers
    customer_view_query = """
    CREATE OR REPLACE VIEW `pepper-analytics-2024.processed_data.unified_customers_view` AS
    SELECT 
        CAST(id AS STRING) as customer_id,
        'shopify' as platform,
        first_name,
        last_name,
        email,
        gender,
        country,
        traffic_source as acquisition_source,
        created_at as first_interaction_date,
        created_at
    FROM `bigquery-public-data.thelook_ecommerce.users`
    """
    
    # Create view for orders (including items)
    orders_view_query = """
    CREATE OR REPLACE VIEW `pepper-analytics-2024.processed_data.unified_orders_view` AS
    SELECT 
        CAST(o.order_id AS STRING) as order_id,
        'shopify' as platform,
        CAST(o.user_id AS STRING) as customer_id,
        o.created_at as order_date,
        o.status,
        COUNT(oi.id) as items_count,
        SUM(oi.sale_price) as total_amount,
        STRUCT(
            u.country as country,
            u.state as state,
            u.city as city,
            u.postal_code as zip_code
        ) as shipping_address,
        o.created_at,
        o.shipped_at,
        o.delivered_at,
        o.returned_at
    FROM `bigquery-public-data.thelook_ecommerce.orders` o
    JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi
        ON o.order_id = oi.order_id
    JOIN `bigquery-public-data.thelook_ecommerce.users` u
        ON o.user_id = u.id
    GROUP BY 
        o.order_id,
        o.user_id,
        o.status,
        u.country,
        u.state,
        u.city,
        u.postal_code,
        o.created_at,
        o.shipped_at,
        o.delivered_at,
        o.returned_at
    """
    
    # Create customer metrics view
    customer_metrics_query = """
    CREATE OR REPLACE VIEW `pepper-analytics-2024.processed_data.customer_metrics_view` AS
    SELECT 
        u.customer_id,
        u.platform,
        u.first_interaction_date,
        MAX(o.order_date) as last_order_date,
        COUNT(DISTINCT o.order_id) as total_orders,
        SUM(o.total_amount) as total_spent,
        SUM(CASE WHEN o.returned_at IS NOT NULL THEN 1 ELSE 0 END) as returns_count,
        u.country,
        u.acquisition_source,
        u.created_at
    FROM `pepper-analytics-2024.processed_data.unified_customers_view` u
    LEFT JOIN `pepper-analytics-2024.processed_data.unified_orders_view` o
        ON u.customer_id = o.customer_id
    GROUP BY 
        u.customer_id,
        u.platform,
        u.first_interaction_date,
        u.country,
        u.acquisition_source,
        u.created_at
    """
    
    try:
        # Execute views creation
        for name, query in {
            "customers": customer_view_query,
            "orders": orders_view_query,
            "metrics": customer_metrics_query
        }.items():
            query_job = client.query(query)
            query_job.result()
            print(f"Successfully created {name} view")
    except Exception as e:
        print(f"Error creating views: {e}")

def verify_views():
    client = bigquery.Client()
    
    verify_query = """
    SELECT 
        'Customers' as source, 
        COUNT(*) as count,
        COUNT(DISTINCT customer_id) as unique_customers
    FROM `pepper-analytics-2024.processed_data.unified_customers_view`
    UNION ALL
    SELECT 
        'Orders' as source, 
        COUNT(*) as count,
        COUNT(DISTINCT customer_id) as unique_customers
    FROM `pepper-analytics-2024.processed_data.unified_orders_view`
    UNION ALL
    SELECT 
        'Customer Metrics' as source, 
        COUNT(*) as count,
        COUNT(DISTINCT customer_id) as unique_customers
    FROM `pepper-analytics-2024.processed_data.customer_metrics_view`
    """
    
    try:
        query_job = client.query(verify_query)
        results = query_job.result()
        print("\nData counts:")
        for row in results:
            print(f"{row.source}: {row.count} total records, {row.unique_customers} unique customers")
    except Exception as e:
        print(f"Error verifying views: {e}")

if __name__ == "__main__":
    create_unified_views()
    verify_views()
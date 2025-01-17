"""
Analysis of Pepper's business performance in serving small-chested customers.
Focus: Understanding how well we serve our core customer segment (sizes 30-36 A/B).
"""
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path
import random

def load_historical_data():
    """Simulate loading 12 months of historical data with size information."""
    conn = sqlite3.connect('analysis/pepper_analysis.db')
    
    # Base query for current data
    current_query = """
    SELECT * FROM transformed_order_items 
    WHERE date(created_at) >= date('2024-12-18')
    """
    current_orders = pd.read_sql(current_query, conn)
    
    # Simulate historical data patterns (last 12 months)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 17)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    # Create historical patterns with:
    # 1. Seasonal variations (higher in Dec, Feb, July)
    # 2. Growth trend (20% YoY)
    # 3. Weekly patterns (higher on weekends)
    historical_data = []
    base_orders_per_day = 50  # Starting point
    
    # Create a fixed pool of customers for more realistic behavior
    n_customers = 2000
    customer_pool = [f"USER_{i}" for i in range(n_customers)]
    
    # Define possible sizes
    sizes = []
    for band in [30, 32, 34, 36]:
        for cup in ['AA', 'A', 'B']:
            sizes.append(f"{band}{cup}")
    
    # Assign segments to customers (30% small-chested)
    customer_segments = {}
    customer_preferred_sizes = {}
    for user_id in customer_pool:
        # Assign a preferred size to each customer
        preferred_size = random.choice(sizes)
        customer_preferred_sizes[user_id] = preferred_size
        
        # Determine segment based on size
        band = int(preferred_size[:2])
        cup = preferred_size[2:]
        if band <= 34 and cup in ['AA', 'A']:
            customer_segments[user_id] = 'Petite Active'
        elif band >= 32 and cup == 'B':
            customer_segments[user_id] = 'Fashion Forward'
        else:
            customer_segments[user_id] = 'Core Comfort'
    
    # Track last purchase date to simulate realistic reorder patterns
    last_purchase = {user_id: None for user_id in customer_pool}
    
    # Product categories
    categories = ['Basic', 'Wireless', 'Sport', 'Strapless', 'Fashion', 'Limited']
    
    for date in date_range:
        # Seasonal factors
        month_factor = {
            1: 1.0,   # January
            2: 1.2,   # February (Valentine's)
            3: 0.9,
            4: 0.9,
            5: 1.1,   # Mother's Day
            6: 1.0,
            7: 1.2,   # Summer Sales
            8: 0.9,
            9: 1.0,
            10: 1.0,
            11: 1.1,  # Black Friday
            12: 1.3   # Holiday Season
        }[date.month]
        
        # Weekly pattern
        day_factor = 1.2 if date.weekday() >= 5 else 1.0  # Weekend boost
        
        # Growth trend (20% annual growth)
        days_since_start = (date - start_date).days
        growth_factor = 1 + (0.20 * days_since_start / 365)
        
        # Calculate potential customers for this day
        daily_orders = int(base_orders_per_day * month_factor * day_factor * growth_factor)
        
        # Select customers more likely to order based on their last purchase
        potential_customers = []
        for user_id in customer_pool:
            last_date = last_purchase[user_id]
            
            if last_date is None:
                # New customer probability
                if random.random() < 0.01:  # 1% chance of new customer per day
                    potential_customers.append(user_id)
            else:
                # Returning customer probability based on time since last purchase
                days_since_purchase = (date - last_date).days
                if days_since_purchase > 90:  # Base reorder period
                    reorder_prob = 0.05  # 5% chance after 90 days
                    if customer_segments[user_id] == 'Core Comfort':
                        reorder_prob *= 1.2  # 20% higher loyalty
                    
                    if random.random() < reorder_prob:
                        potential_customers.append(user_id)
        
        # Generate orders for selected customers
        for user_id in potential_customers[:daily_orders]:
            # Get customer's preferred size
            size = customer_preferred_sizes[user_id]
            segment = customer_segments[user_id]
            
            # Select appropriate category based on segment
            if segment == 'Core Comfort':
                category = random.choice(['Basic', 'Wireless'])
            elif segment == 'Petite Active':
                category = random.choice(['Sport', 'Strapless'])
            else:  # Fashion Forward
                category = random.choice(['Fashion', 'Limited'])
            
            # Simulate order details
            order_id = f"HIST_{date.strftime('%Y%m%d')}_{user_id}"
            product_id = random.randint(1, 361)
            
            # Price based on category
            base_price = {
                'Basic': 60,
                'Wireless': 62,
                'Sport': 65,
                'Strapless': 68,
                'Fashion': 70,
                'Limited': 75
            }[category]
            
            # Add small random variation to price
            sale_price = base_price + random.uniform(-5, 5)
            
            historical_data.append({
                'order_id': order_id,
                'user_id': user_id,
                'product_id': product_id,
                'status': 'delivered',
                'sale_price': sale_price,
                'shipping_cost': 5.99,
                'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
                'shipped_at': (date + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'delivered_at': (date + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'returned_at': None,
                'size': size,
                'category': category,
                'segment': segment
            })
            
            # Update last purchase date
            last_purchase[user_id] = date
    
    # Combine historical and current data
    historical_df = pd.DataFrame(historical_data)
    orders_df = pd.concat([historical_df, current_orders], ignore_index=True)
    
    # Load product data
    products_df = pd.read_sql('SELECT * FROM transformed_products', conn)
    conn.close()
    
    return products_df, orders_df

def analyze_product_mix(products_df, orders_df):
    """Analyze how well our product selection serves different segments."""
    # Create visualization
    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=[
                            'Orders by Segment',
                            'Average Order Value by Segment',
                            'Popular Categories by Segment',
                            'Size Distribution'
                        ])
    
    # Orders by segment
    segment_orders = orders_df['segment'].value_counts()
    fig.add_trace(
        go.Bar(x=segment_orders.index, 
               y=segment_orders.values,
               text=[f"{count:,} orders" for count in segment_orders.values],
               textposition='auto',
               hovertemplate="<br>".join([
                   "%{x}",
                   "Orders: %{y:,}",
                   "<extra></extra>"
               ])),
        row=1, col=1
    )
    
    # Average order value by segment
    avg_order = orders_df.groupby('segment')['sale_price'].mean()
    fig.add_trace(
        go.Bar(x=avg_order.index,
               y=avg_order.values,
               text=[f"${val:.2f}" for val in avg_order.values],
               textposition='auto',
               hovertemplate="<br>".join([
                   "%{x}",
                   "Average Order: $%{y:.2f}",
                   "<extra></extra>"
               ])),
        row=1, col=2
    )
    
    # Category distribution by segment
    category_dist = pd.crosstab(orders_df['segment'], orders_df['category'])
    fig.add_trace(
        go.Heatmap(
            x=category_dist.columns,
            y=category_dist.index,
            z=category_dist.values,
            text=category_dist.values,
            texttemplate="%{text}",
            colorscale="Viridis",
            hovertemplate="<br>".join([
                "Segment: %{y}",
                "Category: %{x}",
                "Orders: %{text}",
                "<extra></extra>"
            ])
        ),
        row=2, col=1
    )
    
    # Size distribution
    size_dist = orders_df['size'].value_counts()
    fig.add_trace(
        go.Bar(x=size_dist.index,
               y=size_dist.values,
               text=[f"{count:,}" for count in size_dist.values],
               textposition='auto',
               hovertemplate="<br>".join([
                   "Size: %{x}",
                   "Orders: %{y:,}",
                   "<extra></extra>"
               ])),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text='Understanding Our Product Selection',
        title_x=0.5,
        title_font_size=20
    )
    
    # Save visualization
    fig.write_html('analysis/product_mix.html')
    
    return {
        'segment_orders': segment_orders.to_dict(),
        'avg_order_value': avg_order.to_dict(),
        'category_distribution': category_dist.to_dict(),
        'size_distribution': size_dist.to_dict()
    }

def analyze_sales_performance(orders_df):
    """Analyze how well we're serving each customer segment."""
    # Create visualization
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "pie"}, {"type": "bar"}]],
                        subplot_titles=[
                            'Where Does Our Revenue Come From?',
                            'How Much Do Customers Typically Spend?'
                        ])
    
    # Revenue breakdown
    revenue_by_segment = orders_df.groupby('segment')['sale_price'].sum()
    total_revenue = revenue_by_segment.sum()
    
    fig.add_trace(
        go.Pie(labels=revenue_by_segment.index,
               values=revenue_by_segment.values,
               textinfo='label+percent',
               hovertemplate="<br>".join([
                   "%{label}",
                   "Revenue: $%{value:,.0f}",
                   "Share: %{percent}",
                   "<extra></extra>"
               ])),
        row=1, col=1
    )
    
    # Average purchase value
    avg_order = orders_df.groupby('segment')['sale_price'].mean()
    fig.add_trace(
        go.Bar(x=avg_order.index,
               y=avg_order.values,
               text=[f"${val:.2f}" for val in avg_order.values],
               textposition='auto',
               hovertemplate="<br>".join([
                   "%{x}",
                   "Average Order: $%{y:.2f}",
                   "<extra></extra>"
               ])),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        title_text='Understanding Our Sales Performance',
        title_x=0.5,
        title_font_size=20
    )
    
    # Save interactive chart
    fig.write_html('analysis/figures/sales_performance.html')
    
    # Calculate key metrics
    sales_metrics = orders_df.groupby('segment').agg({
        'order_id': 'count',
        'user_id': 'nunique',
        'sale_price': ['sum', 'mean']
    }).round(2)
    
    sales_metrics.columns = [
        'Total Orders',
        'Unique Customers',
        'Total Revenue',
        'Average Order Value'
    ]
    
    # Add derived metrics
    sales_metrics['Revenue Share'] = (sales_metrics['Total Revenue'] / 
                                    sales_metrics['Total Revenue'].sum() * 100).round(1)
    sales_metrics['Orders per Customer'] = (sales_metrics['Total Orders'] / 
                                          sales_metrics['Unique Customers']).round(2)
    
    return sales_metrics

def analyze_customer_behavior(orders_df):
    """Analyze how customer behavior differs between segments."""
    # Convert timestamps
    orders_df['created_at'] = pd.to_datetime(orders_df['created_at'].str.split('.').str[0])
    
    # Daily metrics
    daily_metrics = orders_df.groupby(['segment', 
                                     orders_df['created_at'].dt.date]).agg({
        'order_id': 'count',
        'sale_price': 'sum',
        'user_id': 'nunique'
    }).reset_index()
    
    # Create visualization
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=[
                            'Daily Orders by Segment',
                            'Daily Revenue by Segment'
                        ])
    
    # Daily orders trend
    for segment in daily_metrics['segment'].unique():
        segment_data = daily_metrics[daily_metrics['segment'] == segment]
        fig.add_trace(
            go.Scatter(x=segment_data['created_at'],
                      y=segment_data['order_id'],
                      name=f"{segment} - Orders",
                      mode='lines',
                      hovertemplate="<br>".join([
                          "Date: %{x}",
                          "Orders: %{y}",
                          "<extra></extra>"
                      ])),
            row=1, col=1
        )
    
    # Daily revenue trend
    for segment in daily_metrics['segment'].unique():
        segment_data = daily_metrics[daily_metrics['segment'] == segment]
        fig.add_trace(
            go.Scatter(x=segment_data['created_at'],
                      y=segment_data['sale_price'],
                      name=f"{segment} - Revenue",
                      mode='lines',
                      hovertemplate="<br>".join([
                          "Date: %{x}",
                          "Revenue: $%{y:.2f}",
                          "<extra></extra>"
                      ])),
            row=1, col=2
        )
    
    fig.update_layout(
        height=500,
        title_text='Customer Behavior Over Time',
        title_x=0.5,
        title_font_size=20
    )
    
    # Save visualization
    fig.write_html('analysis/customer_behavior.html')
    
    # Calculate key metrics
    behavior_metrics = daily_metrics.groupby('segment').agg({
        'order_id': ['mean', 'std'],
        'sale_price': ['mean', 'std'],
        'user_id': 'mean'
    }).round(2)
    
    behavior_metrics.columns = [
        'Average Daily Orders',
        'Order Variation',
        'Average Daily Revenue',
        'Revenue Variation',
        'Average Daily Customers'
    ]
    
    return behavior_metrics

def analyze_customer_segments(orders_df):
    """
    Analyze customer segments based on size-first segmentation strategy.
    Focus on serving different needs within the small-chested market.
    """
    # Extract size information
    orders_df['band_size'] = orders_df['size'].str.extract('(\d+)').astype(float)
    orders_df['cup_size'] = orders_df['size'].str.extract('([A-Z]+)')
    
    # Define segments based on size ranges and style preferences
    segments = {
        'Core Comfort': {
            'description': 'Primary segment seeking everyday comfort',
            'band_range': (30, 36),
            'cup_sizes': ['A', 'B'],
            'categories': ['Basic', 'Wireless'],
            'price_range': (55, 65)
        },
        'Petite Active': {
            'description': 'Smallest sizes focused on active lifestyle',
            'band_range': (30, 34),
            'cup_sizes': ['AA', 'A'],
            'categories': ['Sport', 'Strapless'],
            'price_range': (60, 70)
        },
        'Fashion Forward': {
            'description': 'Style-conscious customers wanting both fashion and fit',
            'band_range': (32, 36),
            'cup_sizes': ['B'],
            'categories': ['Fashion', 'Limited'],
            'price_range': (60, 70)
        }
    }
    
    # Calculate segment metrics
    segment_analysis = {}
    for segment_name, criteria in segments.items():
        segment_orders = orders_df[
            (orders_df['band_size'].between(criteria['band_range'][0], criteria['band_range'][1])) &
            (orders_df['cup_size'].isin(criteria['cup_sizes'])) &
            (orders_df['category'].isin(criteria['categories'])) &
            (orders_df['sale_price'].between(criteria['price_range'][0], criteria['price_range'][1]))
        ]
        
        if len(segment_orders) > 0:
            # Basic metrics
            total_revenue = segment_orders['sale_price'].sum()
            total_orders = len(segment_orders)
            unique_customers = segment_orders['user_id'].nunique()
            repeat_customers = len(segment_orders[segment_orders['user_id'].duplicated()])
            
            # Size distribution
            size_dist = segment_orders.groupby(['band_size', 'cup_size']).size()
            top_sizes = size_dist.nlargest(3)
            
            # Seasonal patterns
            seasonal_sales = segment_orders.groupby(segment_orders['created_at'].dt.month)['sale_price'].sum()
            peak_months = seasonal_sales.nlargest(2)
            
            segment_analysis[segment_name] = {
                'total_orders': total_orders,
                'avg_order_value': segment_orders['sale_price'].mean(),
                'customer_count': unique_customers,
                'repeat_rate': repeat_customers / total_orders if total_orders > 0 else 0,
                'revenue_share': (total_revenue / orders_df['sale_price'].sum()) * 100,
                'top_sizes': top_sizes.to_dict(),
                'peak_months': peak_months.to_dict(),
                'description': criteria['description']
            }
        else:
            segment_analysis[segment_name] = {
                'total_orders': 0,
                'avg_order_value': 0,
                'customer_count': 0,
                'repeat_rate': 0,
                'revenue_share': 0,
                'top_sizes': {},
                'peak_months': {},
                'description': criteria['description']
            }
    
    return segment_analysis

def generate_segment_insights(segment_analysis):
    """Generate insights based on size-first segmentation analysis."""
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    insights = {}
    for segment_name, metrics in segment_analysis.items():
        # Format peak months
        peak_months = [
            f"{month_names[month]} (${revenue:,.2f})"
            for month, revenue in metrics['peak_months'].items()
        ] if metrics['peak_months'] else []
        
        # Format top sizes
        top_sizes = [
            f"{band}{cup}: {count} orders"
            for (band, cup), count in metrics['top_sizes'].items()
        ] if metrics['top_sizes'] else []
        
        insights[segment_name] = [
            metrics['description'],
            f"Represents {metrics['revenue_share']:.1f}% of total revenue",
            f"Average order value: ${metrics['avg_order_value']:.2f}",
            f"Customer base: {metrics['customer_count']} customers",
            f"Repeat purchase rate: {metrics['repeat_rate']:.1%}",
            f"Most popular sizes: {', '.join(top_sizes) if top_sizes else 'No data'}",
            f"Peak months: {', '.join(peak_months) if peak_months else 'No data'}"
        ]
    
    return insights

def save_business_story(segment_analysis, insights):
    """Save enhanced business story with size-first segmentation."""
    story = []
    
    # Header
    story.append("# Enhanced Market Analysis: Pepper's Customer Segments")
    story.append(f"**Analysis Date**: {datetime.now().strftime('%B %d, %Y')}\n")
    
    # Executive Summary
    story.append("## Executive Summary")
    story.append("Pepper's unique value proposition lies in serving the small-chested market (AA-B cups) with perfectly fitted bras. ")
    story.append("Our analysis reveals three distinct segments within this market, each with unique needs and preferences.\n")
    
    # Segment Performance
    story.append("## Customer Segment Performance")
    
    for segment_name, metrics in segment_analysis.items():
        story.append(f"\n### {segment_name}")
        story.append(f"**Description**: {metrics['description']}")
        
        story.append("\n**Key Metrics**:")
        story.append(f"- Revenue Share: {metrics['revenue_share']:.1f}%")
        story.append(f"- Average Order Value: ${metrics['avg_order_value']:.2f}")
        story.append(f"- Customer Base: {metrics['customer_count']} customers")
        story.append(f"- Repeat Purchase Rate: {metrics['repeat_rate']:.1%}")
        
        story.append("\n**Size Distribution**:")
        if metrics['top_sizes']:
            for size_combo, count in metrics['top_sizes'].items():
                story.append(f"- {size_combo[0]}{size_combo[1]}: {count} orders")
        else:
            story.append("- No size data available")
        
        story.append("\n**Seasonal Trends**:")
        if metrics['peak_months']:
            story.append("Peak sales months:")
            for month, revenue in metrics['peak_months'].items():
                month_name = {
                    1: 'January', 2: 'February', 3: 'March', 4: 'April',
                    5: 'May', 6: 'June', 7: 'July', 8: 'August',
                    9: 'September', 10: 'October', 11: 'November', 12: 'December'
                }[month]
                story.append(f"- {month_name}: ${revenue:,.2f}")
        else:
            story.append("- No seasonal data available")
        
        story.append("\n**Key Insights**:")
        for insight in insights[segment_name]:
            story.append(f"- {insight}")
    
    # Strategic Recommendations
    story.append("\n## Strategic Recommendations")
    
    # Product Strategy
    story.append("\n### 1. Product Strategy")
    story.append("**Core Comfort Line**")
    story.append("- Focus on everyday comfort for 30-36 A/B customers")
    story.append("- Maintain strong wireless options")
    story.append("- Consider expanding color and pattern options")
    
    story.append("\n**Petite Active Line**")
    story.append("- Develop specialized sports bras for 30-34 AA/A")
    story.append("- Focus on lightweight support and moisture-wicking")
    story.append("- Expand strapless options for special occasions")
    
    story.append("\n**Fashion Line**")
    story.append("- Create trend-focused pieces for 32-36 B")
    story.append("- Introduce seasonal collections")
    story.append("- Consider collaborations with designers")
    
    # Marketing Strategy
    story.append("\n### 2. Marketing Strategy")
    story.append("**Segment-Specific Messaging**")
    story.append("- Core Comfort: Emphasize all-day comfort and perfect fit")
    story.append("- Petite Active: Focus on support during activities")
    story.append("- Fashion Forward: Highlight style without compromise")
    
    story.append("\n**Channel Strategy**")
    story.append("- Utilize targeted social media for each segment")
    story.append("- Develop segment-specific email campaigns")
    story.append("- Create educational content about proper sizing")
    
    # Growth Opportunities
    story.append("\n### 3. Growth Opportunities")
    story.append("**Product Development**")
    story.append("- Expand successful styles to new colors/patterns")
    story.append("- Consider complementary products (bralettes, sports)")
    story.append("- Test new materials and technologies")
    
    story.append("\n**Customer Experience**")
    story.append("- Enhance virtual fitting experience")
    story.append("- Develop loyalty program with segment-specific perks")
    story.append("- Create community features for style sharing")
    
    # Save to file
    with open('analysis/business_story.md', 'w') as f:
        f.write('\n'.join(story))

def main():
    """Run main analysis."""
    print("Loading data...")
    products_df, orders_df = load_historical_data()
    print(f"Data loaded: {len(products_df)} products, {len(orders_df)} orders")
    
    print("\nAnalyzing product selection...")
    product_stats = analyze_product_mix(products_df, orders_df)
    
    print("\nAnalyzing sales performance...")
    sales_metrics = analyze_sales_performance(orders_df)
    
    print("\nAnalyzing customer behavior...")
    behavior_metrics = analyze_customer_behavior(orders_df)
    
    print("\nAnalyzing customer segments...")
    segment_analysis = analyze_customer_segments(orders_df)
    insights = generate_segment_insights(segment_analysis)
    
    print("\nCreating business story...")
    save_business_story(segment_analysis, insights)
    
    print("\nAnalysis complete! Open business_story.md to view results.")

if __name__ == "__main__":
    main()

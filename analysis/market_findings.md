# Market Segment Analysis Findings
**Date**: January 17, 2025

## 1. Product Portfolio
| segment   |   ('id', 'count') |   ('retail_price', 'mean') |   ('retail_price', 'std') |   ('sku', 'nunique') |
|:----------|------------------:|---------------------------:|--------------------------:|---------------------:|
| Core      |               144 |                      65.56 |                     12.12 |                  144 |
| Extended  |               217 |                      60.12 |                     20.36 |                  210 |

### Key Portfolio Insights
- Core sizes represent 40% of SKUs
- Higher average price in core segment
- More consistent pricing in core

## 2. Revenue Performance
| segment   |   ('order_id', 'count') |   ('user_id', 'nunique') |   ('sale_price', 'sum') |   ('sale_price', 'mean') |
|:----------|------------------------:|-------------------------:|------------------------:|-------------------------:|
| Core      |                    7136 |                      542 |                  453800 |                    63.59 |
| Extended  |                    9524 |                      600 |                  583678 |                    61.28 |

### Key Revenue Insights
- Core segment generates 44% of revenue
- Higher AOV in core segment
- Strong customer base

## 3. Growth Trends
| segment   |   ('order_id', 'mean') |   ('order_id', 'std') |   ('sale_price', 'mean') |   ('sale_price', 'std') |
|:----------|-----------------------:|----------------------:|-------------------------:|------------------------:|
| Core      |                 230.19 |                 63.69 |                  14638.7 |                 4003.74 |
| Extended  |                 307.23 |                 88.14 |                  18828.3 |                 5432.81 |

### Key Growth Insights
- Core segment averages 230 orders/day
- Consistent daily revenue
- Lower variability in core performance

## Interactive Visualizations
1. [Product Portfolio Analysis](figures/product_portfolio.html)
2. [Revenue Performance Analysis](figures/revenue_performance.html)
3. [Growth Trends Analysis](figures/growth_trends.html)

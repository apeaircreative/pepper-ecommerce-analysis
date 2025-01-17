# Return Tracking and KPI System Specification
**Date**: January 17, 2025  
**Author**: Aaliyah Johnson  
**Project**: Pepper Market Segmentation

## 1. Return Tracking System

### Data Schema
```sql
CREATE TABLE return_tracking (
    return_id TEXT PRIMARY KEY,
    order_id TEXT,
    product_id TEXT,
    user_id TEXT,
    original_order_date DATE,
    return_initiated_date DATE,
    return_received_date DATE,
    return_reason TEXT,
    size_returned TEXT,
    condition_rating INTEGER,
    refund_amount DECIMAL(10,2),
    exchange_requested BOOLEAN,
    new_size_requested TEXT,
    status TEXT,
    notes TEXT
);
```

### Return Reasons
1. Size Issues
   - Too small
   - Too large
   - Band too tight/loose
   - Cup too small/large

2. Style Issues
   - Color not as expected
   - Style different from photos
   - Material concerns
   - Design preferences

3. Quality Issues
   - Manufacturing defect
   - Damage on arrival
   - Wear after use
   - Material quality

### Status Workflow
1. Initiated
2. Return Label Generated
3. In Transit
4. Received
5. Inspected
6. Refunded/Exchanged
7. Completed

## 2. Segment-Specific KPIs

### Customer Acquisition
1. **New Customer Rate**
   ```sql
   SELECT 
       segment,
       COUNT(DISTINCT CASE WHEN is_first_purchase THEN user_id END) as new_customers,
       COUNT(DISTINCT user_id) as total_customers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN is_first_purchase THEN user_id END) / 
             COUNT(DISTINCT user_id), 2) as new_customer_rate
   FROM customer_orders
   GROUP BY segment;
   ```

2. **Customer Acquisition Cost (CAC)**
   ```sql
   SELECT 
       segment,
       SUM(marketing_spend) as total_spend,
       COUNT(DISTINCT CASE WHEN is_first_purchase THEN user_id END) as new_customers,
       ROUND(SUM(marketing_spend) / 
             COUNT(DISTINCT CASE WHEN is_first_purchase THEN user_id END), 2) as cac
   FROM marketing_spend
   GROUP BY segment;
   ```

### Customer Retention
1. **30-Day Retention Rate**
   ```sql
   WITH cohorts AS (
       SELECT 
           user_id,
           segment,
           MIN(order_date) as first_order,
           MAX(order_date) as last_order
       FROM customer_orders
       GROUP BY user_id, segment
   )
   SELECT 
       segment,
       COUNT(DISTINCT user_id) as cohort_size,
       COUNT(DISTINCT CASE WHEN DATEDIFF(last_order, first_order) >= 30 THEN user_id END) as retained,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN DATEDIFF(last_order, first_order) >= 30 THEN user_id END) /
             COUNT(DISTINCT user_id), 2) as retention_rate
   FROM cohorts
   GROUP BY segment;
   ```

2. **Repeat Purchase Rate**
   ```sql
   SELECT 
       segment,
       COUNT(DISTINCT user_id) as customers,
       COUNT(DISTINCT CASE WHEN order_count > 1 THEN user_id END) as repeat_customers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN order_count > 1 THEN user_id END) /
             COUNT(DISTINCT user_id), 2) as repeat_rate
   FROM customer_orders
   GROUP BY segment;
   ```

### Product Performance
1. **Return Rate**
   ```sql
   SELECT 
       segment,
       COUNT(DISTINCT order_id) as orders,
       COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END) as returns,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END) /
             COUNT(DISTINCT order_id), 2) as return_rate
   FROM order_tracking
   GROUP BY segment;
   ```

2. **Size Satisfaction**
   ```sql
   SELECT 
       segment,
       size,
       COUNT(DISTINCT order_id) as orders,
       COUNT(DISTINCT CASE WHEN return_reason LIKE '%size%' THEN order_id END) as size_issues,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN return_reason LIKE '%size%' THEN order_id END) /
             COUNT(DISTINCT order_id), 2) as size_issue_rate
   FROM order_tracking
   JOIN return_tracking USING (order_id)
   GROUP BY segment, size;
   ```

### Revenue Metrics
1. **Average Order Value (AOV)**
   ```sql
   SELECT 
       segment,
       COUNT(DISTINCT order_id) as orders,
       ROUND(SUM(sale_price), 2) as revenue,
       ROUND(SUM(sale_price) / COUNT(DISTINCT order_id), 2) as aov
   FROM order_tracking
   GROUP BY segment;
   ```

2. **Customer Lifetime Value (CLV)**
   ```sql
   SELECT 
       segment,
       COUNT(DISTINCT user_id) as customers,
       ROUND(SUM(sale_price), 2) as total_revenue,
       ROUND(SUM(sale_price) / COUNT(DISTINCT user_id), 2) as clv
   FROM order_tracking
   GROUP BY segment;
   ```

## 3. Implementation Plan

### Phase 1: Data Collection (Week 1-2)
1. Set up return tracking table
2. Implement return workflow
3. Begin collecting return reasons

### Phase 2: KPI Implementation (Week 2-3)
1. Create KPI views
2. Set up automated reporting
3. Validate metrics

### Phase 3: Dashboard Creation (Week 3-4)
1. Design segment dashboards
2. Implement automated updates
3. Create stakeholder views

### Phase 4: Analysis & Optimization (Week 4+)
1. Analyze initial data
2. Identify improvement areas
3. Refine metrics

## 4. Success Metrics

### Implementation Success
- 100% return tracking coverage
- All KPIs reporting accurately
- Automated daily updates

### Business Impact
- Reduced return rates
- Improved customer satisfaction
- Better inventory planning

## 5. Next Steps
1. Review spec with stakeholders
2. Set up development environment
3. Begin Phase 1 implementation

---
*Note: This is a living document that will be updated based on stakeholder feedback and implementation learnings.*

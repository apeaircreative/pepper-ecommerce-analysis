# Development Log

## Project Timeline

### Phase 1: Initial Setup and TheLook Integration
1. Created project structure and environment
2. Set up BigQuery connection
3. Created transformation scripts for TheLook data
4. Implemented schema verification
5. Created unified views for customer and order data

### Phase 2: Olist Integration
#### 2024-01-16
1. **Data Source Setup**
   - Set up Kaggle API authentication 
   - Downloaded core datasets successfully 
   - Data volumes:
     * Customers: 99,441 records
     * Orders: 99,441 records
     * Order Items: 112,650 records
     * Products: 32,951 records

2. **Initial Data Analysis**
   - Date range: Sept 2016 - Oct 2018
   - Average items per order: 1.13 (112,650/99,441)
   - 100% customer-order match (99,441 each)
   - Product catalog: 32,951 unique products

3. **Data Quality Notes**
   - Some BigQuery verification queries failed - need to adjust SQL
   - All core files loaded successfully
   - Clean customer-order relationship (1:1 mapping)
   - No missing core files

#### Next Steps
1. **Fix BigQuery Verification**
   - Adjust SQL queries for Olist schema
   - Add proper timestamp handling
   - Verify all table loads

2. **Schema Integration**
   - Create unified views combining TheLook and Olist
   - Handle platform-specific fields
   - Standardize date formats

3. **Analysis Preparation**
   - Create comparison queries
   - Set up customer segmentation
   - Prepare cohort analysis

## Technical Decisions

### Data Storage
- Using BigQuery views instead of tables for:
  * Cost efficiency (free tier)
  * Real-time data access
  * Flexible schema modifications

### Security
- Implemented .gitignore for sensitive files
- Set up proper API credential management
- Using environment variables for configurations

### Code Organization
- Separate scripts for different pipeline stages
- Documentation in markdown format
- Version control with signed commits

## Challenges and Solutions

### TheLook Integration
- Challenge: Field name mismatches
- Solution: Created unified schema with proper mappings

### Olist Integration
- Challenge: Different data structure
- Solution: Created mapping documentation
- Challenge: Missing fields (e.g., customer demographics)
- Solution: Using NULL values with proper documentation

## Data Quality Findings (Jan 16, 2025)

#### Volume Analysis
- **Time Range**: Sept 2016 - Oct 2018 (634 unique days)
- **Scale**:
  * 99,441 unique customers
  * 99,441 unique orders
  * 32,951 unique products
  * 112,650 order items

#### Key Metrics
1. **Order Patterns**:
   - Average order value: $275.51
   - Orders per customer: Exactly 1 (interesting pattern)
   - Products per customer: 1.03 avg (max 8)

2. **Data Completeness**:
   - Missing delivery dates: 5,930 orders (2.98%)
   - Missing carrier dates: 3,566 orders (1.79%)
   - Missing approval timestamps: 320 orders (0.16%)
   - All estimated delivery dates present

3. **Order Status Distribution**:
   - Delivered: 97.02%
   - In-transit (shipped): 1.11%
   - Canceled/Unavailable: 1.24%
   - Other statuses: <1%

#### Data Quality Issues
1. **Duplicate Investigation Required**:
   - Customer table shows 198,882 rows but 99,441 unique IDs
   - Orders table shows similar pattern
   - Possible data duplication or denormalization

2. **Delivery Pipeline**:
   - Small percentage of undelivered orders (2.98%)
   - Very few orders in processing state (0.30%)
   - Clean progression through order states

#### Integration Considerations
1. **Customer Behavior**:
   - Single order per customer pattern differs from typical e-commerce
   - May affect cohort analysis approach
   - Need to investigate if this is by design or data issue

2. **Next Steps**:
   - Investigate customer/order table duplication
   - Add data quality checks in transformation pipeline
   - Consider handling of missing delivery dates
   - Design unified schema accounting for single-order pattern

## Duplication Investigation Findings (Jan 16, 2025)

#### Key Findings
1. **Customer Records**:
   - 96,096 customers (96.6%) have duplicate records
   - Each customer has 1-17 duplicate IDs (avg: 1.03)
   - Most duplicates are exact copies (same city/state)

2. **Order Patterns**:
   - Same order appears multiple times for same customer
   - Order timestamps are identical across duplicates
   - Clear case of data denormalization, not actual duplicate orders

3. **Location Analysis**:
   - Only 122 customers have multiple locations
   - Most have 2 locations, max is 3
   - Likely represents customer moves/multiple addresses

#### Root Cause Analysis
1. **Data Structure Issue**:
   - Tables appear to be denormalized exports
   - Each customer-order combination creates duplicate customer records
   - Not a data quality issue, but a storage design choice

2. **Impact Assessment**:
   - No data loss risk from deduplication
   - Need to preserve customer location history
   - Can safely deduplicate using customer_unique_id

#### Solution Strategy
1. **Create Cleaned Views**:
   ```sql
   -- Base customer view
   CREATE OR REPLACE VIEW `pepper-analytics-2024.transformed_data.vw_customers_clean` AS
   SELECT DISTINCT
       customer_unique_id,
       FIRST_VALUE(customer_id) OVER(PARTITION BY customer_unique_id ORDER BY customer_id) as customer_id,
       customer_city,
       customer_state
   FROM `pepper-analytics-2024.raw_data.olist_customers`;

   -- Base order view
   CREATE OR REPLACE VIEW `pepper-analytics-2024.transformed_data.vw_orders_clean` AS
   SELECT DISTINCT
       o.order_id,
       c.customer_unique_id,
       o.order_status,
       o.order_purchase_timestamp,
       o.order_approved_at,
       o.order_delivered_carrier_date,
       o.order_delivered_customer_date,
       o.order_estimated_delivery_date
   FROM `pepper-analytics-2024.raw_data.olist_orders` o
   JOIN `pepper-analytics-2024.transformed_data.vw_customers_clean` c
   ON o.customer_id = c.customer_id;
   ```

2. **Next Steps**:
   - Create cleaned views 
   - Add data quality metrics to pipeline
   - Document deduplication logic
   - Update integration strategy for TheLook

## Best Practices Implemented
1. Data Quality Checks
2. Modular Code Structure
3. Comprehensive Documentation
4. Security First Approach
5. Version Control
6. Incremental Development

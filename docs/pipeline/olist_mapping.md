# Olist to TheLook Schema Mapping

## Customer Data Mapping
| Unified Field | TheLook Field | Olist Field | Notes |
|--------------|---------------|-------------|--------|
| customer_id | id | customer_id | Olist uses different IDs per order |
| platform | 'shopify' | 'amazon' | Platform identifier |
| first_name | first_name | NULL | Not available in Olist |
| last_name | last_name | NULL | Not available in Olist |
| email | email | NULL | Not available in Olist |
| country | country | 'Brazil' | Olist is Brazil-only |
| state | state | customer_state | Direct mapping |
| city | city | customer_city | Direct mapping |
| created_at | created_at | order_purchase_timestamp | Using first order as creation |

## Order Data Mapping
| Unified Field | TheLook Field | Olist Field | Notes |
|--------------|---------------|-------------|--------|
| order_id | order_id | order_id | Direct mapping |
| customer_id | user_id | customer_id | Different naming |
| status | status | order_status | Similar values |
| created_at | created_at | order_purchase_timestamp | Direct mapping |
| total_amount | sale_price | price | Sum of items |
| shipped_at | shipped_at | order_delivered_carrier_date | Different naming |
| delivered_at | delivered_at | order_delivered_customer_date | Different naming |

## Integration Strategy
1. Load core tables first
2. Create unified views
3. Handle NULL values for missing fields
4. Standardize status values
5. Normalize timestamps

## Data Quality Considerations
1. Olist specific fields to preserve:
   - seller_id
   - product_category
   - review_scores
2. Missing customer demographics
3. Brazil-specific location data
4. Different status workflows

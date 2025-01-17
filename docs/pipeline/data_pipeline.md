# Data Pipeline Documentation

## Overview
This document describes the data transformation pipeline for the Pepper Analytics project.

## Data Sources
1. TheLook E-commerce Dataset
   - Location: `bigquery-public-data.thelook_ecommerce`
   - Tables:
     - users (100,000 records)
     - orders (124,658 records)
     - order_items (180,860 records)

## Transformed Views
1. unified_customers_view
   - Customer profile data
   - First interaction tracking
   - Acquisition source

2. unified_orders_view
   - Order details with items
   - Shipping information
   - Return tracking

3. customer_metrics_view
   - Aggregated customer metrics
   - LTV calculations
   - Return rates

## Limitations
- Using BigQuery free tier
- Views instead of materialized tables
- No scheduled refreshes
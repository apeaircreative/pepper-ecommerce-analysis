# Pepper Analytics Project

## Overview
Data analytics project for e-commerce analysis focusing on customer retention, LTV, and marketing efficiency.

## Project Structure
- `data/`: Local data files and cached datasets
- `notebooks/`: Jupyter notebooks for analysis
- `scripts/`: Python transformation scripts
- `sql/`: SQL queries for analysis
- `docs/`: Project documentation

## Setup
1. Environment setup:
   ```bash
   conda create -n pepper-analysis python=3.11
   conda activate pepper-analysis
   # Install required packages
   conda install -c conda-forge pandas numpy scikit-learn jupyter matplotlib seaborn plotly ipykernel python-dotenv google-cloud-bigquery pandas-gbq sqlalchemy pyarrow black flake8
   ```

2. Google Cloud Setup:
   - Project: pepper-analytics-2024
   - Dataset: processed_data
   - Using BigQuery free tier features

## Data Pipeline
1. Raw Data Sources:
   - TheLook E-commerce dataset (BigQuery public dataset)
   - Tables: users, orders, order_items

2. Transformed Views:
   - unified_customers_view
   - unified_orders_view
   - customer_metrics_view

## Analysis Plan
1. Cohort Retention Analysis
2. Customer LTV Modeling
3. Marketing Channel Efficiency

## Usage
See individual notebooks in `notebooks/` for specific analyses.

# Data Pipelines

This directory contains our data pipeline components:

## Structure
- `ingestion/`: Data collection and import scripts
  - `download_olist.py`: Download Olist dataset
  - `import_thelook.py`: Import TheLook sample data

- `processing/`: Data transformation scripts
  - `create_clean_views.py`: Create cleaned data views
  - `create_unified_views.py`: Unify data across platforms

- `quality/`: Data quality checks
  - `verify_olist_data.py`: Verify Olist data quality
  - `investigate_duplicates.py`: Analyze data duplication

## Usage
1. Run ingestion scripts first
2. Then processing scripts
3. Finally quality checks

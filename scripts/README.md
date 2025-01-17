# Scripts Directory Structure

## Overview
This directory contains all the Python scripts for the Pepper data analysis project.

## Directory Structure
```
scripts/
├── analysis/        # Data analysis and visualization scripts
├── data_setup/      # Dataset setup and validation scripts
├── scrapers/        # Web scraping and data collection scripts
├── tests/          # Test files for all components
└── utils/          # Utility functions and shared code
```

## Key Components

### Data Setup (`data_setup/`)
- `setup_dataset.py`: Initialize and load datasets into BigQuery
- `test_datasets.py`: Validate dataset integrity
- `check_schema.py`: Schema validation and reporting

### Scrapers (`scrapers/`)
- Shopify data collection
- Navigation validation
- Rate limiting and error handling

### Utils (`utils/`)
- Data quality validation
- Shared utilities
- Logging and configuration

### Tests (`tests/`)
- Unit tests for all components
- Integration tests
- Data validation tests

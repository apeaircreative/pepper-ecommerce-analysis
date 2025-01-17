"""
Check and validate dataset schemas.
"""
from google.cloud import bigquery
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Set

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaValidator:
    def __init__(self, project_id: str, dataset_id: str):
        """Initialize validator with project and dataset IDs."""
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        
    def get_table_schema(self, table_name: str) -> Dict:
        """Get schema for a specific table."""
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
        table = self.client.get_table(table_ref)
        
        schema = {}
        for field in table.schema:
            schema[field.name] = {
                'type': field.field_type,
                'mode': field.mode,
                'description': field.description
            }
        
        return schema
    
    def validate_required_columns(self, table_name: str, required_columns: Set[str]) -> bool:
        """Validate that a table has all required columns."""
        schema = self.get_table_schema(table_name)
        actual_columns = set(schema.keys())
        
        missing_columns = required_columns - actual_columns
        if missing_columns:
            logger.error(f"Missing required columns in {table_name}: {missing_columns}")
            return False
        
        return True
    
    def validate_column_types(self, table_name: str, expected_types: Dict[str, str]) -> bool:
        """Validate column data types."""
        schema = self.get_table_schema(table_name)
        
        type_mismatches = []
        for column, expected_type in expected_types.items():
            if column in schema:
                actual_type = schema[column]['type']
                if actual_type != expected_type:
                    type_mismatches.append(
                        f"{column}: expected {expected_type}, got {actual_type}"
                    )
        
        if type_mismatches:
            logger.error(f"Type mismatches in {table_name}: {type_mismatches}")
            return False
        
        return True
    
    def validate_data_constraints(self, table_name: str) -> bool:
        """Validate data constraints for a table."""
        constraints = {
            'olist_products_dataset': """
                product_weight_g > 0
                AND product_length_cm > 0
                AND product_height_cm > 0
                AND product_width_cm > 0
            """,
            'olist_order_items_dataset': """
                price > 0
                AND freight_value >= 0
            """
        }
        
        if table_name not in constraints:
            logger.info(f"No constraints defined for {table_name}")
            return True
        
        query = f"""
        SELECT COUNT(*) as invalid_count
        FROM `{self.project_id}.{self.dataset_id}.{table_name}`
        WHERE NOT ({constraints[table_name]})
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        row = next(results)
        
        if row.invalid_count > 0:
            logger.error(f"Found {row.invalid_count} rows violating constraints in {table_name}")
            return False
        
        return True
    
    def generate_schema_report(self) -> Dict:
        """Generate a complete schema report."""
        report = {
            'project_id': self.project_id,
            'dataset_id': self.dataset_id,
            'tables': {}
        }
        
        # Get list of tables
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        tables = list(self.client.list_tables(dataset_ref))
        
        for table in tables:
            table_id = table.table_id
            schema = self.get_table_schema(table_id)
            
            # Get row count
            query = f"""
            SELECT COUNT(*) as row_count
            FROM `{self.project_id}.{self.dataset_id}.{table_id}`
            """
            query_job = self.client.query(query)
            results = query_job.result()
            row_count = next(results).row_count
            
            report['tables'][table_id] = {
                'schema': schema,
                'row_count': row_count,
                'constraints_valid': self.validate_data_constraints(table_id)
            }
        
        return report

def main():
    """Main function to check schemas."""
    project_id = "pepper-data-analytics"  # Update with your project
    dataset_id = "olist_data"
    
    validator = SchemaValidator(project_id, dataset_id)
    
    # Define required columns for key tables
    product_columns = {
        'product_id', 'product_category_name', 'product_name_lenght',
        'product_description_lenght', 'product_photos_qty', 'product_weight_g',
        'product_length_cm', 'product_height_cm', 'product_width_cm'
    }
    
    # Validate schemas
    logger.info("Validating product table schema...")
    validator.validate_required_columns('olist_products_dataset', product_columns)
    
    # Generate complete report
    logger.info("Generating schema report...")
    report = validator.generate_schema_report()
    
    # Save report
    report_path = Path('data/schema_reports')
    report_path.mkdir(parents=True, exist_ok=True)
    
    pd.DataFrame(report).to_json(
        report_path / 'schema_report.json',
        orient='records',
        indent=2
    )
    
    logger.info("Schema validation complete")

if __name__ == "__main__":
    main()

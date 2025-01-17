"""
Analyze Pepper product data for insights.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional
import re

class ProductAnalyzer:
    def __init__(self, data_path: str):
        """
        Initialize analyzer with data path.
        
        Args:
            data_path: Path to CSV data file
        """
        self.df = pd.read_csv(data_path)
        self.clean_data()
        
    def clean_data(self):
        """Clean and prepare data for analysis."""
        # Convert price to float
        self.df['Variant Price'] = pd.to_numeric(self.df['Variant Price'], errors='coerce')
        
        # Extract product line from SKU
        self.df['Product Line'] = self.df['Variant SKU'].str[:3].map({
            'BRA': 'Zero-G',
            'ZGW': 'Zero-G',
            'SAY': 'Signature',
            'LUB': 'Lift Up'
        })
        
        # Split size into band and cup
        band_size = self.df['Option1 Value'].str.extract(r'(\d+)')
        self.df['Band Size'] = pd.to_numeric(band_size[0], errors='coerce')
        self.df['Cup Size'] = self.df['Option1 Value'].str.extract(r'([A-Z]+)')[0]
        
        # Remove rows with missing crucial data
        self.df = self.df.dropna(subset=['Band Size', 'Cup Size', 'Product Line', 'Variant Price'])
        
    def analyze_size_distribution(self) -> pd.DataFrame:
        """
        Analyze size distribution across products.
        
        Returns:
            DataFrame with size distribution
        """
        size_dist = pd.crosstab(
            [self.df['Product Line'], self.df['Band Size']], 
            self.df['Cup Size']
        )
        return size_dist
        
    def analyze_price_distribution(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze price distribution by product line.
        
        Returns:
            Dictionary with price statistics
        """
        return self.df.groupby('Product Line')['Variant Price'].agg([
            'mean', 'min', 'max', 'std'
        ]).to_dict('index')
        
    def plot_size_distribution(self, save_path: Optional[str] = None):
        """
        Plot size distribution heatmap.
        
        Args:
            save_path: Optional path to save plot
        """
        size_dist = self.analyze_size_distribution()
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(size_dist, annot=True, fmt='d', cmap='YlOrRd')
        plt.title('Size Distribution by Product Line')
        
        if save_path:
            plt.savefig(save_path)
        plt.close()
        
    def generate_report(self, output_dir: str):
        """
        Generate comprehensive analysis report.
        
        Args:
            output_dir: Directory to save report files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Size distribution
        size_dist = self.analyze_size_distribution()
        size_dist.to_csv(output_path / 'size_distribution.csv')
        self.plot_size_distribution(output_path / 'size_distribution.png')
        
        # Price analysis
        price_analysis = pd.DataFrame.from_dict(
            self.analyze_price_distribution(), 
            orient='index'
        )
        price_analysis.to_csv(output_path / 'price_analysis.csv')
        
        # Generate summary report
        with open(output_path / 'analysis_summary.md', 'w') as f:
            f.write('# Pepper Product Analysis Summary\n\n')
            
            f.write('## Product Lines\n')
            product_counts = self.df['Product Line'].value_counts()
            for line, count in product_counts.items():
                f.write(f'- {line}: {count} variants\n')
            
            f.write('\n## Size Range\n')
            f.write(f'- Band sizes: {self.df["Band Size"].min()}-{self.df["Band Size"].max()}\n')
            f.write(f'- Cup sizes: {", ".join(sorted(self.df["Cup Size"].unique()))}\n')
            
            f.write('\n## Price Analysis\n')
            for line, stats in self.analyze_price_distribution().items():
                f.write(f'\n### {line}\n')
                f.write(f'- Average price: ${stats["mean"]:.2f}\n')
                f.write(f'- Price range: ${stats["min"]:.2f}-${stats["max"]:.2f}\n')

if __name__ == '__main__':
    # Example usage
    analyzer = ProductAnalyzer('data/external/pepper/koala_inspector/csv_exports/All Products Jan 17 2025.csv')
    analyzer.generate_report('docs/analysis/product_analysis')

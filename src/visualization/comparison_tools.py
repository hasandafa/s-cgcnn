"""
Comparison Tools Module
=======================

Analysis and comparison utilities for AlₓGa₁₋ₓAs data.
Supports:
    - Statistical analysis
    - Data source comparison
    - Property correlations
    - Device-relevant composition identification
    - Quality metrics

Author: Abdullah Hasan Dafa
Version: 0.2
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from ..utils.logger_config import setup_logger

logger = setup_logger(__name__)


class ComparisonTools:
    """
    Analysis tools for AlₓGa₁₋ₓAs property comparisons.
    
    Attributes:
        data (pd.DataFrame): Property data
        
    Example:
        >>> tools = ComparisonTools()
        >>> tools.load_data('data/structures/metadata/')
        >>> stats = tools.calculate_statistics()
        >>> print(stats)
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize ComparisonTools.
        
        Args:
            data_dir: Root directory containing metadata
        """
        self.data_dir = Path(data_dir) if data_dir else Path('data')
        self.data: Optional[pd.DataFrame] = None
        
        logger.info("ComparisonTools initialized")
    
    def load_data(self, metadata_dir: Optional[str] = None) -> pd.DataFrame:
        """
        Load property data from JSON metadata files.
        
        Args:
            metadata_dir: Path to metadata directory
            
        Returns:
            DataFrame with all properties
        """
        if metadata_dir is None:
            metadata_dir = self.data_dir / 'structures' / 'metadata'
        else:
            metadata_dir = Path(metadata_dir)
        
        # Load JSON files
        json_files = sorted(metadata_dir.glob('*.json'))
        data_list = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    meta = json.load(f)
                
                # Extract composition (handle multiple JSON formats)
                x = None
                if isinstance(meta, dict):
                    # FIX: Try x_value first (v0.1.1 format)
                    if 'x_value' in meta:
                        x = meta['x_value']
                    # Try nested 'composition' dict
                    elif 'composition' in meta and isinstance(meta['composition'], dict):
                        x = meta['composition'].get('x')
                    # Try direct 'x' key
                    elif 'x' in meta:
                        x = meta['x']
                    # Try extracting from filename as fallback
                    if x is None:
                        stem = json_file.stem
                        if '_x_' in stem:
                            x_part = stem.split('_x_')[1]
                            x = float(x_part.replace('_', '.'))

                if x is None:
                    continue
                
                # FIX: Extract properties from nested 'properties' dict (v0.1.1 format)
                props = meta.get('properties', {})
                
                row = {
                    'x': x,
                    'formula': meta.get('formula', ''),
                    'band_gap': props.get('band_gap', np.nan),  # FIX: Direct access
                    'band_gap_type': props.get('band_gap_type', ''),  # FIX: Direct access
                    'lattice_constant': props.get('lattice_constant', np.nan),  # FIX: Direct access
                    'density': props.get('density', np.nan),  # FIX: From props
                    'data_source': meta.get('data_source', ''),
                }
                
                # Add all optional properties from the properties dict
                # This preserves the original update() behavior but with correct source
                additional_props = [
                    'bulk_modulus', 'shear_modulus', 'thermal_conductivity',
                    'refractive_index', 'electron_mobility', 'hole_mobility',
                    'band_gap_direct', 'band_gap_indirect_X', 'electron_affinity',
                    'electron_effective_mass', 'hole_effective_mass_heavy',
                    'static_dielectric', 'optical_dielectric', 'elastic_c11',
                    'elastic_c12', 'elastic_c44', 'thermal_expansion',
                    'specific_heat', 'debye_temperature'
                ]
                
                for prop in additional_props:
                    if prop in props:
                        row[prop] = props[prop]
                
                data_list.append(row)
                
            except Exception as e:
                logger.warning(f"Failed to load {json_file.name}: {e}")
                continue
        
        self.data = pd.DataFrame(data_list).sort_values('x').reset_index(drop=True)
        logger.info(f"Loaded data for {len(self.data)} compositions")
        
        return self.data
    
    def calculate_statistics(self) -> pd.DataFrame:
        """
        Calculate statistical summary of properties.
        
        Returns:
            DataFrame with statistics (mean, std, min, max, etc.)
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Select numeric columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col != 'x']
        
        stats_dict = {}
        for col in numeric_cols:
            valid_data = self.data[col].dropna()
            if len(valid_data) > 0:
                stats_dict[col] = {
                    'count': len(valid_data),
                    'mean': valid_data.mean(),
                    'std': valid_data.std(),
                    'min': valid_data.min(),
                    'max': valid_data.max(),
                    'range': valid_data.max() - valid_data.min()
                }
        
        stats_df = pd.DataFrame(stats_dict).T
        logger.info("Statistics calculated")
        
        return stats_df
    
    def compare_sources(self, property_name: str) -> Dict:
        """
        Compare property values between data sources.
        
        Args:
            property_name: Property to compare
            
        Returns:
            Dictionary with comparison metrics
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if property_name not in self.data.columns:
            raise ValueError(f"Property '{property_name}' not found in data")
        
        sources = self.data['data_source'].unique()
        comparison = {}
        
        for source in sources:
            source_data = self.data[self.data['data_source'] == source][property_name].dropna()
            comparison[source] = {
                'count': len(source_data),
                'mean': source_data.mean(),
                'std': source_data.std(),
                'min': source_data.min(),
                'max': source_data.max()
            }
        
        # Calculate differences if both sources present
        if len(sources) >= 2:
            source_list = list(sources)
            data1 = self.data[self.data['data_source'] == source_list[0]][['x', property_name]]
            data2 = self.data[self.data['data_source'] == source_list[1]][['x', property_name]]
            
            # Merge on composition
            merged = pd.merge(data1, data2, on='x', suffixes=('_1', '_2'))
            
            if len(merged) > 0:
                diff = merged[f'{property_name}_1'] - merged[f'{property_name}_2']
                comparison['difference'] = {
                    'mean_absolute_difference': np.abs(diff).mean(),
                    'max_absolute_difference': np.abs(diff).max(),
                    'rmse': np.sqrt((diff ** 2).mean())
                }
        
        logger.info(f"Source comparison complete for '{property_name}'")
        return comparison
    
    def calculate_correlations(self, properties: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Calculate correlation matrix between properties.
        
        Args:
            properties: List of properties (None = all numeric)
            
        Returns:
            Correlation matrix DataFrame
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if properties is None:
            # Use all numeric columns except 'x'
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns
            properties = [col for col in numeric_cols if col != 'x']
        
        # Calculate correlation
        corr_data = self.data[properties].corr()
        
        logger.info("Correlation matrix calculated")
        return corr_data
    
    def plot_correlation_heatmap(self, output_path: Optional[str] = None,
                                properties: Optional[List[str]] = None):
        """
        Plot correlation heatmap.
        
        Args:
            output_path: Path to save figure (optional)
            properties: List of properties to include
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        corr_matrix = self.calculate_correlations(properties)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                   center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   ax=ax)
        
        ax.set_title('Property Correlation Matrix: Al$_{x}$Ga$_{1-x}$As',
                    fontweight='bold', pad=15, fontsize=12)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Correlation heatmap saved: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def identify_device_compositions(self, criteria: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
        """
        Identify compositions suitable for specific device applications.
        
        Args:
            criteria: Dictionary of property: (min, max) ranges
                Example: {'band_gap': (1.4, 1.6), 'electron_mobility': (8000, None)}
        
        Returns:
            DataFrame with suitable compositions
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        filtered = self.data.copy()
        
        for prop, (min_val, max_val) in criteria.items():
            if prop not in filtered.columns:
                logger.warning(f"Property '{prop}' not found, skipping criterion")
                continue
            
            if min_val is not None:
                filtered = filtered[filtered[prop] >= min_val]
            if max_val is not None:
                filtered = filtered[filtered[prop] <= max_val]
        
        logger.info(f"Found {len(filtered)} compositions matching criteria")
        return filtered
    
    def find_optimal_composition(self, target_property: str, 
                                target_value: float) -> Tuple[float, float]:
        """
        Find composition with property value closest to target.
        
        Args:
            target_property: Property name
            target_value: Target value
            
        Returns:
            Tuple of (optimal_x, actual_value)
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if target_property not in self.data.columns:
            raise ValueError(f"Property '{target_property}' not found")
        
        valid_data = self.data[[target_property, 'x']].dropna()
        
        # Find closest value
        idx = (valid_data[target_property] - target_value).abs().idxmin()
        optimal_x = valid_data.loc[idx, 'x']
        actual_value = valid_data.loc[idx, target_property]
        
        logger.info(f"Optimal composition: x={optimal_x:.3f} "
                   f"({target_property}={actual_value:.3f})")
        
        return optimal_x, actual_value
    
    def validate_vegard_law(self) -> Dict:
        """
        Validate Vegard's Law for lattice constant.
        
        Returns:
            Dictionary with validation metrics
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if 'lattice_constant' not in self.data.columns:
            raise ValueError("Lattice constant data not available")
        
        # Get endpoint values
        a_GaAs = self.data[self.data['x'] == 0.0]['lattice_constant'].iloc[0]
        a_AlAs = self.data[self.data['x'] == 1.0]['lattice_constant'].iloc[0]
        
        # Calculate Vegard prediction
        self.data['lattice_vegard'] = a_GaAs + self.data['x'] * (a_AlAs - a_GaAs)
        
        # Calculate deviation
        self.data['lattice_deviation'] = (self.data['lattice_constant'] - 
                                         self.data['lattice_vegard'])
        
        validation = {
            'mean_absolute_deviation': np.abs(self.data['lattice_deviation']).mean(),
            'max_absolute_deviation': np.abs(self.data['lattice_deviation']).max(),
            'rmse': np.sqrt((self.data['lattice_deviation'] ** 2).mean()),
            'r_squared': 1 - (np.sum(self.data['lattice_deviation'] ** 2) /
                            np.sum((self.data['lattice_constant'] - 
                                  self.data['lattice_constant'].mean()) ** 2))
        }
        
        logger.info(f"Vegard's Law validation: RMSE = {validation['rmse']:.6f} Å")
        return validation
    
    def export_summary_report(self, output_path: str):
        """
        Export comprehensive summary report to text file.
        
        Args:
            output_path: Output file path
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        with open(output_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("s-CGCNN v0.2 - Property Analysis Summary\n")
            f.write("=" * 70 + "\n\n")
            
            # Basic info
            f.write(f"Total Compositions: {len(self.data)}\n")
            f.write(f"Composition Range: x = {self.data['x'].min():.3f} to {self.data['x'].max():.3f}\n\n")
            
            # Statistics
            f.write("PROPERTY STATISTICS\n")
            f.write("-" * 70 + "\n")
            stats = self.calculate_statistics()
            f.write(stats.to_string())
            f.write("\n\n")
            
            # Data sources
            f.write("DATA SOURCES\n")
            f.write("-" * 70 + "\n")
            source_counts = self.data['data_source'].value_counts()
            for source, count in source_counts.items():
                f.write(f"  {source}: {count} compositions\n")
            f.write("\n")
            
            # Vegard validation
            f.write("VEGARD'S LAW VALIDATION\n")
            f.write("-" * 70 + "\n")
            vegard = self.validate_vegard_law()
            for key, value in vegard.items():
                f.write(f"  {key}: {value:.6f}\n")
            f.write("\n")
            
            f.write("=" * 70 + "\n")
        
        logger.info(f"Summary report exported: {output_path}")


if __name__ == "__main__":
    # Demo usage
    tools = ComparisonTools()
    tools.load_data()
    print(f"Loaded data for {len(tools.data)} compositions")
    
    # Example analysis
    stats = tools.calculate_statistics()
    print("\nProperty Statistics:")
    print(stats)
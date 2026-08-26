import pandas as pd
import numpy as np
import io
import re
import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

class DataCleanerAgent(BaseAgent):
    """
    Data Cleaner Agent.
    
    This agent is responsible for cleaning raw data. It handles both CSV and Excel
    files, standardizes column names, removes exact duplicates, handles missing values,
    infers datatypes (like dates), and detects numerical outliers using the IQR method.
    It is entirely rule-based and ensures the dataset is clean and ready for downstream
    analysis by other agents in the pipeline.
    """
    name: str = "DataCleanerAgent"
    role: str = "Data cleaning and standardization"

    def execute(self, input_data: dict) -> dict:
        file_bytes = input_data.get("file_bytes")
        filename = input_data.get("filename", "")
        
        if not file_bytes:
            raise ValueError("Input data must contain 'file_bytes'.")
            
        # 1. Parse file
        df = self._parse_file(file_bytes, filename)
        
        if df.empty:
            raise ValueError("Parsed dataframe is empty.")
            
        rows_before = len(df)
        issues = []
        
        # 2. Standardize column names
        old_cols = list(df.columns)
        df.columns = self._standardize_columns(df.columns)
        columns_standardized = (old_cols != list(df.columns))
        if columns_standardized:
            issues.append("Standardized column names (lowercased, replaced spaces/special characters with underscores).")
            
        # 3. Remove exact duplicates
        duplicates_count = df.duplicated().sum()
        if duplicates_count > 0:
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)
            issues.append(f"Removed {duplicates_count} duplicate rows.")
            
        # Sanitize formula injection
        df = self._sanitize_formulas(df, issues)
            
        # 4. Handle missing values
        # we convert the series to dict for output
        missing_values_counts = df.isna().sum().to_dict()
        missing_values_action = {}
        
        cols_to_drop = []
        for col in df.columns:
            missing_count = missing_values_counts[col]
            if missing_count == 0:
                continue
                
            missing_pct = missing_count / len(df)
            if missing_pct > 0.5:
                cols_to_drop.append(col)
                missing_values_action[col] = "dropped column"
                issues.append(f"Dropped column '{col}' because it has >50% missing values ({missing_count} missing).")
            else:
                if pd.api.types.is_numeric_dtype(df[col]):
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    missing_values_action[col] = "filled with median"
                    issues.append(f"Filled {missing_count} missing values in '{col}' with median ({median_val}).")
                else:
                    mode_series = df[col].mode()
                    if not mode_series.empty:
                        mode_val = mode_series.iloc[0]
                        df[col] = df[col].fillna(mode_val)
                        missing_values_action[col] = "filled with mode"
                        issues.append(f"Filled {missing_count} missing values in '{col}' with mode ({mode_val}).")
                    else:
                        missing_values_action[col] = "left as is (no mode)"
                        
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)
            
        # 5. Auto-detect dates
        dtype_conversions = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    non_nulls = df[col].dropna()
                    if len(non_nulls) > 0:
                        converted = pd.to_datetime(df[col], errors='coerce', format='mixed')
                        if converted.notna().sum() == non_nulls.notna().sum() and converted.notna().sum() > 0:
                            df[col] = converted
                            dtype_conversions[col] = "object -> datetime"
                            issues.append(f"Converted column '{col}' from object to datetime.")
                except Exception as e:
                    logger.debug(f"Failed to convert column {col} to datetime: {e}")
                    
        # 6. Detect numeric outliers (IQR)
        outliers_flagged = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                low_thresh = Q1 - 1.5 * IQR
                high_thresh = Q3 + 1.5 * IQR
                
                outliers_mask = (df[col] < low_thresh) | (df[col] > high_thresh)
                outlier_count = int(outliers_mask.sum())
                
                if outlier_count > 0:
                    outliers_flagged[col] = {
                        "count": outlier_count,
                        "threshold_low": float(low_thresh),
                        "threshold_high": float(high_thresh)
                    }
                    issues.append(f"Flagged {outlier_count} outliers in '{col}' (IQR method).")
                    
        rows_after = len(df)
        
        # Compile summary
        summary = {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "columns": list(df.columns),
            "duplicates_removed": int(duplicates_count),
            "missing_values": missing_values_counts,
            "missing_values_action": missing_values_action,
            "dtype_conversions": dtype_conversions,
            "columns_standardized": columns_standardized,
            "outliers_flagged": outliers_flagged,
            "issues": issues,
        }
        
        return {
            "cleaned_df": df,
            "summary": summary
        }

    def _sanitize_formulas(self, df: pd.DataFrame, issues: list) -> pd.DataFrame:
        """Strip potentially dangerous formula injection characters from string cells."""
        dangerous_prefixes = ('=', '+', '-', '@', '\t', '\r')
        sanitized_count = 0
        
        for col in df.select_dtypes(include=['object']).columns:
            mask = df[col].astype(str).str.startswith(dangerous_prefixes)
            count = mask.sum()
            if count > 0:
                df[col] = df[col].apply(
                    lambda x: x.lstrip('=+\\-@\t\r') if isinstance(x, str) and x.startswith(dangerous_prefixes) else x
                )
                sanitized_count += count
        
        if sanitized_count > 0:
            issues.append(f"Sanitized {sanitized_count} cells with potential formula injection characters")
        
        return df

    def _parse_file(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """Parses CSV or Excel bytes into a DataFrame, handling various encodings."""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.xls') or filename_lower.endswith('.xlsx'):
            try:
                return pd.read_excel(io.BytesIO(file_bytes))
            except Exception as e:
                logger.error(f"Error reading Excel file: {e}")
                raise ValueError(f"Failed to read Excel file: {e}")
                
        else: # Default to CSV
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for enc in encodings:
                try:
                    return pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                except UnicodeDecodeError:
                    continue
                except pd.errors.EmptyDataError:
                    raise ValueError("The provided CSV file is empty.")
                except Exception as e:
                    logger.error(f"Error reading CSV with encoding {enc}: {e}")
                    raise ValueError(f"Failed to read CSV file: {e}")
            raise ValueError("Failed to parse CSV file with supported encodings.")

    def _standardize_columns(self, columns: pd.Index) -> List[str]:
        """Lowercases and replaces spaces/special characters with underscores."""
        std_cols = []
        for col in columns:
            col_str = str(col).lower().strip()
            col_str = re.sub(r'[^a-z0-9]+', '_', col_str)
            col_str = col_str.strip('_')
            if not col_str:
                col_str = 'unnamed'
            std_cols.append(col_str)
            
        # Handle duplicates in standard columns
        final_cols = []
        seen = {}
        for col in std_cols:
            if col in seen:
                seen[col] += 1
                final_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                final_cols.append(col)
                
        return final_cols

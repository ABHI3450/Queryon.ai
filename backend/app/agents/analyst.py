"""
Analyst Agent
=============
Identifies the 3-5 most important trends, patterns, and outliers in the data.

WHY THIS EXISTS:
- Raw data is overwhelming — this agent finds the signal in the noise
- Dual-mode: rule-based statistical analysis (always works) + Groq LLM enhancement
- Rule-based ensures the system works without any API key
- LLM enhancement provides richer, more nuanced business insights when available
"""

import logging
import json
import time
import uuid
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.config import settings

# Lazy import — Groq SDK is optional (system works without it)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

class AnalystAgent(BaseAgent):
    """
    Analyst Agent is responsible for extracting meaningful insights from a cleaned dataset.
    
    It operates in a dual mode:
    1. Rule-based Statistical Analysis: Always runs to extract fundamental insights like 
       correlations, top-n aggregations, time-series trends, and categorical proportions.
    2. LLM Enhancement (Optional): If Groq LLM is enabled, it enhances the findings by 
       generating higher-level business insights.
       
    The insights are sorted by importance and returned in a structured format suitable 
    for chart generation by downstream agents.
    """
    name: str = "AnalystAgent"
    role: str = "Data Analyst"

    def execute(self, input_data: dict) -> dict:
        """
        Executes the analysis pipeline on the provided dataset.
        
        Args:
            input_data (dict): Contains 'cleaned_df' (pd.DataFrame) and 'cleaning_summary' (dict)
            
        Returns:
            dict: A dictionary containing a list of 'findings', each describing a specific insight
                  and suggesting an appropriate visualization.
        """
        logger.info("AnalystAgent starting execution...")
        start_time = time.time()
        
        # 1. Validate Input
        if 'cleaned_df' not in input_data or not isinstance(input_data['cleaned_df'], pd.DataFrame):
            logger.error("Missing or invalid 'cleaned_df' in input_data")
            raise ValueError("AnalystAgent requires a 'cleaned_df' of type pandas.DataFrame.")
            
        df = input_data['cleaned_df']
        cleaning_summary = input_data.get('cleaning_summary', {})
        
        if df.empty:
            logger.warning("The provided DataFrame is empty.")
            return {"findings": []}
            
        # 2. Rule-Based Analysis
        rule_based_findings = self._run_rule_based_analysis(df)
        
        # 3. LLM Enhancement (Optional)
        llm_findings = []
        if settings.llm_enabled and GROQ_AVAILABLE:
            logger.info("LLM enabled. Running Groq enhancement...")
            try:
                llm_findings = self._run_llm_analysis(df)
                logger.info(f"LLM extracted {len(llm_findings)} findings.")
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}. Falling back to rule-based only.")
        else:
            logger.info("LLM not enabled. Relying solely on rule-based analysis.")
            
        # 4. Merge and Select Findings
        merged_findings = self._merge_findings(rule_based_findings, llm_findings)
        
        # Take top 5 most important findings (ensure High priority comes first)
        high_priority = [f for f in merged_findings if f.get('importance', 'medium').lower() == 'high']
        medium_priority = [f for f in merged_findings if f.get('importance', 'medium').lower() == 'medium']
        
        final_findings = (high_priority + medium_priority)[:5]
        
        # Assign IDs if missing
        for i, finding in enumerate(final_findings):
            if 'id' not in finding:
                finding['id'] = f"finding_{uuid.uuid4().hex[:8]}"
                
        logger.info(f"AnalystAgent finished in {time.time() - start_time:.2f}s. Returning {len(final_findings)} findings.")
        
        return {
            "findings": final_findings
        }

    def _run_rule_based_analysis(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Executes statistical rules to find correlations, top categories, and trends."""
        findings = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
        
        # 1. Correlation Detection
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols].corr().abs()
                # Find upper triangle without diagonal
                upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                
                # Find pairs with correlation > 0.5
                high_corr = [(r, c, upper.loc[r, c]) for r in upper.index for c in upper.columns if pd.notna(upper.loc[r, c]) and upper.loc[r, c] > 0.5]
                
                # Sort by highest correlation
                high_corr.sort(key=lambda x: x[2], reverse=True)
                
                if high_corr:
                    col1, col2, corr_val = high_corr[0] # Take strongest correlation
                    findings.append({
                        "title": f"Strong Correlation: {col1} & {col2}",
                        "description": f"There is a significant positive/negative correlation ({corr_val:.2f}) between {col1} and {col2}.",
                        "importance": "high" if corr_val > 0.7 else "medium",
                        "evidence": {"correlation": corr_val, "col1": col1, "col2": col2},
                        "chart_type": "scatter",
                        "chart_config": {"x": col1, "y": col2, "group_by": None, "data": None}
                    })
            except Exception as e:
                logger.warning(f"Failed to compute correlations: {e}")

        # 2. Top-N Analysis & Category Proportions
        if categorical_cols and numeric_cols:
            for cat_col in categorical_cols[:2]: # Limit to top 2 categorical columns
                try:
                    num_col = numeric_cols[0] # Take first numeric column
                    # Group by and sum
                    grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
                    if not grouped.empty and len(grouped) > 1:
                        top_cat = grouped.index[0]
                        top_val = grouped.iloc[0]
                        findings.append({
                            "title": f"Top {cat_col} by {num_col}",
                            "description": f"{top_cat} has the highest total {num_col} ({top_val:,.2f}).",
                            "importance": "high",
                            "evidence": {"top_category": str(top_cat), "value": float(top_val), "metric": "sum"},
                            "chart_type": "bar",
                            "chart_config": {"x": cat_col, "y": num_col, "group_by": None, "data": None}
                        })
                        
                    # Category Proportions
                    value_counts = df[cat_col].value_counts(normalize=True)
                    if not value_counts.empty and value_counts.iloc[0] > 0.4: # One category dominates > 40%
                        dom_cat = value_counts.index[0]
                        dom_pct = value_counts.iloc[0] * 100
                        findings.append({
                            "title": f"Dominant Category in {cat_col}",
                            "description": f"{dom_cat} represents {dom_pct:.1f}% of the dataset in {cat_col}.",
                            "importance": "medium",
                            "evidence": {"dominant_category": str(dom_cat), "percentage": float(dom_pct)},
                            "chart_type": "pie",
                            "chart_config": {"x": cat_col, "y": None, "group_by": None, "data": None}
                        })
                except Exception as e:
                    logger.warning(f"Failed to compute top-N for {cat_col}: {e}")

        # 3. Time-Series Trend
        if datetime_cols and numeric_cols:
            dt_col = datetime_cols[0]
            num_col = numeric_cols[0]
            try:
                # Basic aggregation (just suggesting line chart, data prep is handled downstream)
                findings.append({
                    "title": f"Trend Analysis: {num_col} over Time",
                    "description": f"Tracking how {num_col} changes across {dt_col}.",
                    "importance": "medium",
                    "evidence": {"time_column": dt_col, "value_column": num_col},
                    "chart_type": "line",
                    "chart_config": {"x": dt_col, "y": num_col, "group_by": None, "data": None}
                })
            except Exception as e:
                logger.warning(f"Failed time-series analysis: {e}")
                
        # 4. Outlier/Distribution Analysis (Basic fallback if no correlations or time series)
        if not findings and numeric_cols:
            for num_col in numeric_cols[:1]:
                try:
                    skewness = df[num_col].skew()
                    desc = "highly skewed" if abs(skewness) > 1 else "relatively normal"
                    findings.append({
                        "title": f"Distribution of {num_col}",
                        "description": f"The distribution of {num_col} is {desc} (skewness: {skewness:.2f}).",
                        "importance": "medium",
                        "evidence": {"skewness": float(skewness)},
                        "chart_type": "bar",
                        "chart_config": {"x": num_col, "y": None, "group_by": None, "data": None} # Histogram proxy
                    })
                except Exception as e:
                    logger.warning(f"Failed distribution analysis: {e}")

        return findings

    def _run_llm_analysis(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Uses Groq LLM to generate insights based on dataset summary."""
        try:
            client = Groq(api_key=settings.groq_api_key)
            
            # Prepare data summary (safely)
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            summary_parts = []
            summary_parts.append(f"Columns and Types:\n{df.dtypes.to_string()}")
            
            if num_cols:
                summary_parts.append(f"\nNumeric Summary:\n{df[num_cols].describe().to_string()}")
                
            if cat_cols:
                cat_summary = []
                for col in cat_cols[:5]: # Max 5 categorical columns
                    top_vals = df[col].value_counts().head(5).to_dict()
                    cat_summary.append(f"{col} top values: {top_vals}")
                summary_parts.append("\nCategorical Summary:\n" + "\n".join(cat_summary))
                
            summary_parts.append(f"\nSample Rows:\n{df.head(5).to_string()}")
            
            data_context = "\n".join(summary_parts)
            
            system_prompt = (
                "You are a senior data analyst. Given a dataset summary, identify the 3-5 most important "
                "business insights. For each insight, provide: title, description, importance (high/medium), "
                "supporting evidence (specific numbers as a flat dictionary), and recommended chart type "
                "(bar, line, scatter, pie, or heatmap).\n"
                "Also provide a 'chart_config' object with 'x' (column name), 'y' (column name, optional), "
                "and 'group_by' (column name, optional).\n\n"
                "Respond ONLY in valid JSON with this format:\n"
                "{\"findings\": [{\"title\": \"...\", \"description\": \"...\", \"importance\": \"high\", "
                "\"evidence\": {\"metric1\": 100}, \"chart_type\": \"bar\", \"chart_config\": {\"x\": \"col1\", \"y\": \"col2\"}}]}"
            )
            
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Dataset Summary:\n{data_context}"}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed.get("findings", [])
            
        except Exception as e:
            logger.error(f"Error in LLM enhancement: {e}")
            return []

    def _merge_findings(self, rule_based: List[Dict], llm_based: List[Dict]) -> List[Dict]:
        """Merges rule-based and LLM findings, giving LLM priority."""
        if not llm_based:
            return rule_based
            
        # For simplicity, if LLM findings exist, we use them primarily, and pad with rule-based if needed
        # We ensure chart_config is properly structured.
        merged = []
        for finding in llm_based:
            if 'chart_config' not in finding:
                finding['chart_config'] = {"x": None, "y": None, "group_by": None, "data": None}
            # Ensure required fields
            finding['id'] = f"finding_{uuid.uuid4().hex[:8]}"
            merged.append(finding)
            
        # Add rule based if we have less than 3 findings
        if len(merged) < 3:
            for rb in rule_based:
                # Avoid exact duplicates by title loosely
                if not any(m.get('title') == rb.get('title') for m in merged):
                    merged.append(rb)
                    if len(merged) >= 5:
                        break
                        
        return merged

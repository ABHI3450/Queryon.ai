import os
import uuid
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Use 'Agg' backend for server-side rendering
matplotlib.use('Agg')

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

class VisualizerAgent(BaseAgent):
    """
    Agent responsible for generating publication-quality modern dark-themed charts.
    Uses high DPI (300), vibrant neon gradients, smooth curves, area glows, and clean typography.
    """
    
    name = "VisualizerAgent"
    role = "Data Visualizer"

    def __init__(self):
        super().__init__()
        self._setup_style()

    def _setup_style(self):
        """Sets up an ultra-modern, crisp dark theme for matplotlib."""
        plt.style.use('dark_background')
        
        # Vibrant modern neon color palette
        self.colors = [
            '#00f0ff',  # Electric Cyan
            '#a855f7',  # Deep Purple/Violet
            '#ff2a85',  # Hot Pink
            '#ffb700',  # Amber Gold
            '#00e676',  # Neon Mint
            '#ff5252',  # Coral Red
            '#3b82f6',  # Vivid Blue
        ]
        
        plt.rcParams.update({
            'figure.figsize': (11, 6.5),
            'figure.dpi': 300,
            'figure.facecolor': '#0b0e17',
            'axes.facecolor': '#0b0e17',
            'axes.edgecolor': '#1e2436',
            'axes.linewidth': 1.2,
            'axes.labelcolor': '#94a3b8',
            'text.color': '#f8fafc',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'axes.grid': True,
            'grid.color': '#1e2436',
            'grid.linestyle': '--',
            'grid.linewidth': 0.8,
            'grid.alpha': 0.6,
            'axes.prop_cycle': plt.cycler('color', self.colors),
            'font.family': ['Segoe UI', 'DejaVu Sans', 'sans-serif'],
            'font.weight': 'medium',
            'axes.titlesize': 15,
            'axes.titleweight': 'bold',
            'axes.titlelocation': 'left',
            'axes.labelsize': 11,
            'axes.labelweight': 'semibold',
        })

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned_df = input_data.get("cleaned_df")
        findings = input_data.get("findings", [])
        output_dir = input_data.get("output_dir", "")
        
        if cleaned_df is None:
            logger.error("No cleaned dataframe provided.")
            return {"charts": []}
            
        if not output_dir:
            logger.error("No output directory provided.")
            return {"charts": []}
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        generated_charts = []
        
        for finding in findings:
            try:
                chart_info = self._process_finding(finding, cleaned_df, output_dir)
                if chart_info:
                    generated_charts.append(chart_info)
            except Exception as e:
                logger.warning(f"Failed to generate chart for finding {finding.get('id', 'unknown')}: {str(e)}")
                
        return {"charts": generated_charts}

    def _process_finding(self, finding: Dict[str, Any], df: pd.DataFrame, output_dir: str) -> Dict[str, Any]:
        finding_id = finding.get('id', str(uuid.uuid4()))
        chart_type = finding.get('chart_type')
        chart_config = finding.get('chart_config', {})
        title = finding.get('title', 'Chart')
        
        if not chart_type or not chart_config:
            logger.info(f"Skipping finding {finding_id} - missing chart type or config.")
            return None
            
        # Determine data source
        data = chart_config.get('data')
        if data:
            if isinstance(data, dict):
                if all(not isinstance(v, (list, tuple, dict)) for v in data.values()):
                    x_col = chart_config.get('x', 'category')
                    y_col = chart_config.get('y', 'value')
                    plot_df = pd.DataFrame(list(data.items()), columns=[x_col, y_col])
                else:
                    plot_df = pd.DataFrame(data)
            else:
                plot_df = pd.DataFrame(data)
        else:
            plot_df = df
            
        file_path = os.path.join(output_dir, f"chart_{finding_id}.png")
        
        fig, ax = plt.subplots(figsize=(11, 6.5))
        
        # Remove top and right spines for a clean minimal layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#1e2436')
        ax.spines['bottom'].set_color('#1e2436')
        
        try:
            if chart_type == 'bar':
                self._create_bar_chart(plot_df, chart_config, title, ax)
            elif chart_type == 'line':
                self._create_line_chart(plot_df, chart_config, title, ax)
            elif chart_type == 'scatter':
                self._create_scatter_chart(plot_df, chart_config, title, ax)
            elif chart_type == 'pie':
                self._create_pie_chart(plot_df, chart_config, title, ax)
            else:
                logger.warning(f"Unsupported chart type: {chart_type}")
                plt.close(fig)
                return None
                
            ax.set_title(title, pad=22, color='#ffffff', fontsize=15, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(file_path, bbox_inches='tight', dpi=300, facecolor='#0b0e17', edgecolor='none')
            
            return {
                "finding_id": finding_id,
                "chart_type": chart_type,
                "file_path": file_path,
                "title": title
            }
        finally:
            plt.close(fig)

    def _create_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any], title: str, ax: plt.Axes):
        x = config.get('x')
        y = config.get('y')
        
        if not x or not y:
            raise ValueError("Bar chart requires 'x' and 'y' in config")
            
        if x not in df.columns or (isinstance(y, str) and y not in df.columns):
            raise ValueError(f"Columns missing from dataframe. Expected x: {x}, y: {y}")
            
        plot_df = df.copy()
        
        # High cardinality handling
        if len(plot_df) > 10 and isinstance(y, str):
            top_10 = plot_df.sort_values(by=y, ascending=False).head(10)
            other_sum = plot_df.sort_values(by=y, ascending=False).iloc[10:][y].sum()
            if other_sum > 0:
                other_row = pd.DataFrame([{x: "Other (Rest)", y: other_sum}])
                plot_df = pd.concat([top_10, other_row], ignore_index=True)
            else:
                plot_df = top_10

        use_horizontal = len(plot_df) >= 6 or any(len(str(val)) > 12 for val in plot_df[x])

        if isinstance(y, list):
            bars = plot_df.plot(x=x, y=y, kind='bar', ax=ax, width=0.75, alpha=0.9)
            ax.legend(facecolor='#0b0e17', edgecolor='#1e2436', labelcolor='#e2e8f0')
        else:
            primary_color = self.colors[0]
            if use_horizontal:
                plot_df = plot_df.iloc[::-1]  # Reverse so highest is at top
                bars = ax.barh(plot_df[x], plot_df[y], color=primary_color, height=0.6, alpha=0.9, edgecolor='#00f0ff', linewidth=1)
                ax.set_ylabel(x, labelpad=10)
                ax.set_xlabel(str(y), labelpad=10)
                
                # Add crisp data labels at bar ends
                max_val = plot_df[y].max()
                for bar in bars:
                    width = bar.get_width()
                    val_str = f"{width:,.1f}".rstrip('0').rstrip('.') if isinstance(width, float) else f"{width:,}"
                    ax.text(width + (max_val * 0.015), bar.get_y() + bar.get_height()/2, val_str,
                            va='center', ha='left', color='#f8fafc', fontsize=9, fontweight='semibold')
            else:
                bars = ax.bar(plot_df[x], plot_df[y], color=primary_color, width=0.55, alpha=0.9, edgecolor='#00f0ff', linewidth=1)
                ax.set_xlabel(x, labelpad=10)
                ax.set_ylabel(str(y), labelpad=10)
                ax.tick_params(axis='x', rotation=30)
                
                # Add crisp data labels above bars
                max_val = plot_df[y].max()
                for bar in bars:
                    height = bar.get_height()
                    val_str = f"{height:,.1f}".rstrip('0').rstrip('.') if isinstance(height, float) else f"{height:,}"
                    ax.text(bar.get_x() + bar.get_width()/2, height + (max_val * 0.02), val_str,
                            ha='center', va='bottom', color='#f8fafc', fontsize=9, fontweight='semibold')

    def _create_line_chart(self, df: pd.DataFrame, config: Dict[str, Any], title: str, ax: plt.Axes):
        x = config.get('x')
        y = config.get('y')
        
        if not x or not y:
            raise ValueError("Line chart requires 'x' and 'y' in config")
            
        if x not in df.columns:
            raise ValueError(f"Column '{x}' missing from dataframe.")
            
        y_cols = y if isinstance(y, list) else [y]
        missing_y = [col for col in y_cols if col not in df.columns]
        if missing_y:
            raise ValueError(f"Columns missing from dataframe: {missing_y}")
            
        plot_df = df
        show_markers = len(plot_df) <= 35

        for i, y_col in enumerate(y_cols):
            color = self.colors[i % len(self.colors)]
            
            # Draw line with subtle glow area fill
            ax.plot(
                plot_df[x],
                plot_df[y_col],
                marker='o' if show_markers else None,
                markersize=6,
                markerfacecolor='#0b0e17',
                markeredgewidth=2,
                markeredgecolor=color,
                linewidth=2.5,
                label=y_col,
                color=color,
            )
            
            # Soft glowing area under line
            try:
                ax.fill_between(
                    plot_df[x],
                    plot_df[y_col],
                    color=color,
                    alpha=0.15
                )
            except Exception:
                pass
            
        ax.set_xlabel(x, labelpad=10)
        ax.set_ylabel('Value' if len(y_cols) > 1 else y_cols[0], labelpad=10)
        ax.tick_params(axis='x', rotation=35)
        
        if len(y_cols) > 1:
            ax.legend(facecolor='#0b0e17', edgecolor='#1e2436', labelcolor='#e2e8f0', framealpha=0.9)

    def _create_scatter_chart(self, df: pd.DataFrame, config: Dict[str, Any], title: str, ax: plt.Axes):
        x = config.get('x')
        y = config.get('y')
        group_by = config.get('group_by')
        
        if not x or not y:
            raise ValueError("Scatter chart requires 'x' and 'y' in config")
            
        if x not in df.columns or y not in df.columns:
            raise ValueError(f"Columns missing from dataframe. Expected x: {x}, y: {y}")
            
        if group_by and group_by in df.columns:
            groups = df.groupby(group_by)
            for i, (name, group) in enumerate(groups):
                color = self.colors[i % len(self.colors)]
                ax.scatter(group[x], group[y], label=str(name), alpha=0.85, color=color, s=70, edgecolors='#ffffff', linewidths=0.5)
            ax.legend(facecolor='#0b0e17', edgecolor='#1e2436', labelcolor='#e2e8f0', framealpha=0.9)
        else:
            ax.scatter(df[x], df[y], alpha=0.85, color=self.colors[0], s=70, edgecolors='#ffffff', linewidths=0.5)
            
        ax.set_xlabel(x, labelpad=10)
        ax.set_ylabel(y, labelpad=10)

    def _create_pie_chart(self, df: pd.DataFrame, config: Dict[str, Any], title: str, ax: plt.Axes):
        labels_col = config.get('x')
        values_col = config.get('y')
        
        if not labels_col or not values_col:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            non_num_cols = [c for c in df.columns if c not in num_cols]
            if non_num_cols and num_cols:
                labels_col = labels_col or non_num_cols[0]
                values_col = values_col or num_cols[0]
            elif len(df.columns) >= 2:
                labels_col = labels_col or df.columns[0]
                values_col = values_col or df.columns[1]

        if not labels_col or not values_col:
            raise ValueError("Pie chart requires 'x' (labels) and 'y' (values) in config")
            
        if labels_col not in df.columns or values_col not in df.columns:
            raise ValueError(f"Columns missing from dataframe. Expected labels: {labels_col}, values: {values_col}")
            
        plot_df = df.copy()

        if len(plot_df) > 6:
            top_5 = plot_df.sort_values(by=values_col, ascending=False).head(5)
            other_val = plot_df.sort_values(by=values_col, ascending=False).iloc[5:][values_col].sum()
            other_row = pd.DataFrame([{labels_col: "Other", values_col: other_val}])
            plot_df = pd.concat([top_5, other_row], ignore_index=True)

        slice_colors = self.colors[:len(plot_df)]
        explode = [0.04] + [0] * (len(plot_df) - 1)  # Slightly pop out the top slice

        wedges, texts, autotexts = ax.pie(
            plot_df[values_col], 
            labels=plot_df[labels_col], 
            autopct='%1.1f%%',
            pctdistance=0.75,
            startangle=140,
            explode=explode,
            colors=slice_colors,
            wedgeprops=dict(width=0.45, edgecolor='#0b0e17', linewidth=2.5) # Sleek modern donut ring
        )
        
        for text in texts:
            text.set_color('#cbd5e1')
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('#ffffff')
            autotext.set_weight('bold')
            autotext.set_fontsize(10)

        # Center summary badge inside donut hole
        total_val = plot_df[values_col].sum()
        total_str = f"{total_val:,.0f}" if isinstance(total_val, (int, float, np.number)) else str(total_val)
        ax.text(0, 0.08, "TOTAL", ha='center', va='center', color='#94a3b8', fontsize=9, fontweight='bold')
        ax.text(0, -0.10, total_str, ha='center', va='center', color='#00f0ff', fontsize=14, fontweight='bold')

        ax.axis('equal')

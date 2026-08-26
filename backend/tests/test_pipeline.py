"""
Tests for the Multi-Agent Data Analyst Pipeline
================================================
Unit tests for each agent + integration test for the full pipeline.

Run with: pytest tests/ -v
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add backend to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.base import BaseAgent, AgentResult
from app.agents.cleaner import DataCleanerAgent
from app.agents.analyst import AnalystAgent
from app.agents.visualizer import VisualizerAgent
from app.agents.explainer import ExplainerAgent


# ═══════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════

@pytest.fixture
def sample_csv_bytes():
    """Sample CSV file as bytes — simulates an uploaded file."""
    csv_content = """date,product,category,region,units_sold,revenue,customer_type
2024-01-05,Laptop Pro 15,Electronics,North,12,18000.00,Business
2024-01-05,Wireless Mouse,Electronics,South,45,1350.00,Consumer
2024-01-08,Office Chair Ergo,Furniture,East,8,4800.00,Business
2024-01-08,Desk Lamp LED,Furniture,West,22,1100.00,Consumer
2024-01-10,Laptop Pro 15,Electronics,South,15,22500.00,Business
2024-01-10,USB-C Hub,Electronics,North,38,2280.00,Consumer
2024-01-12,Standing Desk,Furniture,East,5,3750.00,Business
2024-01-15,Wireless Mouse,Electronics,North,52,1560.00,Consumer
2024-01-15,Monitor 27inch,Electronics,West,10,5000.00,Business
2024-01-18,Office Chair Ergo,Furniture,,6,3600.00,Consumer
2024-01-18,Laptop Pro 15,Electronics,North,20,30000.00,Business
2024-01-20,Desk Lamp LED,Furniture,South,30,1500.00,Consumer
2024-01-22,USB-C Hub,Electronics,East,42,2520.00,Consumer
2024-01-22,Wireless Mouse,Electronics,North,48,1440.00,Consumer
2024-01-22,Wireless Mouse,Electronics,North,48,1440.00,Consumer
01/25/2024,Standing Desk,Furniture,West,7,5250.00,Business
2024-01-25,Monitor 27inch,Electronics,South,12,6000.00,Business
2024-01-28,Laptop Pro 15,Electronics,East,18,27000.00,Business
2024-01-28,Office Chair Ergo,Furniture,North,9,,Consumer
"""
    return csv_content.encode("utf-8")


@pytest.fixture
def cleaned_dataframe():
    """A pre-cleaned DataFrame for testing downstream agents."""
    data = {
        "date": pd.date_range("2024-01-01", periods=20, freq="3D"),
        "product": ["Laptop", "Mouse", "Chair", "Desk", "Monitor"] * 4,
        "category": ["Electronics", "Electronics", "Furniture", "Furniture", "Electronics"] * 4,
        "region": ["North", "South", "East", "West", "North"] * 4,
        "units_sold": [12, 45, 8, 22, 10, 15, 52, 6, 30, 42, 20, 48, 7, 25, 12, 18, 55, 9, 35, 14],
        "revenue": [18000, 1350, 4800, 1100, 5000, 22500, 1560, 3600, 1500, 2520,
                     30000, 1440, 5250, 1250, 6000, 27000, 1650, 5400, 2100, 7000],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_cleaning_summary():
    """Cleaning summary matching the cleaner agent's output format."""
    return {
        "rows_before": 20,
        "rows_after": 19,
        "columns": ["date", "product", "category", "region", "units_sold", "revenue"],
        "duplicates_removed": 1,
        "missing_values": {"region": 1, "revenue": 1},
        "missing_values_action": {"region": "filled with mode", "revenue": "filled with median"},
        "dtype_conversions": {"date": "object -> datetime"},
        "columns_standardized": True,
        "outliers_flagged": {},
        "issues": [
            "Standardized column names.",
            "Removed 1 duplicate row.",
            "Filled 1 missing values in 'region' with mode (North).",
            "Filled 1 missing values in 'revenue' with median (4900.0).",
        ],
    }


@pytest.fixture
def sample_findings():
    """Findings matching the analyst agent's output format."""
    return [
        {
            "id": "finding_1",
            "title": "Laptop Dominates Revenue",
            "description": "Laptop Pro 15 generates the most revenue across all products.",
            "importance": "high",
            "evidence": {"total_revenue": 97500, "pct_of_total": 55.2},
            "chart_type": "bar",
            "chart_config": {
                "x": "product",
                "y": "revenue",
                "group_by": None,
                "data": {"Laptop": 97500, "Mouse": 6000, "Chair": 19800, "Desk": 5950, "Monitor": 23500},
            },
        },
        {
            "id": "finding_2",
            "title": "Electronics vs Furniture Split",
            "description": "Electronics accounts for 65% of total revenue.",
            "importance": "medium",
            "evidence": {"electronics_pct": 65.0, "furniture_pct": 35.0},
            "chart_type": "pie",
            "chart_config": {
                "x": "category",
                "y": "revenue",
                "group_by": None,
                "data": {"Electronics": 127000, "Furniture": 31550},
            },
        },
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for chart output."""
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir()
    return str(charts_dir)


# ═══════════════════════════════════════
# Data Cleaner Agent Tests
# ═══════════════════════════════════════

class TestDataCleanerAgent:
    """Tests for the Data Cleaner Agent (rule-based)."""
    
    def test_cleaner_processes_csv(self, sample_csv_bytes):
        """Cleaner should successfully parse and clean a CSV file."""
        agent = DataCleanerAgent()
        result = agent.run({
            "file_bytes": sample_csv_bytes,
            "filename": "test.csv",
        })
        
        assert result.success, f"Cleaner failed: {result.errors}"
        assert "cleaned_df" in result.data
        assert "summary" in result.data
        assert isinstance(result.data["cleaned_df"], pd.DataFrame)
    
    def test_cleaner_removes_duplicates(self, sample_csv_bytes):
        """Cleaner should detect and remove duplicate rows."""
        agent = DataCleanerAgent()
        result = agent.run({
            "file_bytes": sample_csv_bytes,
            "filename": "test.csv",
        })
        
        summary = result.data["summary"]
        assert summary["duplicates_removed"] >= 1
    
    def test_cleaner_handles_missing_values(self, sample_csv_bytes):
        """Cleaner should fill missing values (median for numeric, mode for categorical)."""
        agent = DataCleanerAgent()
        result = agent.run({
            "file_bytes": sample_csv_bytes,
            "filename": "test.csv",
        })
        
        df = result.data["cleaned_df"]
        # After cleaning, there should be no missing values
        assert df.isna().sum().sum() == 0
    
    def test_cleaner_standardizes_columns(self, sample_csv_bytes):
        """Cleaner should lowercase and snake_case column names."""
        agent = DataCleanerAgent()
        result = agent.run({
            "file_bytes": sample_csv_bytes,
            "filename": "test.csv",
        })
        
        columns = result.data["summary"]["columns"]
        for col in columns:
            assert col == col.lower(), f"Column '{col}' should be lowercase"
    
    def test_cleaner_rejects_empty_file(self):
        """Cleaner should fail gracefully on empty file."""
        agent = DataCleanerAgent()
        result = agent.run({
            "file_bytes": b"",
            "filename": "empty.csv",
        })
        
        assert not result.success
    
    def test_cleaner_generates_issues_list(self, sample_csv_bytes):
        """Cleaner should produce a human-readable list of issues found."""
        agent = DataCleanerAgent()
        result = agent.run({
            "file_bytes": sample_csv_bytes,
            "filename": "test.csv",
        })
        
        issues = result.data["summary"]["issues"]
        assert isinstance(issues, list)
        assert len(issues) > 0  # Should find at least some issues


# ═══════════════════════════════════════
# Analyst Agent Tests
# ═══════════════════════════════════════

class TestAnalystAgent:
    """Tests for the Analyst Agent (rule-based mode, no LLM)."""
    
    def test_analyst_finds_insights(self, cleaned_dataframe, sample_cleaning_summary):
        """Analyst should find 3-5 insights from the data."""
        agent = AnalystAgent()
        result = agent.run({
            "cleaned_df": cleaned_dataframe,
            "cleaning_summary": sample_cleaning_summary,
        })
        
        assert result.success, f"Analyst failed: {result.errors}"
        findings = result.data.get("findings", [])
        assert len(findings) >= 1, "Should find at least 1 insight"
        assert len(findings) <= 5, "Should find at most 5 insights"
    
    def test_analyst_finding_structure(self, cleaned_dataframe, sample_cleaning_summary):
        """Each finding should have the required fields."""
        agent = AnalystAgent()
        result = agent.run({
            "cleaned_df": cleaned_dataframe,
            "cleaning_summary": sample_cleaning_summary,
        })
        
        for finding in result.data["findings"]:
            assert "id" in finding
            assert "title" in finding
            assert "chart_type" in finding
            assert finding["chart_type"] in ("bar", "line", "scatter", "pie", "heatmap")
    
    def test_analyst_handles_empty_df(self):
        """Analyst should handle empty DataFrame gracefully."""
        agent = AnalystAgent()
        result = agent.run({
            "cleaned_df": pd.DataFrame(),
            "cleaning_summary": {},
        })
        
        assert result.success
        assert result.data["findings"] == []


# ═══════════════════════════════════════
# Visualizer Agent Tests
# ═══════════════════════════════════════

class TestVisualizerAgent:
    """Tests for the Visualizer Agent (rule-based, matplotlib)."""
    
    def test_visualizer_creates_charts(self, cleaned_dataframe, sample_findings, temp_output_dir):
        """Visualizer should generate chart files for each finding."""
        agent = VisualizerAgent()
        result = agent.run({
            "cleaned_df": cleaned_dataframe,
            "findings": sample_findings,
            "output_dir": temp_output_dir,
        })
        
        assert result.success, f"Visualizer failed: {result.errors}"
        charts = result.data.get("charts", [])
        assert len(charts) > 0, "Should generate at least 1 chart"
    
    def test_visualizer_saves_png_files(self, cleaned_dataframe, sample_findings, temp_output_dir):
        """Charts should be saved as PNG files that exist on disk."""
        agent = VisualizerAgent()
        result = agent.run({
            "cleaned_df": cleaned_dataframe,
            "findings": sample_findings,
            "output_dir": temp_output_dir,
        })
        
        for chart in result.data.get("charts", []):
            assert os.path.exists(chart["file_path"]), f"Chart file missing: {chart['file_path']}"
            assert chart["file_path"].endswith(".png")
    
    def test_visualizer_handles_no_findings(self, cleaned_dataframe, temp_output_dir):
        """Visualizer should handle empty findings list gracefully."""
        agent = VisualizerAgent()
        result = agent.run({
            "cleaned_df": cleaned_dataframe,
            "findings": [],
            "output_dir": temp_output_dir,
        })
        
        assert result.success
        assert result.data.get("charts", []) == []


# ═══════════════════════════════════════
# Explainer Agent Tests
# ═══════════════════════════════════════

class TestExplainerAgent:
    """Tests for the Explainer Agent (template mode, no LLM)."""
    
    def test_explainer_generates_report(self, sample_cleaning_summary, sample_findings):
        """Explainer should produce a markdown report."""
        agent = ExplainerAgent()
        result = agent.run({
            "cleaning_summary": sample_cleaning_summary,
            "findings": sample_findings,
            "charts": [{"finding_id": "finding_1", "file_path": "/tmp/chart1.png", "chart_type": "bar", "title": "Revenue"}],
        })
        
        assert result.success, f"Explainer failed: {result.errors}"
        assert "report_markdown" in result.data
        assert len(result.data["report_markdown"]) > 100
    
    def test_explainer_report_structure(self, sample_cleaning_summary, sample_findings):
        """Report should contain Overview, Key Insights, What This Means."""
        agent = ExplainerAgent()
        result = agent.run({
            "cleaning_summary": sample_cleaning_summary,
            "findings": sample_findings,
            "charts": [],
        })
        
        sections = result.data.get("report_sections", {})
        assert "overview" in sections
        assert "key_insights" in sections
        assert "what_this_means" in sections
    
    def test_explainer_handles_no_findings(self, sample_cleaning_summary):
        """Explainer should gracefully handle empty findings."""
        agent = ExplainerAgent()
        result = agent.run({
            "cleaning_summary": sample_cleaning_summary,
            "findings": [],
            "charts": [],
        })
        
        assert result.success
        assert "report_markdown" in result.data


# ═══════════════════════════════════════
# Integration Test — Full Pipeline
# ═══════════════════════════════════════

class TestFullPipeline:
    """Integration test: runs the full pipeline end-to-end."""
    
    def test_pipeline_end_to_end(self, sample_csv_bytes, tmp_path):
        """Full pipeline should process a CSV and produce a report."""
        # Set up storage directory
        os.environ["STORAGE_LOCAL_PATH"] = str(tmp_path / "storage")
        
        from app.services.orchestrator import PipelineOrchestrator
        
        statuses = []
        def track_status(status):
            statuses.append(status.to_dict())
        
        orchestrator = PipelineOrchestrator()
        result = orchestrator.run(
            file_bytes=sample_csv_bytes,
            filename="test.csv",
            on_status_update=track_status,
        )
        
        # Pipeline should complete successfully
        assert result.success, f"Pipeline failed: {result.error}"
        
        # Should have cleaning summary
        assert result.cleaning_summary
        assert result.cleaning_summary["rows_before"] > 0
        
        # Should have findings
        assert len(result.findings) >= 1
        
        # Should have a report
        assert len(result.report_markdown) > 100
        
        # Status updates should have been recorded
        assert len(statuses) >= 3  # At least cleaning, analyzing, completed
        
        # Final status should be completed
        assert statuses[-1]["status"] == "completed"
        
        print(f"\n✅ Pipeline completed successfully!")
        print(f"   Rows analyzed: {result.cleaning_summary['rows_after']}")
        print(f"   Findings: {len(result.findings)}")
        print(f"   Charts: {len(result.charts)}")
        print(f"   Duration: {result.total_duration_seconds}s")

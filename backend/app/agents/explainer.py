import logging
import datetime
from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.config import settings

logger = logging.getLogger(__name__)

class ExplainerAgent(BaseAgent):
    """
    Explainer Agent
    
    Role: Synthesize findings, charts, and cleaning details into an engaging,
    plain-English markdown report.
    
    Why it exists:
    Stakeholders need to understand the data without having to parse raw JSON
    findings or understand technical jargon. This agent translates technical
    results into a business-friendly format, optionally enhancing the text
    using an LLM for readability and engagement.
    """
    
    name = "ExplainerAgent"
    role = "Business Report Writer"
    
    def execute(self, input_data: dict) -> dict:
        """
        Executes the Explainer Agent logic.
        
        Args:
            input_data (dict): Contains 'cleaning_summary', 'findings', and 'charts'.
            
        Returns:
            dict: The generated report markdown and structured sections.
        """
        try:
            # Extract inputs
            cleaning_summary = input_data.get("cleaning_summary", {})
            findings = input_data.get("findings", [])
            charts = input_data.get("charts", [])
            
            # Map charts by finding_id for easy lookup
            chart_map = {c.get("finding_id"): c.get("file_path") for c in charts if c.get("finding_id")}
            
            # 1. Template-based Generation
            rows = cleaning_summary.get("initial_rows", 0)
            cols = cleaning_summary.get("initial_cols", 0)
            report_sections = self._generate_template_sections(cleaning_summary, findings, chart_map)
            report_markdown = self._build_markdown(report_sections, rows, cols)
            
            # 2. LLM Enhancement (if enabled)
            if getattr(settings, "llm_enabled", False) and getattr(settings, "groq_api_key", None):
                try:
                    enhanced_markdown = self._enhance_with_llm(report_markdown)
                    if enhanced_markdown:
                        report_markdown = enhanced_markdown
                except Exception as e:
                    logger.warning(f"LLM enhancement failed, falling back to template: {str(e)}")
            
            return {
                "report_markdown": report_markdown,
                "report_sections": report_sections
            }
            
        except Exception as e:
            logger.error(f"ExplainerAgent failed: {str(e)}")
            raise

    def _generate_template_sections(self, cleaning_summary: dict, findings: list, chart_map: dict) -> dict:
        """Generates structured report sections based on templates."""
        # Overview — use actual keys from the cleaner agent's output
        rows = cleaning_summary.get("rows_before", 0)
        cols = len(cleaning_summary.get("columns", []))
        rows_after = cleaning_summary.get("rows_after", rows)
        duplicates_removed = cleaning_summary.get("duplicates_removed", 0)
        missing_actions = cleaning_summary.get("missing_values_action", {})
        issues_list = cleaning_summary.get("issues", [])
        
        # Count total fixes applied
        filled_count = sum(1 for v in missing_actions.values() if "filled" in str(v))
        issues_count = len(issues_list)
        
        fixes = []
        if duplicates_removed > 0:
            fixes.append(f"removing {duplicates_removed} duplicate rows")
        if filled_count > 0:
            fixes.append(f"filling missing values in {filled_count} columns")
        if rows != rows_after:
            fixes.append(f"reducing from {rows} to {rows_after} rows")
            
        summary_of_fixes = ", ".join(fixes) if fixes else "no major fixes required"
        
        overview = f"This report analyzes a dataset with {rows} rows and {cols} columns. During data preparation, {issues_count} data quality issues were addressed, including {summary_of_fixes}."
        
        # Key Insights
        key_insights = []
        if not findings:
            key_insights.append({
                "title": "No Significant Patterns",
                "body": "No significant patterns were found in the dataset.",
                "chart_path": None
            })
        else:
            for i, f in enumerate(findings, 1):
                finding_id = f.get("id")
                title = f.get("title", f.get("type", "Insight").capitalize())
                desc = f.get("description", "")
                evidence = f.get("evidence", {})
                
                evidence_str = ", ".join(f"{k}: {v}" for k, v in evidence.items())
                body = f"{desc} Key metrics: {evidence_str}."
                
                chart_path = chart_map.get(finding_id)
                
                key_insights.append({
                    "title": title,
                    "body": body,
                    "chart_path": chart_path
                })
        
        # What this means
        if not findings:
            what_this_means = "Because no significant patterns were identified, there are no specific actionable takeaways at this time. Consider collecting more data or expanding the scope of the analysis."
        else:
            what_this_means = f"The data reveals {len(findings)} key insights. These patterns suggest areas for potential optimization. Focusing on the top findings could lead to measurable improvements."
            
        return {
            "overview": overview,
            "key_insights": key_insights,
            "what_this_means": what_this_means
        }
        
    def _build_markdown(self, sections: dict, rows: int, cols: int) -> str:
        """Builds the full markdown string from the report sections."""
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        md = f"""# 📊 Data Analysis Report\n\n**Generated on**: {date_str}\n**Dataset**: {rows} rows × {cols} columns\n\n---\n\n## 📋 Overview\n{sections['overview']}\n\n## 🔍 Key Insights\n\n"""
        
        for insight in sections['key_insights']:
            md += f"### Insight: {insight['title']}\n"
            md += f"{insight['body']}\n"
            if insight['chart_path']:
                md += f"![Chart]({insight['chart_path']})\n"
            md += "\n"
            
        md += f"""## 💡 What This Means\n{sections['what_this_means']}\n\n---\n*Report generated by Multi-Agent Data Analyst*\n"""
        return md

    def _enhance_with_llm(self, template_md: str) -> str:
        """Enhances the generated markdown report using Groq LLM."""
        from groq import Groq
        
        client = Groq(api_key=settings.groq_api_key)
        
        system_prompt = (
            "You are a business report writer. Rewrite this data analysis report in clear, "
            "engaging, plain English that a non-technical CEO could understand. Keep the "
            "structure: Overview → Key Insights → What This Means. Use specific numbers "
            "from the data. Make it actionable. Do not use technical jargon like 'correlation', "
            "'standard deviation', or 'IQR'. Keep the markdown formatting."
        )
        
        model = getattr(settings, "groq_model", "llama-3.3-70b-versatile")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the raw report to enhance:\\n\\n{template_md}"}
            ],
            temperature=0.3,
            max_tokens=2048
        )
        
        return response.choices[0].message.content

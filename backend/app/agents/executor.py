"""
Executor Agent

Executes the planner's plan using PandasAI with Google Gemini API.
Generates Python code, executes it, and returns results with optional charts.
"""

import pandas as pd
import numpy as np
import re
import os
from typing import Optional, Any
from pandasai import SmartDataframe
from pandasai.llm.google_gemini import GoogleGemini
import google.generativeai as genai

from app.config import get_settings


class GeminiFlash(GoogleGemini):
    """
    Custom GoogleGemini LLM that uses gemini-1.5-flash model.
    Gemini 2.5 has issues with PandasAI - using 1.5 for better compatibility.
    """
    model: str = "models/gemini-1.5-flash"

    def _configure(self, api_key: str):
        """Configure with the correct model."""
        from pandasai.exceptions import APIKeyNotFoundError

        if not api_key:
            raise APIKeyNotFoundError("Google Gemini API key is required")

        genai.configure(api_key=api_key)
        self.google_gemini = genai.GenerativeModel(self.model)



class ExecutorAgent:
    """
    Agent 2: The Executor

    Uses PandasAI with Google Gemini API to:
    - Receive execution plan from Planner
    - Execute data analysis using natural language
    - Generate visualizations when requested
    - Return structured results with chart configuration
    """

    def __init__(self):
        """Initialize the Executor Agent with PandasAI and Gemini."""
        settings = get_settings()

        # Initialize Google Gemini LLM for PandasAI
        # Using Gemini 1.5 Flash for better PandasAI compatibility
        self.llm = GeminiFlash(api_key=settings.gemini_api_key)
        
        # Chart export directory
        self.chart_dir = "exports/charts"
        os.makedirs(self.chart_dir, exist_ok=True)

    async def execute_plan(
        self,
        plan: str,
        df: pd.DataFrame,
        question: str,
    ) -> dict[str, Any]:
        """
        Execute the plan using PandasAI and return results.

        Args:
            plan: Execution plan from Planner agent
            df: Pandas DataFrame with the data
            question: Original user question

        Returns:
            Dictionary with:
            - answer: String answer to the question
            - chart_config: Optional chart configuration for visualization
        """
        try:
            # Create SmartDataframe with PandasAI
            smart_df = SmartDataframe(
                df,
                config={
                    "llm": self.llm,
                    "verbose": True,
                    "enable_cache": False,
                    "save_charts": True,
                    "save_charts_path": self.chart_dir,
                    "open_charts": False,
                    "enforce_privacy": False,
                    "enable_logging": False,
                },
            )

            # Create enhanced prompt that forces code generation
            enhanced_prompt = f"""
{question}

IMPORTANT: You must write Python code using pandas operations to answer this question.
Always return a concrete result (number, DataFrame, or value), never just an explanation.
"""

            # Execute the query using PandasAI
            print(f"⚡ PandasAI executing: {question[:100]}...")
            result = smart_df.chat(enhanced_prompt)
            print(f"✅ PandasAI result type: {type(result)}")

            # Check for chart file
            chart_path = self._find_generated_chart()
            
            # Process the result
            answer = self._format_result(result, question, chart_path)

            # Determine if chart is needed and generate config
            chart_config = self._generate_chart_config(plan, df, question, result)

            return {
                "answer": answer,
                "chart_config": chart_config,
            }

        except Exception as e:
            print(f"❌ Executor error: {e}")
            error_msg = str(e)
            
            # Better error messages
            if "No code found" in error_msg:
                return {
                    "answer": "I couldn't generate the analysis code. Let me try a different approach.",
                    "chart_config": self._generate_chart_config_fallback(plan, df, question),
                }
            
            return {
                "answer": f"I encountered an error while analyzing: {error_msg}. Please try rephrasing your question.",
                "chart_config": None,
            }

    def _generate_chart_config(
        self,
        plan: str,
        df: pd.DataFrame,
        question: str,
        result: Any,
    ) -> Optional[dict]:
        """
        Generate chart configuration based on the plan and result.

        Returns Recharts-compatible configuration.
        """
        # Check if visualization is needed
        if not self._needs_visualization(plan, question):
            return None

        chart_type = self._determine_chart_type(plan, question)

        if chart_type is None:
            return None

        try:
            # Generate chart data based on result type
            chart_data = self._prepare_chart_data(result, df, plan, question)

            if not chart_data or len(chart_data) == 0:
                return None

            # Determine keys for the chart
            x_key, y_key = self._determine_chart_keys(chart_data, plan, question)

            # Generate title
            title = self._generate_chart_title(question)

            return {
                "type": chart_type,
                "data": chart_data,
                "xKey": x_key,
                "yKey": y_key,
                "title": title,
            }

        except Exception as e:
            print(f"❌ Chart generation error: {e}")
            return None

    def _needs_visualization(self, plan: str, question: str) -> bool:
        """Determine if visualization is needed."""
        viz_keywords = [
            "chart", "graph", "plot", "visualize", "visualization",
            "show", "display", "trend", "compare", "comparison",
            "distribution", "pie", "bar", "line", "scatter"
        ]

        combined = (plan + " " + question).lower()
        return any(keyword in combined for keyword in viz_keywords)

    def _determine_chart_type(self, plan: str, question: str) -> Optional[str]:
        """Determine the appropriate chart type."""
        combined = (plan + " " + question).lower()

        if "pie chart" in combined or ("pie" in combined and "distribution" in combined):
            return "pie"
        elif "line chart" in combined or "trend" in combined or "over time" in combined or "over the years" in combined:
            return "line"
        elif "scatter" in combined or "correlation" in combined:
            return "scatter"
        elif "area" in combined:
            return "area"
        elif "bar" in combined or "compare" in combined or "top" in combined or "by category" in combined:
            return "bar"

        # Default to bar chart for most comparisons
        return "bar"

    def _prepare_chart_data(
        self,
        result: Any,
        df: pd.DataFrame,
        plan: str,
        question: str,
    ) -> list[dict]:
        """Prepare data for chart rendering."""
        if isinstance(result, pd.DataFrame) and not result.empty:
            # Convert DataFrame to list of dicts
            return result.head(20).to_dict(orient="records")

        if isinstance(result, pd.Series):
            # Convert Series to list of dicts
            return [
                {"name": str(idx), "value": float(val) if pd.notna(val) else 0}
                for idx, val in result.head(20).items()
            ]

        # Try to generate chart data from the original DataFrame
        return self._generate_chart_data_from_df(df, plan, question)

    def _generate_chart_data_from_df(
        self,
        df: pd.DataFrame,
        plan: str,
        question: str,
    ) -> list[dict]:
        """Generate chart data by analyzing the DataFrame based on the plan."""
        plan_lower = plan.lower()
        question_lower = question.lower()

        # Find potential grouping column (categorical)
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not cat_cols or not num_cols:
            return []

        # Use first categorical and numerical column as default
        group_col = cat_cols[0]
        value_col = num_cols[0]

        # Try to find better columns from the plan/question
        for col in cat_cols:
            if col.lower() in plan_lower or col.lower() in question_lower:
                group_col = col
                break

        for col in num_cols:
            if col.lower() in plan_lower or col.lower() in question_lower:
                value_col = col
                break

        # Generate aggregated data
        try:
            agg_data = df.groupby(group_col)[value_col].sum().head(10).reset_index()
            return agg_data.to_dict(orient="records")
        except Exception as e:
            print(f"❌ Chart data generation error: {e}")
            return []

    def _determine_chart_keys(
        self,
        chart_data: list[dict],
        plan: str,
        question: str,
    ) -> tuple[str, str]:
        """Determine x and y keys for the chart."""
        if not chart_data:
            return "name", "value"

        keys = list(chart_data[0].keys())

        # Find string key for x-axis and numeric key for y-axis
        x_key = keys[0] if keys else "name"
        y_key = keys[1] if len(keys) > 1 else "value"

        for key in keys:
            sample_value = chart_data[0].get(key)
            if isinstance(sample_value, str):
                x_key = key
            elif isinstance(sample_value, (int, float)):
                y_key = key

        return x_key, y_key

    def _generate_chart_title(self, question: str) -> str:
        """Generate a chart title from the question."""
        # Clean up the question to make a title
        title = question.strip().rstrip("?").rstrip(".")

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]

        # Truncate if too long
        if len(title) > 60:
            title = title[:57] + "..."

        return title
    
    def _find_generated_chart(self) -> Optional[str]:
        """Find the most recently generated chart file."""
        try:
            chart_files = [
                os.path.join(self.chart_dir, f)
                for f in os.listdir(self.chart_dir)
                if f.endswith('.png')
            ]
            
            if not chart_files:
                return None
                
            # Return most recent file
            latest_chart = max(chart_files, key=os.path.getmtime)
            return latest_chart
            
        except Exception as e:
            print(f"❌ Chart search error: {e}")
            return None
    
    def _generate_chart_config_fallback(self, plan: str, df: pd.DataFrame, question: str) -> Optional[dict]:
        """Generate chart config using direct pandas operations as fallback."""
        try:
            chart_type = self._determine_chart_type(plan, question)
            if not chart_type:
                return None
            
            chart_data = self._generate_chart_data_from_df(df, plan, question)
            if not chart_data:
                return None
            
            x_key, y_key = self._determine_chart_keys(chart_data, plan, question)
            title = self._generate_chart_title(question)
            
            return {
                "type": chart_type,
                "data": chart_data,
                "xKey": x_key,
                "yKey": y_key,
                "title": title,
            }
        except Exception as e:
            print(f"❌ Fallback chart generation error: {e}")
            return None

    def _format_result(self, result: Any, question: str, chart_path: Optional[str] = None) -> str:
        """Format the PandasAI result into a readable answer."""
        # If a chart was generated, return the path
        if chart_path:
            return chart_path
        
        if result is None:
            return "I couldn't find a specific answer. Please try rephrasing your question."

        if isinstance(result, pd.DataFrame):
            if result.empty:
                return "The query returned no results."
            # Limit to 20 rows for display
            if len(result) > 20:
                return f"Here are the top 20 results:\n\n{result.head(20).to_string(index=False)}\n\n(Showing 20 of {len(result)} rows)"
            return f"Here are the results:\n\n{result.to_string(index=False)}"

        if isinstance(result, pd.Series):
            if len(result) > 20:
                return f"Results (top 20):\n{result.head(20).to_string()}"
            return f"Results:\n{result.to_string()}"

        if isinstance(result, (np.floating, float)):
            val = float(result)
            if abs(val) >= 1000:
                return f"The answer is: **{val:,.2f}**"
            return f"The answer is: **{val:.4f}**"

        if isinstance(result, (np.integer, int)):
            return f"The answer is: **{int(result):,}**"

        if isinstance(result, list):
            if len(result) > 20:
                items = result[:20]
                return "Results (top 20):\n" + "\n".join(f"• {item}" for item in items)
            return "Results:\n" + "\n".join(f"• {item}" for item in result)

        if isinstance(result, dict):
            return "Results:\n" + "\n".join(f"• {k}: {v}" for k, v in result.items())

        # For string results from PandasAI
        return str(result)

"""
Executor Agent

Executes the planner's plan using PandasAI with Google Gemini API.
Generates Python code, executes it, and returns results with optional charts.
"""

import pandas as pd
import numpy as np
import re
import os
import time
from typing import Optional, Any
from pandasai import Agent
from pandasai.llm.google_gemini import GoogleGemini
import google.generativeai as genai

from app.config import get_settings


# Patch GoogleGemini to use available model in v1beta API
class PatchedGoogleGemini(GoogleGemini):
    """GoogleGemini LLM patched to use models/gemini-1.0-pro."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
        # Override the model to use gemini-1.0-pro (available in v1beta)
        self.google_gemini = genai.GenerativeModel("models/gemini-1.0-pro")


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

        # Initialize Patched Google Gemini LLM for PandasAI with gemini-1.5-flash
        self.llm = PatchedGoogleGemini(api_key=settings.gemini_api_key)
        
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
        # Track timestamp before execution to find only new charts
        start_time = time.time()

        try:
            # Create PandasAI Agent with Gemini LLM
            agent = Agent(
                df,
                config={
                    "llm": self.llm,
                    "verbose": True,
                    "enable_cache": False,
                    "save_charts": True,
                    "save_charts_path": self.chart_dir,
                    "open_charts": False,
                },
            )

            # Create enhanced prompt that includes the plan for context
            enhanced_prompt = f"""
Based on the following analysis plan:
{plan}

User Question: {question}

IMPORTANT: You must write Python code using pandas operations to answer this question.
Always return a concrete result (number, DataFrame, or value), never just an explanation.
"""

            # Execute the query using PandasAI
            print(f"⚡ PandasAI executing: {question[:100]}...")
            result = agent.chat(enhanced_prompt)
            print(f"✅ PandasAI result type: {type(result)}")

            # Check if PandasAI returned an error string (it catches exceptions internally)
            if isinstance(result, str) and (
                "unfortunately" in result.lower() or
                "no code found" in result.lower() or
                "error" in result.lower()
            ):
                print(f"⚠️ PandasAI returned error string, using fallback")
                fallback_config = self._generate_chart_config_fallback(plan, df, question)
                fallback_answer = self._generate_fallback_answer(plan, df, question, fallback_config)
                return {
                    "answer": fallback_answer,
                    "chart_config": fallback_config,
                }

            # Check for chart file generated after start_time
            chart_path = self._find_generated_chart(start_time)

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

            # Better error messages with fallback chart generation
            if "No code found" in error_msg:
                fallback_config = self._generate_chart_config_fallback(plan, df, question)
                fallback_answer = self._generate_fallback_answer(plan, df, question, fallback_config)
                return {
                    "answer": fallback_answer,
                    "chart_config": fallback_config,
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
    
    def _find_generated_chart(self, after_timestamp: float = 0) -> Optional[str]:
        """Find a chart file generated after the given timestamp."""
        try:
            chart_files = [
                os.path.join(self.chart_dir, f)
                for f in os.listdir(self.chart_dir)
                if f.endswith('.png')
            ]

            if not chart_files:
                return None

            # Filter to only charts created after the timestamp
            new_charts = [
                f for f in chart_files
                if os.path.getmtime(f) > after_timestamp
            ]

            if not new_charts:
                return None

            # Return most recent new file
            latest_chart = max(new_charts, key=os.path.getmtime)
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

    def _generate_fallback_answer(
        self,
        plan: str,
        df: pd.DataFrame,
        question: str,
        chart_config: Optional[dict],
    ) -> str:
        """Generate a text answer when PandasAI fails, using the plan and data."""
        try:
            plan_lower = plan.lower()

            # Check if the plan indicates insufficient/missing data
            insufficient_indicators = [
                "insufficient data",
                "cannot be answered",
                "cannot be calculated",
                "no such column",
                "not available",
                "none (insufficient",
                "none (cannot be",
                "data columns needed:** none",
            ]

            for indicator in insufficient_indicators:
                if indicator in plan_lower:
                    # Extract what's missing from the question context
                    if "return" in question.lower():
                        return "This question cannot be answered because the dataset doesn't contain information about returns (e.g., a 'Returned' column or return status)."
                    else:
                        return "This question cannot be answered with the available data. The required information is not present in the dataset."

            # Check for empty question
            if not question or not question.strip():
                return "Please provide a question about your data."

            # If we have chart data, summarize it
            if chart_config and chart_config.get("data"):
                data = chart_config["data"]
                x_key = chart_config.get("xKey", "name")
                y_key = chart_config.get("yKey", "value")

                # Build a text summary
                summary_lines = []
                for item in data[:5]:  # Top 5 items
                    x_val = item.get(x_key, "Unknown")
                    y_val = item.get(y_key, 0)
                    if isinstance(y_val, (int, float)):
                        summary_lines.append(f"• {x_val}: {y_val:,.2f}")
                    else:
                        summary_lines.append(f"• {x_val}: {y_val}")

                if summary_lines:
                    return "Here are the results:\n\n" + "\n".join(summary_lines)

            # Generic fallback
            return "I analyzed the data based on your question. Please see the chart for visual results."

        except Exception as e:
            print(f"❌ Fallback answer generation error: {e}")
            return "I encountered an issue generating the analysis. Please try rephrasing your question."

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

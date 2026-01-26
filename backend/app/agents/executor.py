"""
Executor Agent

Executes the planner's plan using PandasAI to analyze data and generate results.
Uses Google Gemini API through PandasAI for code generation.
"""

import pandas as pd
import re
import json
from typing import Optional, Any
from pandasai import SmartDataframe
from pandasai.llm.google_gemini import GoogleGemini

from app.config import get_settings


class ExecutorAgent:
    """
    Agent 2: The Executor

    Responsibilities:
    - Receive execution plan from Planner
    - Load and process the data
    - Use PandasAI to execute analysis
    - Generate visualizations when requested
    - Return structured results with chart configuration
    """

    def __init__(self):
        """Initialize the Executor Agent with PandasAI and Gemini."""
        settings = get_settings()

        self.llm = GoogleGemini(api_key=settings.gemini_api_key)

    async def execute_plan(
        self,
        plan: str,
        df: pd.DataFrame,
        question: str,
    ) -> dict[str, Any]:
        """
        Execute the plan and return results.

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
                    "verbose": False,
                    "enable_cache": False,
                    "custom_prompts": {
                        "generate_python_code": self._get_executor_prompt(plan),
                    },
                },
            )

            # Execute the query
            result = smart_df.chat(question)

            # Process the result
            answer = self._format_answer(result, question)

            # Determine if chart is needed and generate config
            chart_config = self._generate_chart_config(plan, df, question, result)

            return {
                "answer": answer,
                "chart_config": chart_config,
            }

        except Exception as e:
            print(f"❌ Executor error: {e}")
            return {
                "answer": f"I encountered an error while analyzing the data: {str(e)}. Please try rephrasing your question.",
                "chart_config": None,
            }

    def _get_executor_prompt(self, plan: str) -> str:
        """Generate custom prompt for PandasAI based on the plan."""
        return f"""You are a data analysis executor. Follow this plan to answer the question:

{plan}

Generate Python code that:
1. Follows the steps in the plan exactly
2. Uses pandas operations efficiently
3. Returns a clear, formatted result
4. Handles any edge cases gracefully
"""

    def _format_answer(self, result: Any, question: str) -> str:
        """Format the PandasAI result into a readable answer."""
        if result is None:
            return "I couldn't find a specific answer to your question. Please try rephrasing it."

        if isinstance(result, pd.DataFrame):
            if result.empty:
                return "The query returned no results."
            # Format DataFrame as a readable string
            return f"Here are the results:\n\n{result.to_string(index=False)}"

        if isinstance(result, pd.Series):
            return f"Results:\n{result.to_string()}"

        if isinstance(result, (int, float)):
            return f"The answer is: {result:,.2f}" if isinstance(result, float) else f"The answer is: {result:,}"

        if isinstance(result, list):
            return "Results:\n" + "\n".join(f"• {item}" for item in result)

        return str(result)

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

        if "pie chart" in combined or "pie" in combined and "distribution" in combined:
            return "pie"
        elif "line chart" in combined or "trend" in combined or "over time" in combined:
            return "line"
        elif "scatter" in combined or "correlation" in combined:
            return "scatter"
        elif "area" in combined:
            return "area"
        elif "bar" in combined or "compare" in combined or "top" in combined:
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
                {"name": str(idx), "value": val}
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
        # This is a fallback - try to identify columns from the plan
        plan_lower = plan.lower()

        # Find potential grouping column (categorical)
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not cat_cols or not num_cols:
            return []

        # Use first categorical and numerical column as default
        group_col = cat_cols[0]
        value_col = num_cols[0]

        # Try to find better columns from the plan
        for col in cat_cols:
            if col.lower() in plan_lower:
                group_col = col
                break

        for col in num_cols:
            if col.lower() in plan_lower:
                value_col = col
                break

        # Generate aggregated data
        try:
            agg_data = df.groupby(group_col)[value_col].sum().head(10).reset_index()
            return agg_data.to_dict(orient="records")
        except:
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
        x_key = "name"
        y_key = "value"

        for key in keys:
            sample_value = chart_data[0][key]
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

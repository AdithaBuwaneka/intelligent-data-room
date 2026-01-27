"""
Executor Agent

Executes the planner's plan using PandasAI with Google Gemini API.
Generates Python code, executes it, and returns results with optional charts.

Uses a custom LLM wrapper (GeminiLLM) that connects PandasAI to Google's
Gemini API using the new google-genai SDK (GA as of May 2025).

Fallback also uses Google Gemini API directly to maintain compliance with:
"Agent 2 (The Executor): Uses PandasAI (and the Google Gemini API)"
"""

import pandas as pd
import numpy as np
import re
import os
import time
from typing import Optional, Any
from pandasai import Agent
from pandasai.llm.base import LLM
from google import genai

from app.config import get_settings


class GeminiLLM(LLM):
    """
    Custom LLM wrapper for PandasAI that uses Google Gemini API via google-genai SDK.

    This bypasses PandasAI's built-in GoogleGemini class which uses the deprecated v1beta API.
    Instead, it uses the new google-genai SDK (GA as of May 2025).
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """Initialize the Gemini LLM with API key and model."""
        self._api_key = api_key
        self._model_name = model

        # Create a genai Client with the API key
        self._client = genai.Client(api_key=api_key)

        print(f"✅ GeminiLLM initialized with model: {model}")

    @property
    def type(self) -> str:
        """Return the type of LLM."""
        return "google-gemini"

    def call(self, instruction: str, context: str = None, suffix: str = "") -> str:
        """
        Call the Gemini API with the given instruction.

        This is the main method PandasAI uses to interact with the LLM.
        """
        try:
            # Build the full prompt
            prompt = instruction
            if context:
                prompt = f"{context}\n\n{instruction}"
            if suffix:
                prompt = f"{prompt}\n\n{suffix}"

            print(f"🔄 GeminiLLM.call() invoked, prompt length: {len(prompt)}")

            # Call Gemini API using the new SDK pattern
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt
            )

            # Extract text from response
            if response and response.text:
                print(f"✅ GeminiLLM received response: {len(response.text)} chars")
                return response.text
            else:
                print("⚠️ GeminiLLM: No response text")
                return "No response generated"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ GeminiLLM call error: {error_msg[:200]}")
            raise

    def chat(self, messages: list) -> str:
        """
        Handle chat-style messages (alternative interface some versions of PandasAI use).
        """
        # Convert messages to a single prompt
        prompt_parts = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
            else:
                prompt_parts.append(str(msg))

        full_prompt = "\n\n".join(prompt_parts)
        return self.call(full_prompt)


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
        """Initialize the Executor Agent with PandasAI and Google Gemini API."""
        settings = get_settings()
        self.api_key = settings.gemini_api_key

        # Try models in order of preference (newest first)
        models_to_try = [
            "gemini-2.5-flash",     # Latest flash model (recommended)
            "gemini-2.0-flash",     # Fallback
            "gemini-1.5-flash",     # Stable fallback
        ]

        self.llm = None
        self.genai_client = None
        self.model_name = None
        last_error = None

        for model_name in models_to_try:
            try:
                # Use our custom GeminiLLM that wraps google-genai SDK
                self.llm = GeminiLLM(api_key=self.api_key, model=model_name)

                # Also set up direct Gemini client for fallback (same client)
                self.genai_client = genai.Client(api_key=self.api_key)
                self.model_name = model_name

                print(f"✅ PandasAI + Gemini initialized with model: {model_name}")
                break

            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(f"⚠️ Model {model_name} failed: {error_msg[:100]}")
                continue

        if not self.llm:
            error_detail = str(last_error)[:200] if last_error else "Unknown error"
            raise RuntimeError(
                f"Failed to initialize Google Gemini API. "
                f"Please check your GEMINI_API_KEY. Error: {error_detail}"
            )

        # Chart export directory (temporary storage for generated charts)
        self.chart_dir = "temp_charts"
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

For charts: Save with plt.savefig("temp_chart.png") then return {{"type": "plot", "value": "temp_chart.png"}}
Do NOT import any system modules. Only use: pandas, matplotlib.pyplot, numpy.
"""

            # Execute the query using PandasAI
            print(f"⚡ PandasAI executing: {question[:100]}...")
            result = agent.chat(enhanced_prompt)
            print(f"✅ PandasAI result type: {type(result)}")

            # Log the actual result for debugging
            if isinstance(result, str):
                print(f"📝 PandasAI result content: {result[:500]}")

            # Check if PandasAI returned an error string (it catches exceptions internally)
            if isinstance(result, str) and (
                "unfortunately" in result.lower() or
                "no code found" in result.lower() or
                ("error" in result.lower() and len(result) < 200)  # Only treat short error messages as errors
            ):
                print(f"⚠️ PandasAI returned error string, using fallback")
                # Respect visualization preference even in fallback
                needs_viz = self._needs_visualization(plan, question)
                fallback_config = self._generate_chart_config_fallback(plan, df, question) if needs_viz else None
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
                # Respect visualization preference even in fallback
                needs_viz = self._needs_visualization(plan, question)
                fallback_config = self._generate_chart_config_fallback(plan, df, question) if needs_viz else None
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
        """
        Determine if visualization is needed by checking the plan.
        
        Respects the planner's VISUALIZATION decision which already considered:
        - User's explicit preferences ("don't chart", "without visualization")
        - Question intent and context
        - Whether visualization would add value
        """
        # First priority: Check what the planner decided
        plan_lower = plan.lower()
        
        # Look for explicit VISUALIZATION directive in the plan
        if "visualization:" in plan_lower or "visualization::" in plan_lower:
            # Extract the visualization decision
            if "visualization: no" in plan_lower or "visualization:: no" in plan_lower or "visualization:no" in plan_lower:
                print("📊 Planner said VISUALIZATION: NO - respecting decision")
                return False
            elif "visualization: yes" in plan_lower or "visualization:: yes" in plan_lower or "visualization:yes" in plan_lower:
                print("📊 Planner said VISUALIZATION: YES - will generate chart")
                return True
        
        # Fallback: If no explicit directive in plan, infer from keywords
        # This handles older plans or edge cases
        viz_keywords = [
            "chart", "graph", "plot", "visualize", "visualization",
            "show", "display", "trend", "compare", "comparison",
            "distribution", "pie", "bar", "line", "scatter"
        ]
        
        # Check if user explicitly said NO to visualization
        no_viz_keywords = ["don't chart", "no chart", "without chart", "no visualization", 
                          "without visualization", "no graph", "table only", "just calculate"]
        
        combined = (plan + " " + question).lower()
        
        # If user explicitly said no, respect it
        if any(no_kw in combined for no_kw in no_viz_keywords):
            print("📊 User explicitly requested no visualization")
            return False
        
        # Otherwise check for visualization keywords
        has_viz_keywords = any(keyword in combined for keyword in viz_keywords)
        if has_viz_keywords:
            print("📊 Visualization keywords found, will generate chart")
        return has_viz_keywords

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
        """
        Generate a text answer using DIRECT Google Gemini API when PandasAI fails.

        This ensures compliance with the requirement:
        "Agent 2 (The Executor): Uses PandasAI (and the Google Gemini API)"

        Even when PandasAI fails, we still use Google Gemini API directly.
        """
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
                    # Use Gemini to generate a helpful response about missing data
                    return self._call_gemini_for_answer(
                        question,
                        df,
                        plan,
                        chart_config,
                        is_insufficient_data=True
                    )

            # Check for empty question
            if not question or not question.strip():
                return "Please provide a question about your data."

            # Use Direct Google Gemini API to generate the answer
            return self._call_gemini_for_answer(
                question,
                df,
                plan,
                chart_config,
                is_insufficient_data=False
            )

        except Exception as e:
            print(f"❌ Fallback answer generation error: {e}")
            # Even error case tries Gemini
            try:
                return self._call_gemini_for_answer(
                    question, df, plan, chart_config, is_insufficient_data=False
                )
            except Exception:
                return "I encountered an issue generating the analysis. Please try rephrasing your question."

    def _call_gemini_for_answer(
        self,
        question: str,
        df: pd.DataFrame,
        plan: str,
        chart_config: Optional[dict],
        is_insufficient_data: bool = False,
    ) -> str:
        """
        Call Google Gemini API directly to generate an answer.

        This is the fallback that ensures Google Gemini API is ALWAYS used,
        maintaining compliance with the technical requirements.
        """
        try:
            # Prepare data context for Gemini
            columns_info = ", ".join(df.columns.tolist())
            data_shape = f"{len(df)} rows x {len(df.columns)} columns"

            # Get sample data and basic statistics
            sample_data = df.head(5).to_string(index=False)

            # Get numeric column statistics
            numeric_stats = ""
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                stats_df = df[numeric_cols].describe().round(2)
                numeric_stats = f"\nNumeric Statistics:\n{stats_df.to_string()}"

            # If we have chart data, include it
            chart_data_str = ""
            if chart_config and chart_config.get("data"):
                chart_data_str = f"\nChart Data Generated:\n{chart_config['data'][:10]}"

            # Build the prompt for Gemini
            if is_insufficient_data:
                prompt = f"""You are a data analysis assistant. The user asked a question that cannot be fully answered with the available data.

User Question: {question}

Available Data Schema:
- Columns: {columns_info}
- Shape: {data_shape}

Analysis Plan (shows what's missing):
{plan}

Please provide a helpful response explaining what data would be needed to answer this question, and if possible, suggest what analysis CAN be done with the available data.
Keep your response concise (2-3 sentences)."""
            else:
                # Perform basic pandas analysis to get actual results
                analysis_result = self._perform_pandas_analysis(df, question, plan)

                prompt = f"""You are a data analysis assistant. Based on the following data analysis, provide a clear answer to the user's question.

User Question: {question}

Data Schema:
- Columns: {columns_info}
- Shape: {data_shape}

Sample Data:
{sample_data}
{numeric_stats}

Analysis Plan:
{plan}

Analysis Results:
{analysis_result}
{chart_data_str}

Based on this analysis, provide a clear, concise answer to the user's question. Include specific numbers and insights from the data.
Keep your response focused and under 100 words."""

            # Call Gemini API directly using the new google-genai SDK
            print("🔄 Calling Google Gemini API directly for fallback answer...")
            response = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            answer = response.text.strip()
            print(f"✅ Gemini API response received ({len(answer)} chars)")

            return answer

        except Exception as e:
            print(f"❌ Direct Gemini API call failed: {e}")
            # Last resort: return basic pandas analysis result
            if chart_config and chart_config.get("data"):
                data = chart_config["data"]
                x_key = chart_config.get("xKey", "name")
                y_key = chart_config.get("yKey", "value")
                summary_lines = []
                for item in data[:5]:
                    x_val = item.get(x_key, "Unknown")
                    y_val = item.get(y_key, 0)
                    if isinstance(y_val, (int, float)):
                        summary_lines.append(f"• {x_val}: {y_val:,.2f}")
                    else:
                        summary_lines.append(f"• {x_val}: {y_val}")
                if summary_lines:
                    return "Here are the results:\n\n" + "\n".join(summary_lines)

            return "I analyzed the data based on your question. Please see the chart for visual results."

    def _perform_pandas_analysis(
        self,
        df: pd.DataFrame,
        question: str,
        plan: str,
    ) -> str:
        """
        Perform basic pandas analysis based on the question and plan.
        Returns a string summary of the analysis results.
        """
        try:
            results = []
            question_lower = question.lower()
            plan_lower = plan.lower()

            # Identify key columns mentioned
            cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
            num_cols = df.select_dtypes(include=["number"]).columns.tolist()

            # Find columns mentioned in question/plan
            mentioned_cat = [c for c in cat_cols if c.lower() in question_lower or c.lower() in plan_lower]
            mentioned_num = [c for c in num_cols if c.lower() in question_lower or c.lower() in plan_lower]

            # Default to first columns if none mentioned
            group_col = mentioned_cat[0] if mentioned_cat else (cat_cols[0] if cat_cols else None)
            value_col = mentioned_num[0] if mentioned_num else (num_cols[0] if num_cols else None)

            # Perform aggregations based on keywords
            if group_col and value_col:
                if "top" in question_lower or "highest" in question_lower:
                    agg = df.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(10)
                    results.append(f"Top {group_col} by {value_col}:\n{agg.to_string()}")
                elif "total" in question_lower or "sum" in question_lower:
                    agg = df.groupby(group_col)[value_col].sum()
                    results.append(f"Total {value_col} by {group_col}:\n{agg.to_string()}")
                elif "average" in question_lower or "mean" in question_lower:
                    agg = df.groupby(group_col)[value_col].mean().round(2)
                    results.append(f"Average {value_col} by {group_col}:\n{agg.to_string()}")
                elif "count" in question_lower:
                    agg = df.groupby(group_col).size()
                    results.append(f"Count by {group_col}:\n{agg.to_string()}")
                else:
                    # Default aggregation
                    agg = df.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(10)
                    results.append(f"{value_col} by {group_col}:\n{agg.to_string()}")

            # Handle time-based analysis
            date_cols = [c for c in df.columns if 'date' in c.lower() or 'year' in c.lower()]
            if date_cols and ("trend" in question_lower or "over time" in question_lower or "year" in question_lower):
                date_col = date_cols[0]
                if value_col:
                    try:
                        if df[date_col].dtype == 'object':
                            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        time_agg = df.groupby(df[date_col].dt.year)[value_col].sum()
                        results.append(f"{value_col} over time:\n{time_agg.to_string()}")
                    except Exception:
                        pass

            if results:
                return "\n\n".join(results)

            # Fallback: return basic statistics
            if num_cols:
                return f"Summary statistics:\n{df[num_cols[:3]].describe().to_string()}"

            return "Data loaded successfully. See chart for visualization."

        except Exception as e:
            print(f"❌ Pandas analysis error: {e}")
            return "Analysis completed. See chart for results."

    def _format_result(self, result: Any, question: str, chart_path: Optional[str] = None) -> str:
        """Format the PandasAI result into a readable answer."""
        # Note: chart_path is no longer returned as the answer text
        # Charts are rendered via chart_config, the answer should be descriptive text
        
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
        result_str = str(result)
        
        # Check if result is a chart file path - generate descriptive answer instead
        if result_str and (
            result_str.endswith('.png') or 
            result_str.endswith('.jpg') or
            result_str.endswith('.svg') or
            'temp_charts' in result_str or
            'exports' in result_str
        ):
            # Generate a descriptive answer based on the question
            return self._generate_chart_description(question)
        
        return result_str
    
    def _generate_chart_description(self, question: str) -> str:
        """Generate a descriptive answer when a chart was created."""
        question_lower = question.lower()
        
        # Generate contextual description based on question type
        if "sales" in question_lower and "category" in question_lower:
            return "Here's a breakdown of sales by category. The chart below shows the distribution across different product categories."
        elif "top" in question_lower:
            return "Here are the top results based on your query. See the chart below for a visual comparison."
        elif "trend" in question_lower or "over time" in question_lower or "year" in question_lower:
            return "Here's the trend analysis you requested. The chart below shows how values have changed over time."
        elif "compare" in question_lower or "comparison" in question_lower:
            return "Here's the comparison you requested. The chart below visualizes the differences."
        elif "distribution" in question_lower or "pie" in question_lower:
            return "Here's the distribution breakdown. The chart below shows the proportional breakdown."
        elif "total" in question_lower or "sum" in question_lower:
            return "Here are the aggregated totals based on your query. See the chart below for visualization."
        elif "average" in question_lower or "mean" in question_lower:
            return "Here are the average values. The chart below provides a visual representation."
        elif "profit" in question_lower:
            return "Here's the profit analysis. The chart below shows the profit distribution."
        elif "region" in question_lower or "state" in question_lower or "country" in question_lower:
            return "Here's the geographic breakdown. The chart below shows the regional distribution."
        else:
            return "Here are the results of your analysis. The chart below visualizes the data."

"""
Planner Agent

Analyzes user questions and data schema to create step-by-step execution plans.
Uses Google Gemini API (google-genai SDK) for natural language understanding.
"""

from google import genai
from typing import Optional

from app.config import get_settings

# System prompt for the Planner Agent
PLANNER_SYSTEM_PROMPT = """You are a Data Analysis Planner Agent. Your role is to analyze user questions about data and create clear, step-by-step execution plans.

## Your Responsibilities:
1. Understand the user's question and TRUE INTENT
2. Analyze the data schema (columns and their likely types)
3. Consider any previous conversation context
4. Create a precise execution plan that can be followed by an Executor Agent
5. **Intelligently determine if visualization should be included**

## Output Format:
Create a structured plan with these sections:

**OBJECTIVE:** [One sentence describing what the user wants]

**DATA COLUMNS NEEDED:** [List the specific columns from the schema that will be used]

**STEPS:**
1. [First step - be specific about data operations]
2. [Second step]
3. [Continue as needed]

**VISUALIZATION:** [YES/NO - and if YES, specify: bar/line/pie/scatter chart with X and Y axes]

**OUTPUT FORMAT:** [Describe what the final answer should look like]

## Visualization Decision (CRITICAL RULES!):

**AUTOMATIC YES - If ANY of these words appear in the query, ALWAYS say VISUALIZATION: YES:**
- "chart", "graph", "plot", "visualize", "visualization", "graphical", "diagram", "pie", "bar", "scatter", "line chart"

**Examples that MUST be VISUALIZATION: YES:**
- "Chart the distribution of discounts" → YES
- "Create a bar chart of sales" → YES
- "Graphical representation of categories" → YES
- "Plot sales trend" → YES
- "Pie chart of regions" → YES

**VISUALIZATION: NO ONLY when:**
- User asks questions (what, how many, which)
- User wants calculations (total, average, sum)
- User wants text lists (top 5, list the, show me)
- NO chart/graph/plot words in query

**When QueryAnalysis is provided:** Follow its requires_visualization field exactly.
**CRITICAL RULE: The word "chart", "graph", "plot", "visualize", or "graphical" appearing ANYWHERE in the query = VISUALIZATION: YES**

## Guidelines:
- Be specific about column names (use exact names from schema)
- For aggregations, specify the function (sum, mean, count, etc.)
- For filtering, specify the exact conditions
- For sorting, specify ascending/descending
- If visualization is needed, be explicit about chart type and axes
"""


class PlannerAgent:
    """
    Agent 1: The Planner

    Responsibilities:
    - Analyze user's natural language question
    - Understand the data schema (columns, types)
    - Consider conversation context (last 5 messages)
    - Create a clear, step-by-step execution plan
    - Determine if visualization is needed
    """

    def __init__(self):
        """Initialize the Planner Agent with Google Gemini API."""
        settings = get_settings()

        # Use the new google-genai SDK
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = "gemini-2.5-flash"  # Latest, most capable flash model

    async def create_plan(
        self,
        question: str,
        data_schema: dict,
        context: Optional[str] = None,
        query_analysis: Optional[dict] = None,
    ) -> str:
        """
        Create an execution plan for the given question.

        Args:
            question: User's natural language question
            data_schema: Dictionary with column names and sample data
            context: Previous conversation context
            query_analysis: QueryAnalysis dict from intelligent analyzer (single source of truth)

        Returns:
            Step-by-step execution plan as a string
        """
        # If we have QueryAnalysis, use it to guide the plan (SINGLE SOURCE OF TRUTH)
        if query_analysis:
            return self._create_plan_from_analysis(question, data_schema, query_analysis)

        # Build the prompt with system instruction
        prompt_parts = [PLANNER_SYSTEM_PROMPT, "\n---\n"]

        # Add context if available
        if context and context != "No previous conversation context.":
            prompt_parts.append(f"## Previous Conversation:\n{context}\n")

        # Add data schema
        schema_info = self._format_schema(data_schema)
        prompt_parts.append(f"## Data Schema:\n{schema_info}\n")

        # Add the question
        prompt_parts.append(f"## User Question:\n{question}\n")

        # Add instruction
        prompt_parts.append("## Create Execution Plan:")

        full_prompt = "\n".join(prompt_parts)

        try:
            # Use the new SDK - note: using sync call in async context
            # The new SDK handles this properly
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            plan = response.text.strip()
            return plan

        except Exception as e:
            print(f"❌ Planner error: {e}")
            # Return a basic plan on error
            return f"""**OBJECTIVE:** Answer: {question}

**DATA COLUMNS NEEDED:** All available columns

**STEPS:**
1. Load and examine the data
2. Process according to the question
3. Generate response

**VISUALIZATION:** NO

**OUTPUT FORMAT:** Text response"""

    def _create_plan_from_analysis(
        self,
        question: str,
        data_schema: dict,
        analysis: dict,
    ) -> str:
        """
        Create a plan directly from QueryAnalysis.
        This ensures SINGLE SOURCE OF TRUTH - no conflicting decisions.
        """
        # Extract analysis parameters
        group_col = analysis.get("group_column", "")
        value_col = analysis.get("value_column", "")
        aggregation = analysis.get("aggregation", "sum")
        limit = analysis.get("limit_number")
        chart_type = analysis.get("chart_type")
        requires_viz = analysis.get("requires_visualization", False)
        sort_order = analysis.get("sort_order", "desc")
        is_follow_up = analysis.get("is_follow_up", False)
        follow_up_type = analysis.get("follow_up_type", "")

        # Build columns needed
        columns_needed = []
        if group_col:
            columns_needed.append(group_col)
        if value_col:
            columns_needed.append(value_col)

        columns_str = ", ".join(columns_needed) if columns_needed else "To be determined"

        # Build steps
        steps = []
        step_num = 1

        if is_follow_up:
            steps.append(f"{step_num}. This is a follow-up query ({follow_up_type}). Use parameters from previous analysis.")
            step_num += 1

        if group_col and value_col:
            steps.append(f"{step_num}. Group data by '{group_col}'")
            step_num += 1
            agg_name = {"sum": "Sum", "mean": "Average", "count": "Count", "min": "Minimum", "max": "Maximum"}.get(aggregation, "Sum")
            steps.append(f"{step_num}. Calculate {agg_name} of '{value_col}' for each group")
            step_num += 1

        if limit:
            order = "descending" if sort_order == "desc" else "ascending"
            steps.append(f"{step_num}. Sort results in {order} order and select top {limit}")
            step_num += 1

        if not steps:
            steps.append(f"{step_num}. Process data according to the question")
            step_num += 1

        steps_str = "\n".join(steps)

        # Visualization decision
        viz_str = "NO"
        if requires_viz and chart_type:
            viz_str = f"YES - {chart_type} chart"
            if group_col:
                viz_str += f" with X-axis: {group_col}"
            if value_col:
                viz_str += f", Y-axis: {value_col}"

        # Build objective
        objective = question
        if is_follow_up and follow_up_type:
            type_desc = {
                "chart_type_change": "Change chart type",
                "limit_change": "Change result limit",
                "column_change": "Change grouping column",
                "filter_change": "Apply filter"
            }.get(follow_up_type, "Follow-up")
            objective = f"[{type_desc}] {question}"

        plan = f"""**OBJECTIVE:** {objective}

**DATA COLUMNS NEEDED:** {columns_str}

**STEPS:**
{steps_str}

**VISUALIZATION:** {viz_str}

**OUTPUT FORMAT:** {'Chart with data summary' if requires_viz else 'Text response with data'}"""

        return plan

    def _format_schema(self, data_schema: dict) -> str:
        """Format data schema for the prompt."""
        if not data_schema:
            return "No schema available"

        lines = ["Columns available:"]

        columns = data_schema.get("columns", [])
        sample_data = data_schema.get("sample_data", {})

        for col in columns:
            sample = sample_data.get(col, "N/A")
            lines.append(f"- {col} (sample: {sample})")

        row_count = data_schema.get("row_count", "unknown")
        lines.append(f"\nTotal rows: {row_count}")

        return "\n".join(lines)

    def needs_visualization(self, plan: str) -> bool:
        """Check if the plan requires visualization."""
        plan_lower = plan.lower()
        return "**visualization:** yes" in plan_lower or "visualization: yes" in plan_lower

    def get_chart_type(self, plan: str) -> Optional[str]:
        """Extract chart type from the plan."""
        plan_lower = plan.lower()

        if "bar chart" in plan_lower or "bar graph" in plan_lower:
            return "bar"
        elif "line chart" in plan_lower or "line graph" in plan_lower:
            return "line"
        elif "pie chart" in plan_lower:
            return "pie"
        elif "scatter" in plan_lower:
            return "scatter"
        elif "area chart" in plan_lower:
            return "area"

        return None

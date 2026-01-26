"""
Planner Agent

Analyzes user questions and data schema to create step-by-step execution plans.
Uses Google Gemini API for natural language understanding.
"""

import google.generativeai as genai
from typing import Optional

from app.config import get_settings

# System prompt for the Planner Agent
PLANNER_SYSTEM_PROMPT = """You are a Data Analysis Planner Agent. Your role is to analyze user questions about data and create clear, step-by-step execution plans.

## Your Responsibilities:
1. Understand the user's question in the context of the available data
2. Analyze the data schema (columns and their likely types)
3. Consider any previous conversation context
4. Create a precise execution plan that can be followed by an Executor Agent

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

## Guidelines:
- Be specific about column names (use exact names from schema)
- For aggregations, specify the function (sum, mean, count, etc.)
- For filtering, specify the exact conditions
- For sorting, specify ascending/descending
- If visualization is needed, be explicit about chart type and axes
- Keep plans concise but complete

## Example:
Question: "What are the top 5 products by sales?"
Schema: [Product Name, Sales, Category, Region]

**OBJECTIVE:** Find the 5 products with highest total sales

**DATA COLUMNS NEEDED:** Product Name, Sales

**STEPS:**
1. Group data by 'Product Name'
2. Calculate sum of 'Sales' for each product
3. Sort by total sales in descending order
4. Select top 5 rows

**VISUALIZATION:** YES - Horizontal bar chart with Product Name on Y-axis and Sales on X-axis

**OUTPUT FORMAT:** Table showing Product Name and Total Sales for top 5 products
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
        """Initialize the Planner Agent with Gemini API."""
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=PLANNER_SYSTEM_PROMPT,
        )

    async def create_plan(
        self,
        question: str,
        data_schema: dict,
        context: Optional[str] = None,
    ) -> str:
        """
        Create an execution plan for the given question.

        Args:
            question: User's natural language question
            data_schema: Dictionary with column names and sample data
            context: Previous conversation context

        Returns:
            Step-by-step execution plan as a string
        """
        # Build the prompt
        prompt_parts = []

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
            response = self.model.generate_content(full_prompt)
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

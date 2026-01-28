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

## Intelligent Visualization Decision:

**Understand the user's TRUE INTENT - don't just match keywords:**

**User WANTS visualization when they:**
- Use visual action words in ANY language: "chart", "plot", "graph", "visualize", "draw", "show me visually"
- Ask for visual comparisons: "compare visually", "see the distribution", "display trends"
- Want to see patterns: "show the pattern", "illustrate the relationship"
- Any phrasing that implies wanting to SEE something visually

**User DOES NOT want visualization when they:**
- Use negative language: "don't", "without", "no need for", "skip the", "just calculate", "only numbers"
- Ask for specific formats: "table only", "list format", "text results", "numbers only"
- Focus purely on calculation: "calculate", "compute", "what is the number"
- Any phrasing that indicates they want data without visuals

**Smart Decision Making:**
- If user mentions BOTH (e.g., "chart the sales but don't show visualization"):
  → Understand the contradiction → Negative instruction takes priority → NO
  
- If unclear or ambiguous:
  → Consider question type:
    - Comparisons across categories → Often benefits from visualization
    - Trends over time → Often benefits from visualization  
    - Single values/counts → Usually doesn't need visualization
    - Top N items → Could benefit from visualization
  → Consider if user asked for it before in context
  → Make intelligent decision

- Focus on INTENT, not exact words:
  - "I want to see sales by region" (even without "chart") → Could benefit from visual → YES
  - "Give me the total sales number" → Just wants a number → NO
  - "How does profit compare across categories" → Comparison suggests visual → YES (unless they said no)

## Guidelines:
- Be specific about column names (use exact names from schema)
- For aggregations, specify the function (sum, mean, count, etc.)
- For filtering, specify the exact conditions
- For sorting, specify ascending/descending
- If visualization is needed, be explicit about chart type and axes
- Keep plans concise but complete
- **Use semantic understanding to interpret user intent**

## Examples:

**Example 1:**
Question: "What are the top 5 products by sales?"
→ Intent: Get top products. Could benefit visually but not explicitly requested.
→ Decision: YES (comparison across categories)

**Example 2:**
Question: "Calculate the Return Rate for each Region. Don't give any chart"
→ Intent: Calculate rates BUT explicitly doesn't want visualization
→ Decision: NO (negative instruction clear)

**Example 3:**  
Question: "Show me how profit changed over the years"
→ Intent: See changes/trends ("show me") 
→ Decision: YES (temporal trend, visual helps)

**Example 4:**
Question: "What's the total revenue?"
→ Intent: Get single number
→ Decision: NO (single value doesn't need chart)

**Example 5:**
Question: "Calculate and chart Return Rate by Region, but I only need the table"
→ Intent: Even though "chart" mentioned, "only need the table" overrides
→ Decision: NO (negative instruction in context)
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

"""
Intelligent Query Analyzer

Uses Gemini 2.5 to intelligently analyze queries and make ALL decisions:
- Is this a valid/meaningful data query?
- Should visualization be shown?
- What chart type?
- What columns to use?
- What limit number?
- What aggregation?

This replaces ALL keyword-based logic with AI understanding.
Handles billions of phrase variations intelligently.
"""

import json
import re
from typing import Optional, Any
from google import genai
from pydantic import BaseModel, Field

from app.config import get_settings


class QueryAnalysis(BaseModel):
    """Structured analysis result from Gemini."""

    is_meaningful_query: bool = Field(
        description="Whether this is a meaningful data analysis question"
    )
    can_be_answered: bool = Field(
        description="Whether this can be answered with the available data"
    )
    requires_visualization: bool = Field(
        default=False,
        description="Whether a chart should be shown"
    )
    chart_type: Optional[str] = Field(
        default=None,
        description="Chart type: bar, line, pie, scatter, area, or null"
    )
    limit_number: Optional[int] = Field(
        default=None,
        description="Number limit if user asked for top N, bottom N, etc."
    )
    group_column: Optional[str] = Field(
        default=None,
        description="Column to group by (exact column name from schema)"
    )
    value_column: Optional[str] = Field(
        default=None,
        description="Column for values/aggregation (exact column name from schema)"
    )
    aggregation: Optional[str] = Field(
        default=None,
        description="Aggregation type: sum, mean, count, min, max, or null"
    )
    sort_order: Optional[str] = Field(
        default=None,
        description="Sort order: desc (for top), asc (for bottom), or null"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Explanation if query cannot be answered"
    )
    suggested_response: Optional[str] = Field(
        default=None,
        description="Suggested response for unclear/invalid queries"
    )
    # NEW: Follow-up handling fields
    is_follow_up: bool = Field(
        default=False,
        description="True if this is a follow-up to previous query"
    )
    follow_up_type: Optional[str] = Field(
        default=None,
        description="Type of follow-up: 'chart_type_change', 'limit_change', 'filter_change', 'column_change', or null"
    )
    inherit_from_previous: bool = Field(
        default=False,
        description="True if should inherit columns/aggregation from previous analysis"
    )


ANALYZER_SYSTEM_PROMPT = """You are an intelligent Query Analyzer for a Data Analysis system. Your job is to analyze user queries and return a structured JSON decision.

## CRITICAL: You Must Use SEMANTIC UNDERSTANDING, Not Keyword Matching!

You are a state-of-the-art language model. You must understand the user's TRUE INTENT from their message, regardless of:
- How they phrase it (formal, casual, broken English, slang)
- What specific words they use
- Whether they use complete sentences or fragments
- Regional language variations
- Typos and misspellings

**DO NOT match keywords. UNDERSTAND meaning.**

For example, ALL of these mean the user wants a visual chart:
- "chart this", "make a graph", "visualize it", "plot this data"
- "I wanna see it visually", "can you draw this", "picture form please"
- "put it in a diagram", "graphical representation", "show me the chart"

And ALL of these mean the user just wants data/numbers (NO chart):
- "what's the total", "give me the number", "how many are there"
- "list them", "show me the top 5", "tell me the values"
- "calculate this", "what is X", "find the average"

## Your Task:
Analyze the user's query against the available data schema AND conversation context, then return a JSON object with your analysis.

## CRITICAL: FOLLOW-UP QUESTION HANDLING

**You MUST detect follow-up questions and handle them intelligently:**

### Follow-up Patterns to Detect:

1. **Chart Type Changes** (follow_up_type: "chart_type_change")
   - "as a pie chart", "show as line", "make it a bar chart"
   - "pie chart please", "in a scatter plot"
   - Set: is_follow_up=true, inherit_from_previous=true, keep same columns/aggregation

2. **Limit Changes** (follow_up_type: "limit_change")
   - Standalone numbers: "10", "5", "20" (when previous had a limit)
   - "top 10 instead", "show 15", "first 20"
   - "more" = previous limit + 5, "less" = previous limit - 5
   - Set: is_follow_up=true, inherit_from_previous=true

3. **Column Changes** (follow_up_type: "column_change")
   - "by region instead", "now by category", "group by state"
   - Set: is_follow_up=true, keep aggregation and limit, change column

4. **Filter/Refinement** (follow_up_type: "filter_change")
   - "only for 2021", "just the west region", "exclude returns"
   - Set: is_follow_up=true, inherit_from_previous=true

### When is_follow_up is TRUE:
- Set inherit_from_previous=true to keep previous columns/aggregation
- Only change what the user explicitly asked to change
- If user says "10" and previous was "top 5 by sales", result should be "top 10 by sales"

## Decision Rules:

### 1. is_meaningful_query (CRITICAL)
Return FALSE for:
- Random characters: "pp", "fdsf", "asdf", "test", "123", etc.
- Keyboard smashing: "asdfjkl", "qwerty", etc.
- Empty or near-empty: "", " ", "."
- Gibberish: "testtttt", "hellooo", random words

Return TRUE for:
- Clear data questions: "show sales", "top 5 customers", "profit by region"
- **Follow-ups**: "as pie chart", "10", "by category", "show more"
- Questions about the data: "how many rows", "what columns exist"

**IMPORTANT: A standalone number like "5" or "10" IS meaningful if previous context had a limit query!**

### 2. can_be_answered
Return FALSE if:
- Required columns don't exist in schema
- Question is about data not in the dataset
- Question is unrelated to data (e.g., "weather today", "who is president")

### 3. requires_visualization (CRITICAL RULES!)

**AUTOMATIC TRUE - If ANY of these words appear in the query, ALWAYS return TRUE:**
- "chart" (bar chart, pie chart, chart of, chart the, any chart)
- "graph" (graph of, graph the, make a graph)
- "plot" (plot of, scatter plot, line plot)
- "visualize" (visualize, visualization)
- "graphical" (graphical representation)
- "diagram" (diagram of)
- "draw" (draw a chart, draw the)
- "pie" (pie chart)
- "bar" (bar chart)
- "line chart" or "line graph"
- "scatter" (scatter plot)

**Examples that MUST return TRUE:**
- "Chart the distribution of discounts" → TRUE (contains "chart")
- "Create a bar chart of sales" → TRUE (contains "chart")
- "Graphical representation of categories" → TRUE (contains "graphical")
- "Display a graph of profit" → TRUE (contains "graph")
- "Plot sales trend" → TRUE (contains "plot")
- "Pie chart of regions" → TRUE (contains "pie chart")
- "Visualize profit by segment" → TRUE (contains "visualize")

**Return FALSE ONLY when:**
- User asks a question (what, how many, which, who)
- User wants calculations (total, average, sum, count)
- User wants lists or rankings described in TEXT
- User says "show me" WITHOUT chart/graph/visual words
- User wants to KNOW information, not SEE a picture

**Examples that return FALSE:**
- "What is total sales?" → FALSE (question, wants number)
- "Show me top 5 products" → FALSE (wants text list)
- "How did profit change?" → FALSE (question, wants explanation)
- "List the categories" → FALSE (wants text list)

**CRITICAL RULE: The word "chart", "graph", "plot", "visualize", or "graphical" appearing ANYWHERE in the query = TRUE**

### 4. chart_type (only if requires_visualization is true)
- "bar": comparisons, top N, rankings, categories
- "line": trends over time, changes over period
- "pie": distribution, proportions, percentages
- "scatter": correlations, relationships between 2 numeric columns
- "area": cumulative trends

### 5. limit_number
Extract the number from phrases like:
- "top 5" -> 5
- "bottom 10" -> 10
- "first 3" -> 3
- "last 20" -> 20
- "show me 15" -> 15
- **FOLLOW-UP: Standalone "10" after "top 5 query" -> 10**
If no limit mentioned, return null (let system use default)

### 6. group_column & value_column
- Match EXACTLY to column names from the schema (case-sensitive!)
- If user says "by category", find the column that matches (e.g., "Category")
- If user says "sales", find "Sales" column
- **FOLLOW-UP: If inherit_from_previous=true and columns not specified, return null (system will use previous)**
- Return null if cannot determine or column doesn't exist

### 7. aggregation
- "total", "sum" -> "sum"
- "average", "mean" -> "mean"
- "count", "how many" -> "count"
- "minimum", "lowest" -> "min"
- "maximum", "highest" -> "max"

### 8. error_message & suggested_response
- For invalid queries: provide helpful guidance
- For missing columns: explain what's missing and suggest alternatives

## Output Format:
Return ONLY a valid JSON object, no other text:
{
  "is_meaningful_query": boolean,
  "can_be_answered": boolean,
  "requires_visualization": boolean,
  "chart_type": "bar" | "line" | "pie" | "scatter" | "area" | null,
  "limit_number": number | null,
  "group_column": "exact_column_name" | null,
  "value_column": "exact_column_name" | null,
  "aggregation": "sum" | "mean" | "count" | "min" | "max" | null,
  "sort_order": "desc" | "asc" | null,
  "error_message": "string" | null,
  "suggested_response": "string" | null,
  "is_follow_up": boolean,
  "follow_up_type": "chart_type_change" | "limit_change" | "column_change" | "filter_change" | null,
  "inherit_from_previous": boolean
}
"""


class QueryAnalyzer:
    """
    Intelligent Query Analyzer using Gemini 2.5.

    Makes ALL decisions with AI instead of keywords:
    - Validates if query is meaningful
    - Determines visualization needs
    - Extracts parameters (limit, columns, aggregation)
    """

    def __init__(self):
        """Initialize with Gemini API."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = "gemini-2.5-flash"

    async def analyze(
        self,
        question: str,
        schema: dict,
        context: str = "",
    ) -> QueryAnalysis:
        """
        Analyze a user query and return structured decisions.

        Args:
            question: User's query
            schema: Data schema with columns and sample data
            context: Previous conversation context

        Returns:
            QueryAnalysis with all decisions
        """
        # Build the analysis prompt
        columns_info = self._format_schema(schema)

        context_section = ""
        if context and context != "No previous conversation context.":
            context_section = f"""
## Conversation Context:
{context}

Note: Consider if this is a follow-up question. For example:
- If previous query was "show top 5 customers" and current is "10", user might want top 10
- If previous query showed a bar chart and current is "as pie", user wants same data as pie
"""

        prompt = f"""{ANALYZER_SYSTEM_PROMPT}

## Available Data Schema:
{columns_info}
{context_section}

## User Query:
"{question}"

## Your Analysis (JSON only):"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            result_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            json_str = self._extract_json(result_text)

            # Parse JSON
            analysis_dict = json.loads(json_str)

            # Create QueryAnalysis object
            return QueryAnalysis(**analysis_dict)

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Raw response: {result_text[:500]}")
            return self._create_fallback_analysis(question, schema)

        except Exception as e:
            print(f"❌ Query analyzer error: {e}")
            return self._create_fallback_analysis(question, schema)

    def _format_schema(self, schema: dict) -> str:
        """Format schema for the prompt."""
        if not schema:
            return "No schema available"

        lines = ["Available Columns:"]

        columns = schema.get("columns", [])
        sample_data = schema.get("sample_data", {})

        for col in columns:
            sample = sample_data.get(col, "N/A")
            lines.append(f"- {col} (example: {sample})")

        row_count = schema.get("row_count", "unknown")
        lines.append(f"\nTotal rows: {row_count}")

        return "\n".join(lines)

    def _extract_json(self, text: str) -> str:
        """Extract JSON from response text, handling markdown code blocks."""
        # Try to find JSON in code blocks
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Try to find raw JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)

        return text

    def _create_fallback_analysis(
        self,
        question: str,
        schema: dict,
    ) -> QueryAnalysis:
        """Create a safe fallback analysis when AI fails."""
        question_clean = question.strip().lower()

        # Check for common follow-up patterns (even if just a number)
        follow_up_patterns = {
            "pie": ("chart_type_change", "pie"),
            "bar": ("chart_type_change", "bar"),
            "line": ("chart_type_change", "line"),
            "scatter": ("chart_type_change", "scatter"),
            "more": ("limit_change", None),
            "less": ("limit_change", None),
        }

        # Check for chart type follow-ups
        for pattern, (follow_type, chart_type) in follow_up_patterns.items():
            if pattern in question_clean:
                return QueryAnalysis(
                    is_meaningful_query=True,
                    can_be_answered=True,
                    requires_visualization=True,
                    chart_type=chart_type,
                    is_follow_up=True,
                    follow_up_type=follow_type,
                    inherit_from_previous=True,
                )

        # Check for standalone numbers (limit changes)
        if question_clean.isdigit():
            return QueryAnalysis(
                is_meaningful_query=True,
                can_be_answered=True,
                requires_visualization=True,
                limit_number=int(question_clean),
                is_follow_up=True,
                follow_up_type="limit_change",
                inherit_from_previous=True,
            )

        # Check for obviously invalid queries
        is_meaningful = (
            len(question_clean) > 3 and
            any(c.isalpha() for c in question_clean) and
            not question_clean.replace(" ", "").isdigit() and
            len(question_clean.split()) > 1 or question_clean in ["help", "columns", "schema"]
        )

        if not is_meaningful:
            return QueryAnalysis(
                is_meaningful_query=False,
                can_be_answered=False,
                requires_visualization=False,
                suggested_response="I couldn't understand your request. Please ask a clear question about your data, like 'What are the top 5 products by sales?' or 'Show total revenue by region'."
            )

        # Default safe analysis
        return QueryAnalysis(
            is_meaningful_query=True,
            can_be_answered=True,
            requires_visualization=False,  # Safe default: no chart
            suggested_response=None
        )


# Global analyzer instance
_analyzer: QueryAnalyzer | None = None


def get_query_analyzer() -> QueryAnalyzer:
    """Get or create analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryAnalyzer()
    return _analyzer

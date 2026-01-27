"""
Query Classifier Agent

Uses Google Gemini 2.5 Flash to intelligently classify user queries.
Determines if a query is a data analysis question or casual conversation.
"""

from google import genai
from typing import Literal

from app.config import get_settings


# Classification types
QueryType = Literal["DATA_QUESTION", "GREETING", "CHITCHAT", "UNCLEAR"]


# System prompt for the classifier
CLASSIFIER_SYSTEM_PROMPT = """You are a Query Classifier for a Data Analysis chatbot. Your job is to determine if a user message is asking about data/analysis OR if it's just casual conversation.

## Classification Categories:

1. **DATA_QUESTION** - User wants to analyze, query, or understand their uploaded data
   Examples:
   - "What is the total sales?"
   - "Show me top 5 products"
   - "Calculate average revenue by region"
   - "Create a chart of monthly trends"
   - "How many rows have missing values?"
   - "What columns are in the data?"
   - "Compare Q1 vs Q2 performance"

   IMPORTANT - Follow-up questions are also DATA_QUESTION:
   - "What about by region?" (follow-up to previous analysis)
   - "Show me that as a chart"
   - "Now filter by category"
   - "And the average?"
   - "Break it down by month"
   - "Sort by highest"
   - "Top 10 instead"

2. **GREETING** - Simple greetings or salutations (ONLY when NO previous data conversation)
   Examples:
   - "Hi", "Hello", "Hey"
   - "Good morning", "Good evening"
   - "Hi there", "Howdy"

3. **CHITCHAT** - Casual conversation, personal questions, or off-topic messages (ONLY when clearly NOT about data)
   Examples:
   - "How are you?"
   - "What's your name?"
   - "Tell me a joke"
   - "What can you do?"
   - "Thanks", "Thank you"
   - "Nice weather today"
   - "Who created you?"

4. **UNCLEAR** - Message is ambiguous and could go either way
   Examples:
   - Single word that could be a column name or greeting
   - Incomplete sentences

## CRITICAL RULES:
- If conversation history shows "[DATA ANALYSIS SESSION]" or "[executed data analysis]" or "[created chart]", then ANY short follow-up message is almost certainly DATA_QUESTION
- ANY question after a data analysis response = DATA_QUESTION (e.g., "What about X?", "And by region?", "Show me that", "Top 5", "Break it down")
- Short questions/commands after data results = DATA_QUESTION (e.g., "as a chart", "by month", "sort it", "filter by X", "top 10 instead")
- When in doubt, ALWAYS classify as DATA_QUESTION
- Only classify as GREETING if it's a clear greeting like "Hi", "Hello" AND there is NO data analysis history
- Only classify as CHITCHAT if it's clearly personal/off-topic AND there is NO data analysis history

## Instructions:
- Respond with ONLY ONE of these exact words: DATA_QUESTION, GREETING, CHITCHAT, or UNCLEAR
- No explanation, no extra text, just the classification
- When in doubt between DATA_QUESTION and others, ALWAYS lean towards DATA_QUESTION
"""


class QueryClassifier:
    """
    Intelligent Query Classifier using Gemini 2.5 Flash.

    Classifies user queries to route them appropriately:
    - DATA_QUESTION -> Full multi-agent workflow (Planner + Executor)
    - GREETING/CHITCHAT -> Friendly response without data analysis
    """

    def __init__(self):
        """Initialize the classifier with Google Gemini API."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = "gemini-2.5-flash"  # Fast model for quick classification

    async def classify(self, question: str, context: str = "") -> QueryType:
        """
        Classify the user's question with conversation context.

        Args:
            question: User's input message
            context: Previous conversation context for follow-up detection

        Returns:
            QueryType: DATA_QUESTION, GREETING, CHITCHAT, or UNCLEAR
        """
        # Build the classification prompt with context
        context_section = ""
        if context and context != "No previous conversation context.":
            context_section = f"""
## Recent Conversation History:
{context}

NOTE: If there was recent data analysis discussion, short follow-up messages are likely DATA_QUESTION.
"""

        prompt = f"""{CLASSIFIER_SYSTEM_PROMPT}
{context_section}
User message: "{question}"

Classification:"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            result = response.text.strip().upper()

            # Validate and return the classification
            if "DATA_QUESTION" in result:
                return "DATA_QUESTION"
            elif "GREETING" in result:
                return "GREETING"
            elif "CHITCHAT" in result:
                return "CHITCHAT"
            elif "UNCLEAR" in result:
                return "UNCLEAR"
            else:
                # Default to DATA_QUESTION if response is unexpected
                print(f"⚠️ Unexpected classifier response: {result}, defaulting to DATA_QUESTION")
                return "DATA_QUESTION"

        except Exception as e:
            print(f"❌ Classifier error: {e}")
            # On error, default to DATA_QUESTION to not break functionality
            return "DATA_QUESTION"

    def get_friendly_response(self, query_type: QueryType, question: str) -> str:
        """
        Generate a friendly response for non-data queries.

        Args:
            query_type: The classification type
            question: Original user message

        Returns:
            Friendly response string
        """
        question_lower = question.lower().strip()

        if query_type == "GREETING":
            # Handle various greetings
            if any(word in question_lower for word in ["good morning", "morning"]):
                return "Good morning! I'm ready to help you analyze your data. What would you like to know?"
            elif any(word in question_lower for word in ["good evening", "evening"]):
                return "Good evening! I'm here to help with your data analysis. What questions do you have?"
            elif any(word in question_lower for word in ["good afternoon", "afternoon"]):
                return "Good afternoon! Ready to dive into your data. What would you like to explore?"
            else:
                return "Hello! I'm your Data Analysis Assistant. I can help you explore and understand your uploaded data. Try asking questions like 'What are the top 5 products by sales?' or 'Show me a chart of monthly trends'."

        elif query_type == "CHITCHAT":
            # Handle various chitchat
            if "how are you" in question_lower:
                return "I'm doing great, thank you for asking! I'm ready to help you analyze your data. What would you like to know about your dataset?"
            elif "your name" in question_lower or "who are you" in question_lower:
                return "I'm your Data Analysis Assistant! I use AI to help you explore and understand your uploaded data. Ask me questions about your dataset and I'll provide insights, calculations, and visualizations."
            elif "what can you do" in question_lower or "help" in question_lower:
                return "I can help you analyze your uploaded data! Here's what I can do:\n\n- Answer questions about your data (e.g., 'What is the total sales?')\n- Calculate statistics (e.g., 'Show average revenue by region')\n- Find patterns (e.g., 'What are the top 5 products?')\n- Create visualizations (e.g., 'Create a bar chart of sales by category')\n\nJust ask me anything about your data!"
            elif any(word in question_lower for word in ["thank", "thanks"]):
                return "You're welcome! Let me know if you have any more questions about your data."
            elif "joke" in question_lower:
                return "I'm better at analyzing data than telling jokes! But here's a data one: Why did the data analyst break up with the pie chart? Because they found someone with better distribution! Now, what would you like to know about your data?"
            else:
                return "I'm a Data Analysis Assistant focused on helping you understand your uploaded data. Try asking me questions like 'What is the total revenue?' or 'Show me top 10 customers by sales'. What would you like to explore?"

        else:
            # UNCLEAR - prompt for clarification
            return "I'm not sure if you're asking about your data or just chatting. I'm a Data Analysis Assistant - I can help you explore your uploaded dataset. Could you please ask a specific question about your data?"


# Global classifier instance
_classifier: QueryClassifier | None = None


def get_classifier() -> QueryClassifier:
    """Get or create classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier

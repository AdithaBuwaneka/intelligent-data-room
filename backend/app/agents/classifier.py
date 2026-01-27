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
CLASSIFIER_SYSTEM_PROMPT = """You are an intelligent Query Classifier for a Data Analysis chatbot. Your job is to understand the user's TRUE INTENT and classify their message appropriately.

## Classification Categories:

1. **DATA_QUESTION** - User wants to analyze, query, or explore their data
   Examples:
   - "show me total sales", "what's the average?", "top 5 products"
   - "create a chart", "visualize trends", "plot by region"
   - "how many rows?", "what columns exist?", "filter by X"
   - Follow-ups: "by category?", "sort it", "top 10 instead", "as a bar chart"
   - Short commands after analysis: "more", "others", "different view"

2. **GREETING** - Pure social greeting with NO data request
   Examples:
   - ANY variation of hello: "hi", "hello", "hey", "hiii", "heyy", "yo", "sup"
   - Time greetings: "good morning", "gm", "good evening", "good night"
   - Informal: "howdy", "aloha", "hiya", "greetings", "salutations"
   - With typos: "helo", "hiii", "heya", "heyyyy"
   
   CRITICAL: A greeting is ALWAYS a greeting, even during a data session!
   - "hi" after 10 data queries = still GREETING
   - User can greet you anytime without wanting data analysis

3. **CHITCHAT** - Personal questions, capabilities, or social conversation
   Examples:
   - Personal: "how are you", "how r u", "what's up", "how you doing"
   - Identity: "who are you", "what's your name", "who made you", "what are you"
   - Capabilities: "what can you do", "help", "features", "how does this work"
   - Social: "thanks", "thank you", "cool", "nice", "awesome", "great"
   - Random: "tell a joke", "weather", "fun fact"
   
   CRITICAL: Chitchat is chitchat regardless of conversation history!
   - "who are you" after data analysis = still CHITCHAT
   - User can ask about YOU without asking about their DATA

4. **UNCLEAR** - Genuinely ambiguous (use sparingly)
   Only when the message could reasonably be interpreted as both:
   - Single word that could be column name: "sales" (after discussing products)
   - Vague reference needing context: "that one", "more", "continue"

## CRITICAL RULES FOR INTELLIGENCE:

**Rule 1: Intent Over Context**
- If message is CLEARLY greeting/chitchat, classify it as such
- Don't assume everything in a data session is about data
- Users can chat casually at any point

**Rule 2: Semantic Understanding**
- Recognize intent, not keywords
- Handle ANY variation: "hiiiii", "helo", "heyyy", "morning!", "yo wassup"
- Understand typos, slang, abbreviations
- Consider tone and social cues

**Rule 3: Context as Helper, Not Decider**
- Context helps with ambiguous follow-ups ("by region?", "top 10")
- Context should NOT override clear greetings/chitchat
- "hi" = GREETING (always)
- "who are you" = CHITCHAT (always)
- "show more" after analysis = DATA_QUESTION (context helps)

**Rule 4: When in Doubt**
- Clear greeting/chitchat? → Classify as such
- Could be follow-up but unclear? → UNCLEAR or DATA_QUESTION
- Ambiguous single word? → Consider context

## Output:
Respond with EXACTLY ONE word: DATA_QUESTION, GREETING, CHITCHAT, or UNCLEAR
No explanation. Just the classification.
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
        Classify the user's question intelligently using AI.

        Args:
            question: User's input message
            context: Previous conversation context for intent analysis

        Returns:
            QueryType: DATA_QUESTION, GREETING, CHITCHAT, or UNCLEAR
        """
        # Build the classification prompt with context awareness
        context_section = ""
        if context and context != "No previous conversation context.":
            context_section = f"""
## Conversation Context:
{context}

**Analysis**: This conversation has history. Consider whether the user is continuing 
a data analysis session or starting fresh casual conversation.
"""
        else:
            context_section = """
## Conversation Context:
No previous conversation.

**Analysis**: This is the start of the conversation. Pure greetings and chitchat 
are more likely unless the message explicitly asks about data.
"""

        prompt = f"""{CLASSIFIER_SYSTEM_PROMPT}
{context_section}

User Message: "{question}"

Classification:"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            result = response.text.strip().upper()

            # Parse the classification intelligently
            if "DATA_QUESTION" in result or "DATA" in result:
                return "DATA_QUESTION"
            elif "GREETING" in result:
                return "GREETING"
            elif "CHITCHAT" in result or "CHIT" in result:
                return "CHITCHAT"
            elif "UNCLEAR" in result:
                return "UNCLEAR"
            else:
                # If AI response is unexpected, analyze the question ourselves as fallback
                print(f"⚠️ Unexpected classifier response: {result}")
                question_lower = question.lower().strip()
                
                # Very basic fallback - single word likely greeting if no context
                if len(question_lower.split()) == 1 and not context:
                    if len(question_lower) < 15:  # Short single words
                        return "GREETING"
                
                # Default to DATA_QUESTION for safety
                return "DATA_QUESTION"

        except Exception as e:
            print(f"❌ Classifier error: {e}")
            # On error, analyze the question with basic heuristics
            question_lower = question.lower().strip()
            
            # Very short messages without context are likely greetings
            if not context and len(question_lower) < 20 and "?" not in question_lower:
                if any(word in question_lower for word in ["hi", "hello", "hey", "morning", "evening"]):
                    return "GREETING"
            
            # Default to DATA_QUESTION to maintain functionality
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

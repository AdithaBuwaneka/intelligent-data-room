"""
LangGraph Workflow

Defines the multi-agent workflow using LangGraph's StateGraph.
Orchestrates communication between Planner and Executor agents.

Workflow:
    User Question → Planner Agent → Executor Agent → Response
"""

from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, END
import pandas as pd

from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent


class AgentState(TypedDict):
    """
    State schema for the multi-agent workflow.

    Passed between nodes in the graph.
    """
    # Input
    question: str
    data_schema: dict
    context: str
    dataframe: Any  # pd.DataFrame

    # Intermediate
    plan: str

    # Output
    answer: str
    chart_config: Optional[dict]
    error: Optional[str]


class AgentWorkflow:
    """
    Multi-Agent Workflow using LangGraph.

    Nodes:
    - planner: Creates execution plan from question
    - executor: Executes plan and generates results

    Flow:
    START → planner → executor → END
    """

    def __init__(self):
        """Initialize the workflow with agents and graph."""
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph.

        Returns:
            Compiled StateGraph
        """
        # Create the graph with state schema
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)

        # Define edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", END)

        # Compile the graph
        return workflow.compile()

    async def _planner_node(self, state: AgentState) -> dict:
        """
        Planner node: Creates execution plan.

        Args:
            state: Current workflow state

        Returns:
            Updated state with plan
        """
        print("🧠 Planner Agent: Analyzing question and creating plan...")

        try:
            plan = await self.planner.create_plan(
                question=state["question"],
                data_schema=state["data_schema"],
                context=state.get("context"),
            )

            print(f"📋 Plan created:\n{plan[:200]}...")

            return {"plan": plan}

        except Exception as e:
            print(f"❌ Planner error: {e}")
            return {
                "plan": "Direct execution required",
                "error": str(e),
            }

    async def _executor_node(self, state: AgentState) -> dict:
        """
        Executor node: Executes plan and generates results.

        Args:
            state: Current workflow state with plan

        Returns:
            Updated state with answer and chart_config
        """
        print("⚡ Executor Agent: Executing plan...")

        try:
            df = state["dataframe"]

            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                return {
                    "answer": "No data available to analyze.",
                    "chart_config": None,
                }

            result = await self.executor.execute_plan(
                plan=state["plan"],
                df=df,
                question=state["question"],
            )

            print(f"✅ Execution complete. Answer length: {len(result['answer'])} chars")

            return {
                "answer": result["answer"],
                "chart_config": result["chart_config"],
            }

        except Exception as e:
            print(f"❌ Executor error: {e}")
            return {
                "answer": f"I encountered an error while analyzing: {str(e)}",
                "chart_config": None,
                "error": str(e),
            }

    async def run(
        self,
        question: str,
        dataframe: pd.DataFrame,
        context: Optional[str] = None,
    ) -> dict:
        """
        Run the multi-agent workflow.

        Args:
            question: User's natural language question
            dataframe: Pandas DataFrame with the data
            context: Previous conversation context

        Returns:
            Dictionary with answer, plan, and chart_config
        """
        print(f"\n{'='*50}")
        print(f"🚀 Starting Multi-Agent Workflow")
        print(f"📝 Question: {question}")
        print(f"{'='*50}\n")

        # Prepare data schema
        data_schema = self._extract_schema(dataframe)

        # Initial state
        initial_state: AgentState = {
            "question": question,
            "data_schema": data_schema,
            "context": context or "No previous conversation context.",
            "dataframe": dataframe,
            "plan": "",
            "answer": "",
            "chart_config": None,
            "error": None,
        }

        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)

            print(f"\n{'='*50}")
            print(f"✅ Workflow Complete")
            print(f"{'='*50}\n")

            return {
                "answer": final_state.get("answer", "No answer generated"),
                "plan": final_state.get("plan", ""),
                "chart_config": final_state.get("chart_config"),
                "error": final_state.get("error"),
            }

        except Exception as e:
            print(f"❌ Workflow error: {e}")
            return {
                "answer": f"An error occurred: {str(e)}",
                "plan": "",
                "chart_config": None,
                "error": str(e),
            }

    def _extract_schema(self, df: pd.DataFrame) -> dict:
        """
        Extract schema information from DataFrame.

        Args:
            df: Pandas DataFrame

        Returns:
            Dictionary with columns, types, and sample data
        """
        if df is None or df.empty:
            return {"columns": [], "sample_data": {}, "row_count": 0}

        columns = df.columns.tolist()

        # Get sample data (first non-null value for each column)
        sample_data = {}
        for col in columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                sample_data[col] = str(non_null.iloc[0])[:50]
            else:
                sample_data[col] = "N/A"

        return {
            "columns": columns,
            "sample_data": sample_data,
            "row_count": len(df),
        }

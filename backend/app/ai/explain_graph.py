from typing import Callable, Awaitable
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict,NotRequired


class ExplainState(TypedDict):
    name: str
    content: str
    explanation: NotRequired[str]


def build_explain_graph(
    explain_code: Callable[[str, str], Awaitable[str]]
):
    async def explain_node(state: ExplainState):
        explanation = await explain_code(
            state["name"],
            state["content"]
        )
        return {"explanation": explanation}

    generate_explanation = StateGraph(ExplainState)

    generate_explanation.add_node("explain", explain_node)
    generate_explanation.add_edge(START, "explain")
    generate_explanation.add_edge("explain", END)

    return generate_explanation.compile()
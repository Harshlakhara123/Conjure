from app.ai.ollama_explainer import build_ollama_explainer
from app.ai.explain_graph import build_explain_graph

from functools import lru_cache

@lru_cache(maxsize=1)
def get_explain_graph():
    explain_code_function = build_ollama_explainer()
    return build_explain_graph(explain_code_function)
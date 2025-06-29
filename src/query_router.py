# src/query_router.py

from typing import List
from llama_index.core.schema import BaseNode
from llama_index.core import VectorStoreIndex, SummaryIndex
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector

def create_query_router(vector_index: VectorStoreIndex, nodes: List[BaseNode], verbose: bool=True) -> RouterQueryEngine:
    """
    Creates a RouterQueryEngine that intelligently routes queries to the most
    appropriate sub-engine (either vector search or summarization).

    Args:
        vector_index (VectorStoreIndex): The index built for detailed, specific semantic search.
        nodes (List[BaseNode]): The list of all nodes, used to build the summary index.
        verbose (bool): Whether to print the routing decision process. Defaults to True.

    Returns:
        RouterQueryEngine: The configured router query engine.
    """
    # initialize two query engines
    # for specific questions, use vector search
    vector_query_engine = vector_index.as_query_engine()
    # for summary questions, use summarization
    summary_index = SummaryIndex(nodes)
    summary_query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize",
        use_async=True,
    )
    
    # define tools for router
    vector_tool = QueryEngineTool(
        query_engine=vector_query_engine,
        metadata=ToolMetadata(
            name="vector_search_engine",
            description=(
                "Useful for answering specific, detailed questions about the implementation, "
                "code, functions, classes, or the content of specific files."
            )
        )
    )
    summary_tool = QueryEngineTool(
        query_engine=summary_query_engine,
        metadata=ToolMetadata(
            name="summary_engine",
            description=(
                "Useful for answering high-level, general, or summary questions about the "
                "entire repository, such as its overall purpose, structure, main components, "
                "or providing a list of files."
            )
        )
    )

    # create the RouterQueryEngine
    query_engine = RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[
            vector_tool, 
            summary_tool,
        ],
        verbose=verbose,
    )

    return query_engine


# src/tools.py
import os
from duckduckgo_search import DDGS

# FOR FILE TREE GENERATION --------------------------------------------------------------------

def get_file_tree(repo_path: str, max_depth: int = 3) -> str:
    """
    Generates a string representation of the file tree structure for a given repository.

    Args:
        repo_path (str): The local path to the repository.
        max_depth (int): The maximum depth to traverse the directory tree.

    Returns:
        str: A string representing the file tree.
    """
    tree_str = f"File tree for '{os.path.basename(repo_path)}' (up to depth {max_depth}):\n\n"
    
    # Excluded directories for a cleaner view
    exclude_dirs = {'.git', '.vscode', 'node_modules', '__pycache__', 'target', 'build', 'dist', '.venv', 'venv'}

    for root, dirs, files in os.walk(repo_path):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        level = root.replace(repo_path, '').count(os.sep)
        if level >= max_depth:
            # Stop descending further if max depth is reached
            dirs[:] = [] 
            continue

        indent = ' ' * 4 * level
        tree_str += f"{indent}├── {os.path.basename(root)}/\n"
        
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            tree_str += f"{sub_indent}├── {f}\n"
            
    return tree_str

# FOR SEARCHING THE WEB --------------------------------------------------------------------

def internet_search(query: str, max_results: int = 5) -> str:
    """
    Performs an internet search using DuckDuckGo and returns the results.

    Args:
        query (str): The search query.
        max_results (int): The maximum number of results to return.

    Returns:
        str: A formatted string of the search results, including title, snippet, and URL.
    """
    results_str = ""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return f"No search results found for '{query}'."
    for i, result in enumerate(results, 1):
        results_str += f"Result {i}:\n"
        results_str += f"  - Title: {result.get('title', 'N/A')}\n"
        results_str += f"  - Snippet: {result.get('body', 'N/A')}\n"
        results_str += f"  - URL: {result.get('href', 'N/A')}\n\n"
    return results_str.strip()
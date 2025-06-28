# src/doc_generator.py

from collections import defaultdict
import os
from typing import List
from pydantic import BaseModel
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.llms import LLM
from .language_utils import EXTENSION_TO_LANGUAGE_MAP
from llama_index.core import PromptTemplate

class KeyFileInfo(BaseModel):
    """Data model for key files identified for the quick start guide"""
    file_path: str
    reason: str # why this file is important

class KeyFiles(BaseModel):
    """Data model for a list of key files"""
    files: List[KeyFileInfo]

def generate_quick_start(repo_path: str, query_engine: BaseQueryEngine, llm: LLM) -> str:
    """
    Generates a Quick Start Guide for a given repository.

    This function follows a multi-step process:
    1. Identify key files crucial for a new developer.
    2. Summarize the content and purpose of each key file.
    3. Synthesize these summaries into a coherent Quick Start Guide.

    Args:
        repo_path (str): The local path to the repository.
        query_engine (BaseQueryEngine): The query engine to summarize file content.
        llm (LLM): The language model to perform selection and synthesis tasks.

    Returns:
        str: The generated Quick Start Guide in Markdown format.
    """
    # identify key files
    categorized_files = {
        "Documentation": [],
        "Configuration": [],
        "Source Code": defaultdict(list),
        "Other": []
    }
    doc_files = ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", ".md", ".rst"]
    config_files = ["requirements.txt", "package.json", "Dockerfile", ".env", ".yaml", ".yml", ".toml", ".ini", ".cfg"]
    for root, _, files in os.walk(repo_path):
        if any(d in root for d in [".git", "__pycache__", "node_modules", "target", "build", "dist"]):
            continue
        for file in files:
            file_path = os.path.join(root, file)
            _, extension = os.path.splitext(file)
            
            if file in doc_files or any(file.endswith(ext) for ext in doc_files if ext.startswith('.')):
                categorized_files["Documentation"].append(file_path)
            elif file in config_files or any(file.endswith(ext) for ext in config_files if ext.startswith('.')):
                categorized_files["Configuration"].append(file_path)
            elif extension in EXTENSION_TO_LANGUAGE_MAP:
                language = EXTENSION_TO_LANGUAGE_MAP[extension]
                categorized_files["Source Code"][language].append(file_path)
            else:
                try:
                    if os.path.getsize(file_path) < 1_000_000: # Ignore files larger than 1MB
                        categorized_files["Other"].append(file_path)
                except OSError:
                    continue

    # build a structured prompt with the categorized file list
    structured_file_list = "Here is a categorized list of files in the project:\n\n"
    if categorized_files["Documentation"]:
        structured_file_list += "### Documentation Files\n- " + "\n- ".join(categorized_files["Documentation"]) + "\n"
    if categorized_files["Configuration"]:
        structured_file_list += "\n### Configuration & Dependency Files\n- " + "\n- ".join(categorized_files["Configuration"]) + "\n"
    if categorized_files["Source Code"]:
        structured_file_list += "\n### Source Code Files\n"
        for lang, files in categorized_files["Source Code"].items():
            structured_file_list += f"- **{lang.capitalize()}**:\n  - " + "\n  - ".join(files) + "\n"
    if categorized_files["Other"]:
         structured_file_list += "\n### Other Files\n- " + "\n- ".join(categorized_files["Other"]) + "\n"


    # use llm to select the most important files
    selection_prompt_template = PromptTemplate(
        "Given a categorized list of file paths from a software project,\n"
        "please select the top 5-7 most important files for a new developer\n"
        "to understand the project quickly.\n\n"
        "Your selection should be based on this priority:\n"
        "1. README files: Almost always the most important file.\n"
        "2. Installation/dependency files: Crucial for setup (e.g., package.json, requirements.txt).\n"
        "3. Core application entry points: The starting point of the code (e.g., main.py, app.js).\n"
        "4. Key configuration files: Defines how the project runs (e.g., Dockerfile).\n"
        "5. A central source file: A file that contains the core business logic.\n\n"
        "For each file you select, provide a brief reason why it's important.\n\n"
        "CATEGORIZED FILE LIST:\n"
        "---------------------\n"
        "{file_list}\n"
        "---------------------\n"
    )

    try:
        key_files_response = llm.structured_predict(
            KeyFiles,
            selection_prompt_template,
            file_list=structured_file_list
        )
        key_files = key_files_response.files
    except Exception as e:
        return f"Error: Could not identify key files using the LLM. Details: {e}"

    # summarize the content of key files
    summaries = []
    for kf in key_files:
        try:
            response = query_engine.query(f"Summarize the purpose and content of the file: `{kf.file_path}`")
            summaries.append(f"### File: `{kf.file_path}`\n**Importance:** {kf.reason}\n**Summary:**\n{response}\n")
        except Exception as e:
            summaries.append(f"### File: `{kf.file_path}`\n**Error:** Could not summarize this file. Details: {e}\n")
    summaries_str = "\n---\n".join(summaries)

    # sythesize the final guide
    final_guide_template = PromptTemplate(
        "You are an expert technical writer creating a \"Quick Start Guide\" for a new developer.\n"
        "Based on the following summaries of key project files, write a comprehensive, clear,\n"
        "and easy-to-follow guide.\n\n"
        "The guide MUST include the following sections:\n"
        "- ## 🚀 Project Overview: A brief, high-level introduction to the project's purpose.\n"
        "- ## 🔧 Installation: How to set up the project and install dependencies.\n"
        "- ## ▶️ How to Run: The exact commands to run the project.\n"
        "- ## 🏛️ Core Components Explained: Briefly explain the role of each key file.\n\n"
        "Use the provided summaries to fill in these sections accurately.\n"
        "Format the entire output in Markdown.\n\n"
        "**FILE SUMMARIES:**\n"
        "---------------------\n"
        "{summaries}\n"
        "---------------------\n"
    )

    try:
        final_response = llm.predict(
            final_guide_template,
            summaries=summaries_str
        )
        return final_response
    except Exception as e:
        # This will now correctly handle errors from the final predict call
        return f"Error: Could not synthesize the final guide. Details: {e}"

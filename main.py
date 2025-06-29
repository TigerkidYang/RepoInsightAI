import streamlit as st
import os
import re

# --- 1. Imports: Grouped for clarity ---
# Backend modules
from src.git_utils import clone_or_pull_repo
from src.index_builder import get_or_create_index
from src.query_router import create_query_router
from src.doc_generator import generate_quick_start, generate_api_docs
from src.tools import get_file_tree, internet_search

# LlamaIndex modules
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core import Settings
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.core.memory import ChatMemoryBuffer


# --- 2. Helper Functions ---
def clean_markdown_output(raw_text: str) -> str:
    """
    Removes the outer markdown code block (e.g., ```markdown ... ```) 
    from the LLM's output to ensure proper rendering in Streamlit.
    """
    # Regex to find a markdown block with an optional language specifier
    match = re.match(r"^```(\w*\n)?(.*?)```$", raw_text, re.DOTALL)
    if match:
        # Return the captured content inside the code block
        return match.group(2).strip()
    return raw_text.strip()


# --- 3. Page Configuration ---
st.set_page_config(
    page_title="RepoInsightAI - Your AI GitHub Repo Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 4. Session State Initialization ---
# This is the "memory" of the Streamlit app. It preserves data across reruns.
# We initialize all possible state variables here to avoid errors.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "query_engine" not in st.session_state: # To pass to doc generators
    st.session_state.query_engine = None
if "repo_path" not in st.session_state:
    st.session_state.repo_path = None
if "quick_start_guide" not in st.session_state:
    st.session_state.quick_start_guide = None
if "api_docs" not in st.session_state:
    st.session_state.api_docs = None
if "file_tree" not in st.session_state:
    st.session_state.file_tree = None


# --- 5. Application UI and Logic ---

# Render the title and caption
st.title("🤖 RepoInsightAI")
st.caption("Deeply understand any codebase and chat with your GitHub projects.")

# Setup the sidebar for configuration and actions
with st.sidebar:
    st.header("1. Configure Your Codebase")
    repo_url = st.text_input(
        "Enter GitHub Repository URL",
        placeholder="e.g., https://github.com/jerryjliu/llama_index"
    )

    if st.button("Analyze Repository", type="primary", use_container_width=True):
        if not repo_url or not repo_url.startswith("https://github.com"):
            st.error("Please enter a valid GitHub HTTPS URL!")
        else:
            # This block runs when the user starts an analysis.
            # It performs all heavy lifting and stores results in the session state.
            with st.spinner("Analysis in progress, please wait..."):
                try:
                    # Clear any previous results to start fresh
                    st.session_state.quick_start_guide = None
                    st.session_state.api_docs = None
                    st.session_state.messages = []
                    
                    st.info("Step 1: Cloning repository...")
                    st.session_state.repo_path = clone_or_pull_repo(repo_url)
                    
                    st.info("Step 2: Building knowledge index...")
                    vector_index, nodes = get_or_create_index(st.session_state.repo_path)
                    
                    st.info("Step 3: Creating smart query router...")
                    st.session_state.query_engine = create_query_router(vector_index, nodes, verbose=False)
                    
                    st.info("Step 4: Creating ReAct agent with multiple tools...")
                    # Tool1: RAG Router
                    query_engine_tool = QueryEngineTool(
                        query_engine=st.session_state.query_engine,
                        metadata=ToolMetadata(
                            name="codebase_qa_system",
                            description="The primary tool for answering any questions about the analyzed code repository. Use this for all questions related to code, implementation, project purpose, and file content."
                        )
                    )
                    # Tool2: File Tree Viewer
                    file_tree_tool = FunctionTool.from_defaults(
                        fn=lambda: get_file_tree(st.session_state.repo_path),
                        name="file_tree_viewer",
                        description="Extremely useful for understanding the project's structure. Use this specific tool ONLY when the user asks to 'list files', 'show the directory structure', or 'what is the file tree?'"          
                    )
                    # Tool3: Internet Search
                    search_tool = FunctionTool.from_defaults(
                        fn=internet_search,
                        name="internet_search",
                        description=(
                            "A powerful tool to search the internet for real-time information, "
                            "definitions of external libraries, or general programming concepts "
                            "not found within the local codebase."
                        )
                    )

                    memory = ChatMemoryBuffer.from_defaults(token_limit=4096)

                    st.session_state.chat_engine = OpenAIAgent.from_tools(
                        tools=[query_engine_tool, file_tree_tool, search_tool],
                        llm=Settings.llm,
                        memory=memory,
                        system_prompt="""
                        You are a helpful and expert AI assistant for understanding code repositories.
                        You have two types of tools:
                        1. A codebase Q&A system to answer questions about the code.
                        2. A file tree viewer to show the directory structure.
                        3. A web search tool to find real-time information, definitions of external libraries, or general programming concepts not found within the local codebase.
                        Always use your tools to answer questions.
                        """,
                        verbose=True # Keep verbose=True for debugging agent's thoughts in your console!
                    )
                    
                    # Set up the initial welcome message for the chat
                    repo_name = os.path.basename(st.session_state.repo_path)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"✅ Repository '{repo_name}' is ready! You can now ask questions or generate documents."}
                    )
                    st.success("Analysis complete!")
                    # Force a rerun to update the main page UI immediately
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")

    # This section appears only after a repository has been successfully analyzed
    if st.session_state.chat_engine:
        st.divider()
        st.header("2. Generate Documents")

        if st.button("Generate File Tree", use_container_width=True):
            with st.spinner("🌳 Generating file tree..."):
                tree = get_file_tree(st.session_state.repo_path)
                st.session_state.file_tree = tree
            st.success("File Tree generated!")
        
        if st.button("Generate Quick Start Guide", use_container_width=True):
            with st.spinner("🚀 Generating Quick Start Guide... This may take a moment."):
                guide = generate_quick_start(
                    st.session_state.repo_path,
                    st.session_state.query_engine, # Use the base query engine for summarization
                    Settings.llm
                )
                st.session_state.quick_start_guide = guide
            st.success("Quick Start Guide generated!")

        if st.button("Generate API Docs", use_container_width=True):
            with st.spinner("🛠️ Generating API Docs... This is a deep process and may take several minutes."):
                docs = generate_api_docs(
                    st.session_state.repo_path,
                    Settings.llm
                )
                st.session_state.api_docs = docs
            st.success("API Docs generated!")

    st.divider()
    st.info("Powered by LlamaIndex.")

# --- 6. Main Page Content (Tabs) ---

# Set up a welcome message if chat history is empty
if not st.session_state.messages:
     st.session_state.messages = [{"role": "assistant", "content": "Hello! Please enter a GitHub repository URL on the left and click 'Analyze' to get started."}]

# Create tabs for different functionalities
tab_chat, tab_file_tree, tab_quick_start, tab_api_docs = st.tabs(["💬 Chat with Repo", "🌳 File Tree", "🚀 Quick Start Guide", "🛠️ API Docs"])

# Chat Tab Logic
with tab_chat:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask anything about this codebase..."):
        if not st.session_state.chat_engine:
            st.warning("Please analyze a repository first.", icon="⚠️")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("AI is thinking..."):
                response = st.session_state.chat_engine.chat(prompt)
                ai_response = str(response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun() # Rerun to display the new messages immediately

# File Tree Tab Logic
with tab_file_tree:
    st.header("🌳 Repository File Tree")
    if st.session_state.file_tree:
        # Use st.code to display the tree with a fixed-width font for proper alignment
        st.code(st.session_state.file_tree, language=None)
    else:
        st.info("Click the 'Generate File Tree' button in the sidebar to see the repository structure here.")

# Quick Start Guide Tab Logic
with tab_quick_start:
    st.header("🚀 Quick Start Guide")
    if st.session_state.quick_start_guide:
        cleaned_guide = clean_markdown_output(st.session_state.quick_start_guide)
        st.markdown(cleaned_guide)
        st.download_button(
            label="Download Guide", data=cleaned_guide, file_name="QUICK_START_GUIDE.md", mime="text/markdown"
        )
    else:
        st.info("Click the 'Generate Quick Start Guide' button in the sidebar after analyzing a repository.")

# API Docs Tab Logic
with tab_api_docs:
    st.header("🛠️ API Documentation")
    if st.session_state.api_docs:
        cleaned_docs = clean_markdown_output(st.session_state.api_docs)
        st.markdown(cleaned_docs)
        st.download_button(
            label="Download API Docs", data=cleaned_docs, file_name="API_DOCS.md", mime="text/markdown"
        )
    else:
        st.info("Click the 'Generate API Docs' button in the sidebar after analyzing a repository.")
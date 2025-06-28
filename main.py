import streamlit as st
import os
import re

# --- 1. Imports: Grouped for clarity ---
# Backend modules
from src.git_utils import clone_or_pull_repo
from src.index_builder import get_or_create_index
from src.query_router import create_query_router
from src.doc_generator import generate_quick_start

# LlamaIndex modules
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core import Settings


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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "repo_path" not in st.session_state:
    st.session_state.repo_path = None
if "quick_start_guide" not in st.session_state:
    st.session_state.quick_start_guide = None


# --- 5. Application UI and Logic ---

# Render the title and caption
st.title("🤖 RepoInsightAI")
st.caption("Deeply understand any codebase and chat with your GitHub projects.")

# Setup the sidebar for configuration and actions
with st.sidebar:
    st.header("1. Configure Your Codebase")
    repo_url = st.text_input(
        "Enter GitHub Repository URL",
        placeholder="e.g., https://github.com/streamlit/streamlit"
    )

    if st.button("Analyze Repository", type="primary", use_container_width=True):
        if not repo_url or not repo_url.startswith("https://github.com"):
            st.error("Please enter a valid GitHub HTTPS URL!")
        else:
            # This block runs when the user starts an analysis.
            # It performs all heavy lifting and stores results in the session state.
            with st.spinner("Analysis in progress, please wait..."):
                try:
                    # Clear any previous results
                    st.session_state.quick_start_guide = None
                    st.session_state.messages = []
                    
                    st.info("Step 1: Cloning repository...")
                    st.session_state.repo_path = clone_or_pull_repo(repo_url)
                    
                    st.info("Step 2: Building knowledge index...")
                    vector_index, nodes = get_or_create_index(st.session_state.repo_path)
                    
                    st.info("Step 3: Creating smart query router...")
                    query_engine = create_query_router(vector_index, nodes, verbose=False)
                    
                    st.info("Step 4: Creating stateful chat engine...")
                    st.session_state.chat_engine = CondenseQuestionChatEngine.from_defaults(
                        query_engine=query_engine,
                        verbose=False
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
        
        if st.button("Generate Quick Start Guide", use_container_width=True):
            with st.spinner("🚀 Generating Quick Start Guide... This may take a moment."):
                guide = generate_quick_start(
                    st.session_state.repo_path,
                    st.session_state.chat_engine, # Pass the chat engine for summarization
                    Settings.llm
                )
                st.session_state.quick_start_guide = guide
            st.success("Quick Start Guide generated!")
            # No need to rerun, Streamlit will update the tab content automatically

    st.divider()
    st.info("Powered by LlamaIndex.")

# --- 6. Main Page Content (Tabs) ---

# Set up a welcome message if the chat is empty
if not st.session_state.messages:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please enter a GitHub repository URL on the left and click 'Analyze' to get started."}
    ]

# Create tabs for different functionalities
tab_chat, tab_quick_start = st.tabs(["💬 Chat with Repo", "🚀 Quick Start Guide"])

# --- Chat Tab Logic (Canonical Pattern) ---
with tab_chat:
    # 1. First, display all historical messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 2. Then, render the chat input at the bottom.
    # The `if` block executes ONLY when the user submits a new message.
    if prompt := st.chat_input("Ask anything about this codebase..."):
        # Ensure the engine is ready before processing
        if not st.session_state.chat_engine:
            st.warning("Please analyze a repository first.", icon="⚠️")
        else:
            # 3. Add user's new message to the state
            st.session_state.messages.append({"role": "user", "content": prompt})

            # 4. Get AI's response
            with st.spinner("AI is thinking..."):
                response = st.session_state.chat_engine.chat(prompt)
                ai_response = str(response)
            
            # 5. Add AI's new response to the state
            st.session_state.messages.append({"role": "assistant", "content": ai_response})

            # 6. Let Streamlit rerun from the top.
            # The rerun will automatically display the new messages from the state.
            st.rerun()

# Quick Start Guide Tab Logic
with tab_quick_start:
    if st.session_state.quick_start_guide:
        # Clean and display the generated guide
        cleaned_guide = clean_markdown_output(st.session_state.quick_start_guide)
        st.markdown(cleaned_guide)
        
        # Add a download button for the guide
        st.download_button(
            label="Download Guide",
            data=cleaned_guide,
            file_name="QUICK_START_GUIDE.md",
            mime="text/markdown",
        )
    else:
        st.info("Click the 'Generate Quick Start Guide' button in the sidebar after analyzing a repository to see the guide here.")
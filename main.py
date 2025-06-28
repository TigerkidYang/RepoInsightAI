# main.py

import streamlit as st
import os

# UPDATED: Import the correct chat engine for this use case
from llama_index.core.chat_engine import CondenseQuestionChatEngine

# Import your existing backend modules
from src.git_utils import clone_or_pull_repo
from src.index_builder import get_or_create_index
from src.query_router import create_query_router

# --- 1. Page Configuration (No changes) ---
st.set_page_config(
    page_title="RepoInsightAI - Your AI GitHub Repo Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Application Title and Caption (No changes) ---
st.title("🤖 RepoInsightAI")
st.caption("Deeply understand any codebase and chat with your GitHub projects.")

# --- 3. Session State Initialization (No changes) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please enter a GitHub repository URL on the left and click 'Analyze' to get started."}
    ]
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None

# --- 4. Sidebar for User Input and Control ---
with st.sidebar:
    st.header("Configure Your Codebase")
    
    repo_url = st.text_input(
        "Enter GitHub Repository URL", 
        placeholder="e.g., https://github.com/streamlit/streamlit-example"
    )

    if st.button("Analyze Repository", type="primary", use_container_width=True):
        if not repo_url or not repo_url.startswith("https://github.com"):
            st.error("Please enter a valid GitHub HTTPS URL!")
        else:
            with st.spinner("Analysis in progress, please wait..."):
                try:
                    # Steps 1 & 2 (No changes)
                    st.info("Step 1: Cloning/updating repository...")
                    repo_path = clone_or_pull_repo(repo_url)
                    st.info("Step 2: Building/loading knowledge index...")
                    vector_index, nodes = get_or_create_index(repo_path)
                    
                    # Step 3: Create the base query engine (the router)
                    st.info("Step 3: Creating smart query router...")
                    query_engine = create_query_router(vector_index, nodes, verbose=False)
                    
                    # --- START OF CORRECTIONS ---
                    
                    # NEW: Step 4 - Wrap the query engine in a stateful CondenseQuestionChatEngine
                    st.info("Step 4: Creating stateful chat engine with memory...")
                    st.session_state.chat_engine = CondenseQuestionChatEngine.from_defaults(
                        query_engine=query_engine, # Pass the entire router query engine directly
                        # This chat engine has its own built-in memory management
                        verbose=False # Set to True in console to see the condensed question
                    )
                    
                    # --- END OF CORRECTIONS ---

                    # Reset chat history
                    repo_name = os.path.basename(repo_path)
                    st.session_state.messages = [
                        {"role": "assistant", "content": f"✅ Repository '{repo_name}' is ready! The chat now has memory. You can ask follow-up questions."}
                    ]
                    st.success("Analysis complete!")
                    
                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")

    st.divider()
    st.info("Powered by LlamaIndex.")

# --- 5. Main Chat Interface (No changes to this section) ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What would you like to know about this codebase?"):
    if st.session_state.chat_engine is None:
        st.warning("Please enter a repository URL and click 'Analyze' first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("AI is thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
        
        ai_response = str(response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.markdown(ai_response)
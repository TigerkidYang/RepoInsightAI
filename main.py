import streamlit as st
import os

# Import the core backend modules you've already created and tested
from src.git_utils import clone_or_pull_repo
from src.index_builder import get_or_create_index

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="RepoInsightAI - Your AI GitHub Repo Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Application Title and Caption ---
st.title("🤖 RepoInsightAI")
st.caption("Deeply understand any codebase and chat with your GitHub projects.")

# --- 3. Session State Initialization ---
# This is crucial for Streamlit apps to maintain data across user interactions (reruns)
# Initialize chat history with a welcome message
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Please enter a GitHub repository URL on the left and click 'Analyze' to get started."}
    ]
# Initialize the chat engine
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None

# --- 4. Sidebar for User Input and Control ---
with st.sidebar:
    st.header("Configure Your Codebase")
    
    # Get the GitHub URL from the user
    repo_url = st.text_input(
        "Enter GitHub Repository URL", 
        placeholder="e.g., https://github.com/streamlit/streamlit-example"
    )

    # "Analyze Repository" button
    if st.button("Analyze Repository", type="primary", use_container_width=True):
        # a. Validate the input
        if not repo_url or not repo_url.startswith("https://github.com"):
            st.error("Please enter a valid GitHub HTTPS URL!")
        else:
            # b. Execute backend logic with real-time feedback
            with st.spinner("Analysis in progress, please wait... (First time may take a few minutes)"):
                try:
                    # Call backend functions
                    st.info("Step 1: Cloning/updating repository...")
                    repo_path = clone_or_pull_repo(repo_url)
                    
                    st.info("Step 2: Building/loading knowledge index...")
                    index = get_or_create_index(repo_path)
                    
                    # c. Create the chat engine and save it to the session state
                    st.session_state.chat_engine = index.as_chat_engine(
                        chat_mode="condense_plus_context", # An optimized chat mode
                        verbose=False # Usually disabled for UI
                    )
                    
                    # d. Reset chat history for the new session
                    repo_name = os.path.basename(repo_path)
                    st.session_state.messages = [
                        {"role": "assistant", "content": f"✅ Repository '{repo_name}' is ready! You can now ask any questions about it."}
                    ]
                    st.success("Analysis complete!")
                    
                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")

    # Add some extra info or help
    st.divider()
    st.info("Powered by LlamaIndex.")

# --- 5. Main Chat Interface ---

# a. Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# b. Get new user input
if prompt := st.chat_input("What would you like to know about this codebase?"):
    # c. Ensure the chat engine is ready before proceeding
    if st.session_state.chat_engine is None:
        st.warning("Please enter a repository URL and click 'Analyze' first.")
    else:
        # d. Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # e. Generate AI response with a thinking indicator
        with st.spinner("AI is thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
        
        # f. Add AI response to history and display it
        ai_response = str(response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.markdown(ai_response)
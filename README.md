# 🤖 RepoInsightAI

**Deeply understand any codebase and chat with your GitHub projects using an advanced AI Agent.**

RepoInsightAI is a powerful web application built with LlamaIndex and Streamlit that acts as an AI-powered assistant for developers. Simply provide a GitHub repository URL, and the application will ingest, index, and analyze the entire codebase, enabling you to:

-   **Chat with the repository** to understand code, fix bugs, or get implementation details.
-   **Automatically generate crucial documentation**, such as a "Quick Start Guide" and "API Documentation".
-   **Explore the repository structure** with an interactive file tree.
-   **Leverage internet search** for questions about external libraries or general concepts.

---

## ✨ Features

-   **Multi-Tool AI Agent**: At its core, RepoInsightAI uses a sophisticated `OpenAIAgent` that can intelligently choose from a suite of tools to best answer your query.
-   **Smart Codebase Q&A**: The agent uses a `RouterQueryEngine` to decide whether to perform a semantic vector search for specific code details or to summarize information for high-level questions.
-   **Conversational Memory**: The agent remembers the context of your conversation, allowing for natural follow-up questions.
-   **Automated Document Generation**:
    -   **Quick Start Guide**: Automatically identifies key files (README, package.json, main entry points) and synthesizes them into a coherent getting-started guide.
    -   **API Documentation**: Parses source code files to extract classes, functions, and their signatures, generating structured API docs on the fly.
-   **Repository Tools**:
    -   **File Tree Viewer**: Instantly generates a clean, explorable file tree of the repository.
    -   **Internet Search**: Seamlessly searches the web using DuckDuckGo to answer questions about external libraries, concepts, or real-time information.
-   **Robust Multi-Language Support**: Thanks to a multi-parser architecture, it can intelligently process repositories containing Python, JavaScript, Java, Go, and many other languages.
-   **Interactive Web UI**: A clean, intuitive, and responsive user interface built with Streamlit.

---

## 🛠️ Tech Stack

-   **Core AI Framework**: LlamaIndex
-   **LLM & Agent**: OpenAI (`OpenAIAgent`)
-   **Web Framework**: Streamlit
-   **Code Processing**:
    -   GitPython (for cloning repos)
    -   tree-sitter & tree-sitter-languages (for code-aware splitting)
-   **Search**: duckduckgo-search
-   **Environment Management**: `dotenv`, `venv`

---

## 🚀 Getting Started

Follow these steps to run RepoInsightAI on your local machine.

### 1. Prerequisites

-   Python 3.10+
-   An OpenAI API Key

### 2. Installation

First, clone the repository to your local machine:
```bash
git clone https://github.com/TigerkidYang/RepoInsightAI.git
cd RepoInsightAI
```

Next, create a Python virtual environment and activate it. This keeps your project dependencies isolated.
```bash
# Create a virtual environment
python -m venv .venv

# Activate it (on Windows)
.\.venv\Scripts\activate

# Or on macOS/Linux
source .venv/bin/activate
```

Install all the required packages using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a file named `.env` in the root directory of the project. This file will store your secret keys and configurations.

Copy the following content into your `.env` file and replace `"sk-..."` with your actual OpenAI API Key.

```env
REPOS_DIR = ./repos
STORAGE_DIR = ./storage

# OPENAI
OPENAI_API_KEY = "YOUT_API_KEY_HERE"

LLM_MODEL = "o3-mini"
EMBEDDING_MODEL = "text-embedding-3-large"
```

### 4. Running the Application

You are now ready to launch the Streamlit app! Run the following command in your terminal:

```bash
streamlit run main.py
```

Streamlit will automatically open a new tab in your web browser at `http://localhost:8501`. Enjoy exploring codebases with your AI assistant!

---

## ⚙️ How It Works: Architecture Overview

The power of RepoInsightAI lies in its modular and agentic architecture.

1.  **UI (Streamlit)**: The user interacts with the application, providing a GitHub URL and asking questions.
2.  **Analysis Pipeline**:
    -   **Git Clone (`git_utils.py`)**: The repository is cloned or updated locally.
    -   **Indexing (`index_builder.py`)**: The codebase is processed. A robust multi-parser system identifies files by language, uses the appropriate `CodeSplitter` for each, and creates a `VectorStoreIndex`. The index and parsed nodes are persisted to disk for efficiency.
3.  **The AI Agent (`main.py`)**: An `OpenAIAgent` is initialized with a powerful set of tools.
4.  **Tool-Use Workflow**: When a user asks a question:
    -   The **`OpenAIAgent`** receives the query.
    -   It thinks and decides which tool is best suited for the job:
        -   If the question is about **code details or project purpose**, it selects the **`codebase_qa_system`** tool. This tool is a `RouterQueryEngine` that further decides whether to use vector search (for specifics) or summarization (for overviews).
        -   If the question is about **file structure**, it selects the **`file_tree_viewer`** tool.
        -   If the question requires **external knowledge**, it selects the **`internet_search`** tool.
    -   The selected tool is executed, and its output is used by the agent to formulate the final answer.
5.  **Document Generation (`doc_generator.py`)**: When requested, dedicated functions use a multi-step LLM chain (Identify -> Summarize -> Synthesize) to generate high-quality Markdown documents like the Quick Start Guide and API Docs.

This multi-tool, agentic approach allows RepoInsightAI to handle a much wider and more complex range of tasks than a simple RAG pipeline.

---

## 🗺️ Future Work & Roadmap

RepoInsightAI is currently a powerful tool, but the journey has just begun. We have an exciting roadmap of features planned to make it even more intelligent and versatile. Contributions in these areas are highly welcome\!

  * **Multi-LLM Provider Support**

      * **Goal**: To move beyond OpenAI and add support for other leading LLM providers like **Anthropic (Claude)**, **Google (Gemini)**, and open-source models via **Ollama**.
      * **Implementation**: This would involve creating an abstraction layer for the LLM and embedding models, allowing users to select their preferred provider from a configuration file or the UI.

  * **Advanced Static Analysis Tools**

      * **Goal**: To provide deeper, quantitative insights into code quality.
      * **Implementation**: Create new tools for the agent that can:
          * Calculate **code complexity** (e.g., Cyclomatic Complexity) using libraries like `radon` for Python.
          * Identify "code smells" or potential bugs.
          * Visualize dependencies between files and modules.

  * **Git History Analysis**

      * **Goal**: To understand the evolution and dynamics of the repository.
      * **Implementation**: Add new tools that use the `.git` history to answer questions like:
          * *"What were the major changes in the last month?"* (by summarizing commit messages).
          * *"Show me the code churn for the most critical files."*
          * *"Who are the most active contributors in the `backend` directory?"*

  * **Code Execution Sandbox**

      * **Goal**: To enable the agent to **verify** its own findings and generated instructions.
      * **Implementation**: A long-term vision to integrate a secure sandbox environment (e.g., a Docker container) where the agent can:
          * Run the project's test suite.
          * Execute the installation commands it generated in the "Quick Start Guide" to confirm they work.
          * Run a single function to test its output.

  * **Enhanced UI/UX**

      * **Goal**: To give users more control and a richer experience.
      * **Implementation**:
          * Add a configuration panel in the UI to let users tweak settings (e.g., `CodeSplitter` chunk size, `max_depth` for file tree).
          * Implement real-time, streaming responses in the chat for a more dynamic feel.
          * Visualize code relationships using interactive graphs.

---

## ❤️ Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. We welcome contributions of all kinds to RepoInsightAI\!

Whether you're fixing a bug, adding a new feature, improving the documentation, or suggesting a new idea, your help is greatly appreciated.

### How to Contribute

1.  **Fork the Repository**: Click the 'Fork' button at the top right of this page to create your own copy.
2.  **Create a Feature Branch**:
    ```bash
    git checkout -b feature/YourAmazingFeature
    ```
3.  **Make Your Changes**: Add your new feature or fix the bug.
4.  **Commit Your Changes**:
    ```bash
    git commit -m 'Add: YourAmazingFeature'
    ```
5.  **Push to Your Branch**:
    ```bash
    git push origin feature/YourAmazingFeature
    ```
6.  **Open a Pull Request**: Go to your forked repository on GitHub and open a new Pull Request against the `main` branch of this project.

### Areas We Need Help With

  - Implementing any of the features listed in our **Future Work & Roadmap**.
  - Adding support for more language parsers in our `language_utils`.
  - Improving the accuracy and comprehensiveness of the `exclude` list for different project types.
  - Refining the prompts in `doc_generator.py` to produce even better results.
  - Enhancing the Streamlit UI with new features and a better layout.

We are excited to see your contributions\!
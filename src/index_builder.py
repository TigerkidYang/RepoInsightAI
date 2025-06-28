# src/index_builder.py

from collections import defaultdict
import os
from dotenv import load_dotenv
load_dotenv()
# for index
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    SummaryIndex,
    StorageContext,
    load_index_from_storage,
    Settings, 
)
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter
from llama_index.core.schema import BaseNode
# for llm and embedding
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
# for document
from llama_index.core import Document
from typing import List, Tuple
# for language detection
from src.language_utils import EXTENSION_TO_LANGUAGE_MAP

# LLM and Embedding Global Settings
Settings.llm = OpenAI(model=os.getenv("LLM_MODEL"))
Settings.embed_model = OpenAIEmbedding(model=os.getenv("EMBEDDING_MODEL"))

STORAGE_DIR = os.getenv("STORAGE_DIR")

def get_or_create_index(repo_path: str) -> Tuple[VectorStoreIndex, List[BaseNode]]:
    """
    Creates a LlamaIndex VectorStoreIndex from a local repository path.
    If an index has already been created and persisted for this repository,
    it loads the index from storage instead of rebuilding it.

    Args:
        repo_path (str): The absolute local path to the cloned repository.

    Returns:
        VectorStoreIndex: The loaded or newly created LlamaIndex object.
    """
    # Generate storage path based on repo_path
    repo_name = os.path.basename(repo_path)
    storage_path = os.path.join(STORAGE_DIR, repo_name)

    # decide load or create index
    if os.path.exists(storage_path):
        # load index from storage
        storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        index = load_index_from_storage(storage_context)
        nodes = list(index.docstore.docs.values())

    else:
        # create index
        
        # define exclude files
        exclude = [
            # === Version Control ===
            ".git", ".svn", ".hg", ".bzr",

            # === Dependencies & Build Artifacts (Comprehensive) ===
            "node_modules",   # JavaScript
            "bower_components", # JavaScript (legacy)
            "vendor",         # PHP (Composer), Go
            "target",         # Rust, Java (Maven/Gradle)
            "build",          # General
            "dist",           # General
            "bin",            # Compiled binaries
            "obj",            # Compiled object files
            ".gradle",        # Gradle cache
            "__pycache__",    # Python cache
            "*.pyc",          # Python compiled files
            "*.pyo",          # Python optimized files
            "*.egg-info",     # Python packaging metadata

            # === Virtual Environments ===
            "venv", ".venv", "env", ".env", "ENV",

            # === IDE / Editor Specific ===
            ".idea",          # JetBrains IDEs
            ".vscode",        # Visual Studio Code
            ".vs",            # Visual Studio
            ".sublime-project",
            ".sublime-workspace",
            ".project",       # Eclipse
            ".classpath",     # Eclipse
            ".settings",      # Eclipse
            "*.swp",          # Vim swap file
            "*.swo",          # Vim swap file

            # === Operating System / Misc ===
            ".DS_Store",      # macOS
            "Thumbs.db",      # Windows
            "desktop.ini",    # Windows

            # === Logs, Caches, Temp Files ===
            "*.log",
            "*.tmp",
            "*.temp",
            "cache",
            ".cache",
            "logs",

            # === Binary & Asset Files (Crucial to exclude) ===
            # Images
            "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.tiff", "*.webp", "*.ico", "*.svg",
            # Audio
            "*.mp3", "*.wav", "*.ogg", "*.flac",
            # Video
            "*.mp4", "*.mkv", "*.mov", "*.avi", "*.webm",
            # Fonts
            "*.ttf", "*.otf", "*.woff", "*.woff2",
            # Archives & Compressed files
            "*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2", "*.xz",
            # Documents (unless you want to index their text content)
            "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx", "*.odt",
            # Executables & Libraries
            "*.exe", "*.dll", "*.so", "*.a", "*.lib", "*.jar", "*.war",

            # === Dependency Lock Files ===
            # These are often huge and their info is redundant if package.json etc. is indexed.
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
            "Pipfile.lock",
            "composer.lock",
        ]

        # load data
        reader = SimpleDirectoryReader(
            input_dir=repo_path,
            exclude=exclude,
            recursive=True,
        )
        documents = reader.load_data(show_progress=True)

        # group documents by language
        docs_by_language = defaultdict(list)
        for doc in documents:
            file_extension = os.path.splitext(doc.metadata.get('file_path', ''))[1]
            language = EXTENSION_TO_LANGUAGE_MAP.get(file_extension, "default")
            docs_by_language[language].append(doc)

        # parse each group with specific parser
        all_nodes = []
        for language, lang_docs in docs_by_language.items():
            parser = None
            if language == 'default':
                # For markdown, text, or unknown files, use a simple text splitter
                parser = SentenceSplitter()
            else:
                # For code files, try to use the CodeSplitter
                try:
                    parser = CodeSplitter(language=language)
                except Exception as e:
                    # If a specific language parser fails to load, we warn and skip
                    print(f"   [!] Warning: Could not initialize parser for language '{language}'. Skipping these files. Error: {e}")
                    continue
            
            # Parse the documents with the selected parser
            try:
                nodes = parser.get_nodes_from_documents(lang_docs, show_progress=True)
                all_nodes.extend(nodes)
            except Exception as e:
                print(f"   [!] Error parsing documents for language '{language}'. Skipping. Error: {e}")

        # create the final index from all collected nodes
        if not all_nodes:
            raise ValueError("No documents were successfully parsed. Cannot create an index.")
            
        index = VectorStoreIndex(all_nodes, show_progress=True)
        index.storage_context.persist(persist_dir=storage_path)
        nodes = all_nodes
    
    return index, nodes
        
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
from llama_index.core.node_parser import CodeSplitter
# for llm and embedding
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
# for document
from llama_index.core import Document
from typing import List, Tuple

# LLM and Embedding Global Settings
Settings.llm = OpenAI(model=os.getenv("LLM_MODEL"))
Settings.embed_model = OpenAIEmbedding(model=os.getenv("EMBEDDING_MODEL"))

STORAGE_DIR = os.getenv("STORAGE_DIR")

def get_or_create_index(repo_path: str) -> Tuple[VectorStoreIndex, List[Document]]:
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
        
        # define require and exclude files
        required = [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp"]
        exclude = [".git", "node_modules", "dist", "build", "venv", ".venv"]

        # load data
        reader = SimpleDirectoryReader(
            input_dir=repo_path,
            required_exts=required,
            exclude=exclude,
            recursive=True,
        )
        documents = reader.load_data(show_progress=True)

        # define splitter
        code_splitter = CodeSplitter(
            language="python",
            chunk_lines=40,
            chunk_lines_overlap=15,
            max_chars=1500,
        )

        # pass the parser
        Settings.node_parser = code_splitter
        nodes = Settings.node_parser.get_nodes_from_documents(documents, show_progress=True)

        # create index and persist it
        index = VectorStoreIndex(nodes, show_progress=True)
        index.storage_context.persist(persist_dir=storage_path)
    
    return index, nodes
        
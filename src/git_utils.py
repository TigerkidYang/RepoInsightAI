import os
import git
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

REPOS_DIR = os.getenv("REPOS_DIR")

def clone_or_pull_repo(repo_url: str) -> str:
    """
    Clones a repository if it doesn't exist locally, or pulls the latest changes if it does.

    Args:
        repo_url (str): The HTTPS or SSH URL of the Git repository.

    Returns:
        str: The absolute local path to the cloned repository.

    Raises:
        git.exc.GitCommandError: If the git command fails (e.g., invalid URL, authentication failed).
        Exception: For other potential errors during path creation.
    """
    # if no REPOS_DIR, create it
    if not os.path.exists(REPOS_DIR):
        os.makedirs(REPOS_DIR)

    # parse the repo name from the url
    # https://github.com/TigerkidYang/RepoInsightAI.git -> RepoInsightAI
    parsed_url = urlparse(repo_url)
    repo_name = parsed_url.path.split("/")[-1].split('.')[0]
    local_repo_path = REPOS_DIR + "/" + repo_name

    # decide clone or pull
    if os.path.exists(local_repo_path):
        # pull the latest changes
        try:
            repo = git.Repo(local_repo_path)
            repo.remotes.origin.pull()
        except Exception as e:
            print(f"Error pulling repository: {e}")
            return None
    else:
        # clone the repository
        try:
            git.Repo.clone_from(repo_url, local_repo_path)
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return None
    
    return local_repo_path

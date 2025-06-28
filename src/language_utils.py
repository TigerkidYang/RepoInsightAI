# src/language_utils.py
EXTENSION_TO_LANGUAGE_MAP = {
    # === Web Development: Frontend ===
    ".js": "javascript",
    ".jsx": "javascript", # JSX is parsed by the JavaScript parser
    ".ts": "typescript",
    ".tsx": "typescript", # TSX is parsed by the TypeScript parser
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",      # SASS/SCSS
    ".less": "less",

    # === Web Development: Backend & General Purpose ===
    ".py": "python",
    ".java": "java",
    ".php": "php",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".cs": "c_sharp",     # C#
    ".kt": "kotlin",
    ".kts": "kotlin",     # Kotlin Script
    ".scala": "scala",
    ".swift": "swift",
    ".m": "objc",         # Objective-C
    ".pl": "perl",
    ".lua": "lua",
    ".ex": "elixir",
    ".exs": "elixir",
    ".dart": "dart",
    ".erl": "erlang",
    ".hrl": "erlang",

    # === C Family ===
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",        # C++
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",

    # === Data & Configuration ===
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "html",       # The HTML parser can handle XML structures well for splitting
    ".sql": "sql",
    ".csv": "python",     # No specific CSV parser, Python parser can handle it as plain text

    # === Shell & DevOps ===
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    "Dockerfile": "dockerfile",
    ".tf": "terraform",
    ".hcl": "terraform",  # HashiCorp Configuration Language
    ".groovy": "java",    # Groovy has Java-like syntax
    ".jenkinsfile": "java",

    # === Documentation & Markup ===
    ".md": "markdown",
    ".rst": "markdown",   # reStructuredText can be treated as markdown for basic splitting
    ".tex": "latex",

    # === Functional Programming ===
    ".hs": "haskell",
    ".fs": "f_sharp",
    ".fsi": "f_sharp",
    ".ml": "ocaml",
    ".mli": "ocaml",

    # === Mobile Development ===
    # .swift, .kt, .java, .dart are already covered above

    # === Special Cases & Others ===
    ".vue": "vue",
    ".svelte": "svelte",
    ".res": "rescript",   # ReScript
}

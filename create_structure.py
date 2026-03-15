import os

def find_project_root(start_path='.'):
    """
    Walks backward from the current directory to find the project root.
    Assumes the root is the directory containing '.git' or 'README.md' as markers.
    """
    current_path = os.path.abspath(start_path)
    while current_path != os.path.dirname(current_path):  # Stop at filesystem root
        if os.path.exists(os.path.join(current_path, '.git')) or os.path.exists(os.path.join(current_path, 'README.md')):
            return current_path
        current_path = os.path.dirname(current_path)
    raise FileNotFoundError("Project root not found. Ensure you're inside the project directory with markers like '.git' or 'README.md'.")

def create_structure(root_path):
    """
    Creates the folder and file structure, skipping if they already exist.
    """
    # Define the structure as a dict of paths (folders end with '/', files are strings)
    structure = {
        '.gitignore': '',
        'README.md': '',
        'pyproject.toml': '',
        'appliance/': None,
        'appliance/requirements.txt': '',
        'appliance/src/': None,
        'appliance/src/__init__.py': '',
        'appliance/src/edge_rl.py': '',
        'appliance/src/telemetry_ingest.py': '',
        'appliance/tests/': None,
        'appliance/tests/__init__.py': '',
        'assistant/': None,
        'assistant/requirements.txt': '',
        'assistant/src/': None,
        'assistant/src/__init__.py': '',
        'assistant/src/app.py': '',
        'assistant/src/config.py': '',
        'assistant/src/routers/': None,
        'assistant/src/routers/__init__.py': '',
        'assistant/src/routers/governance.py': '',
        'assistant/tests/': None,
        'assistant/tests/__init__.py': '',
        'docs/': None,
        'docs/architecture.md': '',
        'docs/backlog.md': '',
        'docs/online_todo.md': '',
        'docs/risks.md': '',
        'docs/vision.md': '',
        'scripts/': None,
        'scripts/update.sh': '',
        'shared/': None,
        'shared/src/': None,
        'shared/src/__init__.py': '',
        'shared/src/db_schema.py': '',
        'shared/tests/': None,
        'shared/tests/__init__.py': '',
    }

    for path, content in structure.items():
        full_path = os.path.join(root_path, path)
        if path.endswith('/'):  # Folder
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                print(f"Created folder: {full_path}")
            else:
                print(f"Skipped existing folder: {full_path}")
        else:  # File
            dir_name = os.path.dirname(full_path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            if not os.path.exists(full_path):
                with open(full_path, 'w') as f:
                    f.write(content or '')  # Empty or with optional content
                print(f"Created file: {full_path}")
            else:
                print(f"Skipped existing file: {full_path}")

if __name__ == "__main__":
    project_root = find_project_root()
    print(f"Found project root: {project_root}")
    create_structure(project_root)
import subprocess
import os

WORKSPACE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

def _resolve_path(path: str) -> str:
    """Helper to resolve paths within the workspace sandbox."""
    # Ensure workspace exists
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    # Join the workspace directory with the relative path
    # Use normpath to handle redundant separators and navigate up (though realpath is better for security)
    full_path = os.path.normpath(os.path.join(WORKSPACE_DIR, path))
    # Security check: ensure the resulting path is still inside the workspace
    # This prevents directory traversal attacks (e.g., passing "../../etc/passwd")
    abs_workspace = os.path.abspath(WORKSPACE_DIR)
    abs_path = os.path.abspath(full_path)
    if not abs_path.startswith(abs_workspace):
        raise ValueError(f"Path {path} is outside the allowed workspace.")
    return full_path

def read_file(path: str) -> str:
    """Reads the content of a file from the workspace sandbox."""
    try:
        resolved_path = _resolve_path(path)
        with open(resolved_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Writes content to a file in the workspace sandbox. Creates directories if needed."""
    try:
        resolved_path = _resolve_path(path)
        os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
        with open(resolved_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path} within workspace"
    except Exception as e:
        return f"Error writing to file {path}: {str(e)}"

def list_directory(path: str = ".") -> str:
    """Lists files in a given directory within the workspace."""
    try:
        resolved_path = _resolve_path(path)
        if not os.path.exists(resolved_path):
            return f"Directory {path} does not exist."
        files = os.listdir(resolved_path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing directory {path}: {str(e)}"

def execute_command(command: str) -> str:
    """Executes a terminal/shell command within the workspace sandbox."""
    try:
        # Ensure workspace exists
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30,
            cwd=WORKSPACE_DIR # Set working directory to workspace
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return f"Exit Code {result.returncode} Output: {output}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

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

def validate_code_blocks(path: str) -> str:
    """Parses markdown files to extract code blocks and validate their syntax (e.g., Python)."""
    try:
        import ast
        import json
        resolved_path = _resolve_path(path)
        with open(resolved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        in_block = False
        lang = ""
        block_lines = []
        block_start = 0
        errors = []
        
        for i, line in enumerate(lines, 1):
            if line.startswith("```"):
                if not in_block:
                    in_block = True
                    lang = line[3:].strip().lower()
                    block_lines = []
                    block_start = i
                else:
                    in_block = False
                    block_content = "\n".join(block_lines)
                    # Validate block content based on lang
                    if lang in ["python", "py"]:
                        try:
                            ast.parse(block_content)
                        except SyntaxError as e:
                            # Adjust lineno relative to the file line
                            error_line = block_start + (e.lineno or 1) - 1
                            errors.append(f"Python Syntax Error in block starting at line {block_start}: {e.msg} (around file line {error_line})")
                    elif lang == "json":
                        try:
                            json.loads(block_content)
                        except Exception as e:
                            errors.append(f"JSON Syntax Error in block starting at line {block_start}: {str(e)}")
            elif in_block:
                block_lines.append(line)
        
        if errors:
            return "Validation Failed:\n" + "\n".join(errors)
        return "Validation Passed: All code blocks are syntactically correct."
    except Exception as e:
        return f"Error validating code blocks in file {path}: {str(e)}"


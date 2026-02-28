import subprocess
import os

def read_file(path: str) -> str:
    """Reads the content of a file from the local filesystem."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Writes content to a file in the local filesystem. Creates directories if needed."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file {path}: {str(e)}"

def execute_command(command: str) -> str:
    """Executes a terminal/shell command and returns the output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return f"Exit Code {result.returncode} Output: {output}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

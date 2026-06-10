import os
import re
from pathlib import Path

class ScannerService:
    def __init__(self, repo_root: str) -> None:
        """Initialize the ScannerService with a repository root path.
        
        Args:
            repo_root: The absolute path to the repository root.
        """
        self.repo_root = Path(repo_root).resolve()

    def _safe_resolve(self, relative_path: str) -> Path:
        """Safely resolve a path relative to the repository root.
        
        Args:
            relative_path: The path to resolve.
            
        Returns:
            The resolved absolute Path.
        """
        resolved = (self.repo_root / relative_path).resolve()
        if not resolved.is_relative_to(self.repo_root):
            raise ValueError(f"Path is outside the repository root: {relative_path}")
        return resolved

    def scan_todos(self, directory: str) -> list[dict[str, str | int]]:
        """Scan a directory recursively for TODO, FIXME, HACK, XXX comments.
        
        Args:
            directory: The directory path relative to the repo root.
            
        Returns:
            A list of dicts containing 'file', 'line_number', and 'text'.
        """
        dir_path = self._safe_resolve(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        markers = ["TODO", "FIXME", "HACK", "XXX"]
        # Compile a regex to match any of the markers as whole words or starting patterns
        pattern = re.compile(rf"\b({'|'.join(markers)})\b")
        results = []

        # List of binary extensions or directories to ignore
        ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "build", "dist"}
        ignored_exts = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz", ".mp3", ".mp4", ".pyc", ".db"}

        for root, dirs, filenames in os.walk(dir_path):
            # Prune ignored directories in place
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix.lower() in ignored_exts:
                    continue

                rel_path = file_path.relative_to(self.repo_root)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append({
                                    "file": str(rel_path),
                                    "line_number": idx,
                                    "text": line.strip()
                                })
                except Exception:
                    # Ignore read failures on files that might be binary/unreadable
                    continue

        return results

    def find_large_functions(self, file_path: str) -> list[dict[str, str | int]]:
        """Identify large functions (over 40 lines) in a file using a simple heuristic.
        
        Args:
            file_path: Relative path to the file from the repo root.
            
        Returns:
            A list of dicts with function name, starting line, and length.
        """
        resolved_path = self._safe_resolve(file_path)
        if not resolved_path.is_file():
            raise ValueError(f"File not found: {file_path}")

        # Only run on supported source code types (python, javascript/typescript, java, go)
        supported_suffixes = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go"}
        if resolved_path.suffix not in supported_suffixes:
            return []

        results = []
        try:
            with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}")

        # Python simple parser
        if resolved_path.suffix == ".py":
            # Find python functions by looking for `def ` or `class ` definitions
            # A simple indentation tracker
            current_func = None
            for idx, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    # Save the previous one if it was large
                    if current_func:
                        length = idx - current_func["start_line"]
                        if length > 40:
                            current_func["line_count"] = length
                            results.append(current_func)
                    
                    # Extract function name
                    match = re.search(r"def\s+([a-zA-Z0-9_]+)", stripped)
                    name = match.group(1) if match else "unknown"
                    
                    # Store new function tracking
                    current_func = {
                        "file": file_path,
                        "function": name,
                        "start_line": idx,
                        "line_count": 0
                    }
                elif current_func and stripped and not line.startswith(" ") and not line.startswith("\t"):
                    # Indentation returned to 0, function ended
                    length = idx - current_func["start_line"]
                    if length > 40:
                        current_func["line_count"] = length
                        results.append(current_func)
                    current_func = None
            
            # Flush the last function
            if current_func:
                length = len(lines) - current_func["start_line"] + 1
                if length > 40:
                    current_func["line_count"] = length
                    results.append(current_func)

        else:
            # Curly brace languages (JS/TS/Java/Go)
            # Find `function name(...) {` or method declarations using regex
            # Let's do a basic brace-matching heuristic
            func_pattern = re.compile(
                r"(?:function\s+([a-zA-Z0-9_]+)|([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{)"
            )
            
            for idx, line in enumerate(lines, 1):
                match = func_pattern.search(line)
                if match:
                    # Find function name
                    name = match.group(1) or match.group(2) or "anonymous"
                    # Count matching braces or search lines ahead to estimate function end
                    brace_count = 0
                    found_open = False
                    end_idx = idx
                    
                    for check_idx in range(idx - 1, len(lines)):
                        check_line = lines[check_idx]
                        if "{" in check_line:
                            brace_count += check_line.count("{")
                            found_open = True
                        if "}" in check_line:
                            brace_count -= check_line.count("}")
                        
                        if found_open and brace_count <= 0:
                            end_idx = check_idx + 1
                            break
                    
                    length = end_idx - idx + 1
                    if length > 40:
                        results.append({
                            "file": file_path,
                            "function": name,
                            "start_line": idx,
                            "line_count": length
                        })

        return results

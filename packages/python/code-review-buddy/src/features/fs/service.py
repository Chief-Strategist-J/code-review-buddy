import os
from pathlib import Path


class FileSystemService:
    def __init__(self, repo_root: str) -> None:
        """Initialize the FileSystemService with a repository root path.
        
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
            
        Raises:
            ValueError: If the resolved path is outside the repo root.

        """
        # Join path and resolve
        resolved = (self.repo_root / relative_path).resolve()
        # Verify it stays within the repo root to prevent directory traversal
        if not resolved.is_relative_to(self.repo_root):
            raise ValueError(f"Path is outside the repository root: {relative_path}")
        return resolved

    def list_files(self, directory: str, extension: str | None = None) -> list[str]:
        """List files in a directory relative to the repository root.
        
        Args:
            directory: The directory path relative to the repo root.
            extension: Optional extension filter (e.g. '.py').
            
        Returns:
            A list of relative file paths.

        """
        dir_path = self._safe_resolve(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        files = []
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = Path(root) / filename
                # Make it relative to the repository root
                rel_path = file_path.relative_to(self.repo_root)

                # Apply extension filter if provided
                if extension:
                    if file_path.suffix == extension or filename.endswith(extension):
                        files.append(str(rel_path))
                else:
                    files.append(str(rel_path))
        return sorted(files)

    def read_file(self, file_path: str) -> str:
        """Read the content of a file. Refuses to read files over 500 lines.
        
        Args:
            file_path: The file path relative or absolute.
            
        Returns:
            The contents of the file.

        """
        resolved_path = self._safe_resolve(file_path)
        if not resolved_path.is_file():
            raise ValueError(f"File not found: {file_path}")

        # Check line count first to respect the safety guard
        with open(resolved_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            if len(lines) > 500:
                raise ValueError(f"File exceeds the limit of 500 lines (contains {len(lines)} lines)")
            return "".join(lines)

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file relative to repository root.
        
        Args:
            file_path: Relative path to the file from repository root.
            content: Content to write to the file.

        """
        resolved_path = self._safe_resolve(file_path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote to {file_path}"

    def update_file(self, file_path: str, target_text: str, replacement_text: str) -> str:
        """Update a file by replacing target_text with replacement_text.
        
        Args:
            file_path: Relative path to the file from repository root.
            target_text: The exact string to search for and replace.
            replacement_text: The string to replace target_text with.

        """
        resolved_path = self._safe_resolve(file_path)
        if not resolved_path.is_file():
            raise ValueError(f"File not found: {file_path}")

        with open(resolved_path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        if target_text not in content:
            raise ValueError(f"Target text not found in {file_path}")

        updated_content = content.replace(target_text, replacement_text)

        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return f"Successfully updated {file_path}"


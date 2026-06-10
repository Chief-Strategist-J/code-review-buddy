import subprocess
from pathlib import Path

class GitService:
    def __init__(self, repo_root: str) -> None:
        """Initialize the GitService with a repository root path.
        
        Args:
            repo_root: The absolute path to the repository root.
        """
        self.repo_root = Path(repo_root).resolve()

    def get_git_diff(self, base_branch: str = "main", compare_branch: str = "HEAD") -> str:
        """Get the git diff between two branches, truncated to ~200 lines if large.
        
        Args:
            base_branch: The base branch to compare from.
            compare_branch: The compare branch to compare to.
            
        Returns:
            The diff output as a string.
        """
        # Validate branch names to prevent command injection
        # Standard branch names can have letters, numbers, slashes, dashes, dots, underscores
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")

        try:
            # Run git diff
            cmd = ["git", "diff", f"{base_branch}..{compare_branch}"]
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.splitlines()
            if len(lines) > 200:
                truncated_info = f"\n... [Diff truncated to 200 lines; total {len(lines)} lines] ..."
                return "\n".join(lines[:200]) + truncated_info
            
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or str(e)
            raise RuntimeError(f"Git diff failed: {error_msg}")

    def get_recent_commits(self, count: int = 5) -> list[dict[str, str]]:
        """Get recent git commits from the repository.
        
        Args:
            count: Number of recent commits to fetch (1-20).
            
        Returns:
            A list of dicts with 'hash' and 'message'.
        """
        if not (1 <= count <= 20):
            raise ValueError("Count must be between 1 and 20")

        try:
            # Run git log
            cmd = ["git", "log", "--oneline", "-n", str(count)]
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                # git log --oneline outputs: <hash> <commit message>
                parts = line.split(" ", 1)
                commit_hash = parts[0]
                commit_message = parts[1] if len(parts) > 1 else ""
                commits.append({
                    "hash": commit_hash,
                    "message": commit_message
                })
            return commits
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or str(e)
            raise RuntimeError(f"Git log failed: {error_msg}")

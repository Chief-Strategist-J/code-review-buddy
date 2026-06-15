import subprocess
from pathlib import Path
from typing import Any


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

    def commit_and_push_file(self, file_path: str, commit_message: str) -> str:
        """Stage, commit, and push a specific file.
        
        Args:
            file_path: The file path relative to repository root.
            commit_message: The commit message.

        """
        resolved_path = (self.repo_root / file_path).resolve()
        if not resolved_path.is_relative_to(self.repo_root):
            raise ValueError(f"Path is outside the repository root: {file_path}")

        git_rel_path = resolved_path.relative_to(self.repo_root)

        if not commit_message or any(c in "\r\n" for c in commit_message):
            raise ValueError("Commit message cannot be empty or contain newlines")

        try:
            # 1. git add
            subprocess.run(
                ["git", "add", str(git_rel_path)],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            # 2. git commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            # 3. git push
            subprocess.run(
                ["git", "push"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            return f"Successfully staged, committed, and pushed {file_path} with message: '{commit_message}'"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or e.stdout.strip() or str(e)
            raise RuntimeError(f"Git operation failed: {error_msg}")

    def get_advanced_diff(self, base_branch: str = "main", compare_branch: str = "HEAD", word_diff: bool = False, unified: int = 3, show_stat: bool = False, file_path: str | None = None) -> str:
        """Show advanced diff between branches with optional word diff, stat, context lines, or targeting a file."""
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")

        cmd = ["git", "diff"]
        if word_diff:
            cmd.append("--word-diff=color")
        if unified != 3:
            cmd.append(f"--unified={unified}")
        if show_stat:
            cmd.append("--stat")
            cmd.append("--patch")
            
        cmd.append(f"{base_branch}...{compare_branch}")
        
        if file_path:
            resolved_path = (self.repo_root / file_path).resolve()
            if not resolved_path.is_relative_to(self.repo_root):
                raise ValueError(f"Path is outside repository root: {file_path}")
            cmd.extend(["--", str(resolved_path.relative_to(self.repo_root))])
            
        try:
            result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            if len(lines) > 500:
                return "\n".join(lines[:500]) + f"\n... [Diff truncated to 500 lines; total {len(lines)} lines] ..."
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git diff failed: {e.stderr.strip() or str(e)}")

    def get_branch_history(self, since: str | None = None, limit: int = 30) -> str:
        """Show visual branch history graph."""
        cmd = ["git", "log", "--oneline", "--graph", "--decorate", "--all"]
        if since:
            cmd.append(f"--since={since}")
        cmd.extend(["-n", str(limit)])
        try:
            result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git log branch history failed: {e.stderr.strip() or str(e)}")

    def get_file_history(self, file_path: str, function_name: str | None = None, search_query: str | None = None, is_regex: bool = False) -> str:
        """Show file commit history, with optional function level history or search query."""
        resolved_path = (self.repo_root / file_path).resolve()
        if not resolved_path.is_relative_to(self.repo_root):
            raise ValueError(f"Path is outside repository root: {file_path}")
        rel_path = str(resolved_path.relative_to(self.repo_root))
        
        cmd = ["git", "log"]
        if function_name:
            cmd.extend([f"-L:{function_name}:{rel_path}", "--no-patch"])
        elif search_query:
            if is_regex:
                cmd.extend(["-G", search_query, "--oneline", "--all"])
            else:
                cmd.extend(["-S", search_query, "--oneline", "--all"])
        else:
            cmd.extend(["-p", "--follow", "--", rel_path])
            
        try:
            result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            if len(lines) > 300:
                return "\n".join(lines[:300]) + f"\n... [Log truncated to 300 lines; total {len(lines)} lines] ..."
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git log file history failed: {e.stderr.strip() or str(e)}")

    def get_file_blame(self, file_path: str, line_range: str | None = None, ignore_whitespace: bool = True) -> str:
        """Show line-by-line git blame information."""
        resolved_path = (self.repo_root / file_path).resolve()
        if not resolved_path.is_relative_to(self.repo_root):
            raise ValueError(f"Path is outside repository root: {file_path}")
        rel_path = str(resolved_path.relative_to(self.repo_root))
        
        cmd = ["git", "blame"]
        if ignore_whitespace:
            cmd.extend(["-w", "-C", "-C", "-C"])
        if line_range:
            cmd.extend(["-L", line_range])
        cmd.append(rel_path)
        
        try:
            result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git blame failed: {e.stderr.strip() or str(e)}")

    def inspect_commit(self, commit_sha: str) -> dict[str, str]:
        """Show metadata, changed files, and full diff patch of a specific commit."""
        if not all(c.isalnum() for c in commit_sha):
            raise ValueError(f"Invalid characters in commit SHA: {commit_sha}")
            
        try:
            res_stat = subprocess.run(["git", "show", "--stat", commit_sha], cwd=self.repo_root, capture_output=True, text=True, check=True)
            res_patch = subprocess.run(["git", "show", "--patch", commit_sha], cwd=self.repo_root, capture_output=True, text=True, check=True)
            
            patch_out = res_patch.stdout
            lines = patch_out.splitlines()
            if len(lines) > 300:
                patch_out = "\n".join(lines[:300]) + f"\n... [Patch truncated to 300 lines; total {len(lines)} lines] ..."
                
            return {
                "stat": res_stat.stdout,
                "patch": patch_out
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git show failed: {e.stderr.strip() or str(e)}")

    def check_merge_safety(self, base_branch: str, feature_branch: str) -> dict[str, Any]:
        """Check if branch can merge cleanly without conflicts, and show commit gap."""
        from typing import Any
        for name, label in [(base_branch, "base_branch"), (feature_branch, "feature_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")
                
        try:
            res_base = subprocess.run(["git", "merge-base", base_branch, feature_branch], cwd=self.repo_root, capture_output=True, text=True, check=True)
            common_ancestor = res_base.stdout.strip()
            
            res_count = subprocess.run(["git", "rev-list", f"{base_branch}..{feature_branch}", "--count"], cwd=self.repo_root, capture_output=True, text=True, check=True)
            commits_ahead = int(res_count.stdout.strip())
            
            try:
                res_tree = subprocess.run(["git", "merge-tree", common_ancestor, base_branch, feature_branch], cwd=self.repo_root, capture_output=True, text=True)
                has_conflicts = "conflict" in res_tree.stdout.lower() or "conflict" in res_tree.stderr.lower()
                conflicts_preview = res_tree.stdout if has_conflicts else ""
            except Exception:
                has_conflicts = False
                conflicts_preview = "Could not perform virtual merge-tree check."
                
            return {
                "common_ancestor": common_ancestor,
                "commits_ahead": commits_ahead,
                "clean_merge": not has_conflicts,
                "conflicts_preview": conflicts_preview[:1000] if conflicts_preview else ""
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git merge-base or rev-list failed: {e.stderr.strip() or str(e)}")

    def get_code_churn(self, limit: int = 15) -> dict[str, Any]:
        """Identify files with highest change frequency (risk factor) and lines added/deleted."""
        from typing import Any
        try:
            res = subprocess.run(["git", "log", "--format=format:", "--name-only"], cwd=self.repo_root, capture_output=True, text=True, check=True)
            files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            
            from collections import Counter
            counts = Counter(files)
            top_churn = [{"file": k, "changes": v} for k, v in counts.most_common(limit)]
            
            res_stats = subprocess.run(["git", "log", "--numstat", "--format="], cwd=self.repo_root, capture_output=True, text=True, check=True)
            added = 0
            deleted = 0
            for line in res_stats.stdout.splitlines():
                parts = line.split()
                if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                    added += int(parts[0])
                    deleted += int(parts[1])
                    
            return {
                "top_churn_files": top_churn,
                "total_lines_added": added,
                "total_lines_deleted": deleted
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git churn logic failed: {e.stderr.strip() or str(e)}")

    def analyze_churn_risk(self, base_branch: str = "main", compare_branch: str = "HEAD", file_path: str | None = None) -> dict[str, Any]:
        """Compute advanced churn risk scores, authorship entropy, or logical couplings."""
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")

        try:
            results: dict[str, Any] = {}
            res = subprocess.run(["git", "log", "--numstat", "--format=commit %H", f"{base_branch}..{compare_branch}"], cwd=self.repo_root, capture_output=True, text=True, check=True)
            
            file_churn: dict[str, int] = {}
            file_commits: dict[str, int] = {}
            current_commit_files: set[str] = set()
            co_changes: dict[frozenset[str], int] = {}
            
            for line in res.stdout.splitlines():
                if line.startswith("commit "):
                    if len(current_commit_files) > 1:
                        lst = sorted(list(current_commit_files))
                        for i in range(len(lst)):
                            for j in range(i+1, len(lst)):
                                pair = frozenset([lst[i], lst[j]])
                                co_changes[pair] = co_changes.get(pair, 0) + 1
                    current_commit_files = set()
                    continue
                parts = line.split()
                if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                    f = parts[2]
                    changes = int(parts[0]) + int(parts[1])
                    file_churn[f] = file_churn.get(f, 0) + changes
                    file_commits[f] = file_commits.get(f, 0) + 1
                    current_commit_files.add(f)

            coupled = [{"files": list(k), "co_changes": v} for k, v in sorted(co_changes.items(), key=lambda x: x[1], reverse=True)[:10]]
            results["logical_couplings"] = coupled
            
            risk_scores = []
            for f in file_churn:
                commits = file_commits[f]
                risk_scores.append({
                    "file": f,
                    "changes": file_churn[f],
                    "commits": commits,
                    "risk_score": file_churn[f] * commits
                })
            results["risk_scores"] = sorted(risk_scores, key=lambda x: x["risk_score"], reverse=True)[:15]
            
            if file_path:
                resolved = (self.repo_root / file_path).resolve()
                if resolved.is_relative_to(self.repo_root):
                    rel = str(resolved.relative_to(self.repo_root))
                    res_authors = subprocess.run(["git", "log", "--format=%ae", "--follow", "--", rel], cwd=self.repo_root, capture_output=True, text=True, check=True)
                    authors = [line.strip() for line in res_authors.stdout.splitlines() if line.strip()]
                    from collections import Counter
                    author_counts = Counter(authors)
                    results["ownership"] = {
                        "file": rel,
                        "unique_authors": len(author_counts),
                        "total_commits": len(authors),
                        "author_contributions": dict(author_counts.most_common(10))
                    }
                    
            return results
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Churn risk analysis failed: {e.stderr.strip() or str(e)}")

    def detect_code_similarity(self, base_branch: str = "main", compare_branch: str = "HEAD", similarity_threshold: int = 50, target_file: str | None = None) -> str:
        """Find copy-pasted code blocks or heavy renames/refactors."""
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")

        cmd = ["git", "diff", f"-C{similarity_threshold}", "--find-copies-harder", f"-M{similarity_threshold}", "--stat"]
        if target_file:
            resolved = (self.repo_root / target_file).resolve()
            if not resolved.is_relative_to(self.repo_root):
                raise ValueError(f"Path outside repository: {target_file}")
            cmd.extend([f"{base_branch}..{compare_branch}", "--", str(resolved.relative_to(self.repo_root))])
        else:
            cmd.append(f"{base_branch}..{compare_branch}")

        try:
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
            return res.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Similarity detection failed: {e.stderr.strip() or str(e)}")

    def get_semantic_diff(self, base_branch: str = "main", compare_branch: str = "HEAD", file_pattern: str = "*") -> dict[str, Any]:
        """Extract API signature changes and cyclomatic complexity proxies from diffs."""
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")

        try:
            res = subprocess.run(["git", "diff", f"{base_branch}..{compare_branch}", "--", file_pattern], cwd=self.repo_root, capture_output=True, text=True, check=True)
            diff_text = res.stdout
            
            added_funcs = []
            removed_funcs = []
            complexity_proxy = 0
            
            for line in diff_text.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    if "func " in line or "def " in line or "class " in line or "interface " in line:
                        added_funcs.append(line[1:].strip())
                    import re
                    if re.search(r"\b(if|for|while|switch|case|except|select)\b", line):
                        complexity_proxy += 1
                elif line.startswith("-") and not line.startswith("---"):
                    if "func " in line or "def " in line or "class " in line or "interface " in line:
                        removed_funcs.append(line[1:].strip())
                        
            return {
                "added_definitions": added_funcs[:50],
                "removed_definitions": removed_funcs[:50],
                "cyclomatic_complexity_proxy_additions": complexity_proxy
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Semantic diff failed: {e.stderr.strip() or str(e)}")

    def query_object_graph(self, action: str, param1: str, param2: str | None = None) -> Any:
        """Query Git's object graph: reachability, ancestry_path, reflog, or blob matching."""
        if not action or not all(c.isalnum() or c == "_" for c in action):
            raise ValueError("Invalid action name")
            
        try:
            if action == "reachability":
                if not param2:
                    raise ValueError("reachability requires param2 (commit Y)")
                res = subprocess.run(["git", "merge-base", "--is-ancestor", param1, param2], cwd=self.repo_root, capture_output=True)
                return {
                    "is_ancestor": res.returncode == 0
                }
            elif action == "ancestry_path":
                if not param2:
                    raise ValueError("ancestry_path requires param2 (commit Y)")
                res = subprocess.run(["git", "rev-list", "--ancestry-path", f"{param1}..{param2}"], cwd=self.repo_root, capture_output=True, text=True, check=True)
                return res.stdout.splitlines()
            elif action == "reflog":
                res = subprocess.run(["git", "reflog", "show", "--format=%H %gd %gs %ci", "-n", "30"], cwd=self.repo_root, capture_output=True, text=True, check=True)
                return res.stdout
            elif action == "blob_find":
                res = subprocess.run(["git", "log", "--all", "--format=%H"], cwd=self.repo_root, capture_output=True, text=True, check=True)
                commits = res.stdout.splitlines()[:50]
                matches = []
                for commit in commits:
                    res_tree = subprocess.run(["git", "ls-tree", "-r", commit], cwd=self.repo_root, capture_output=True, text=True)
                    if param1 in res_tree.stdout:
                        matches.append(commit)
                return matches
            else:
                raise ValueError(f"Unknown action: {action}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Object graph query failed: {e.stderr.strip() or str(e)}")

    def get_diff_with_algorithm(self, base_branch: str = "main", compare_branch: str = "HEAD", algorithm: str = "histogram", pathspecs: list[str] | None = None) -> str:
        """Fetch diff between branches utilizing specific diff algorithms and magic pathspec filters."""
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")
                
        if algorithm not in ["myers", "patience", "histogram", "minimal"]:
            raise ValueError(f"Unknown diff algorithm: {algorithm}")
            
        cmd = ["git", "diff", f"--diff-algorithm={algorithm}", f"{base_branch}...{compare_branch}"]
        if pathspecs:
            cmd.append("--")
            for spec in pathspecs:
                if spec.startswith("-") and not spec.startswith(":!"):
                    raise ValueError(f"Invalid pathspec filter: {spec}")
                cmd.append(spec)
                
        try:
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
            lines = res.stdout.splitlines()
            if len(lines) > 500:
                return "\n".join(lines[:500]) + f"\n... [Diff truncated to 500 lines; total {len(lines)} lines] ..."
            return res.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git diff failed: {e.stderr.strip() or str(e)}")

    def search_repository(self, query: str, search_all: bool = False, file_pattern: str = "*", and_query: str | None = None) -> list[str]:
        """Perform multi-dimensional deep searches inside code repository using git grep."""
        if not query or any(c in "\r\n;" for c in query):
            raise ValueError("Invalid search query pattern")
            
        cmd = ["git", "grep", "-n", "--name-only" if not and_query else "-l", query]
        
        if search_all:
            try:
                res_commits = subprocess.run(["git", "rev-list", "--all", "-n", "30"], cwd=self.repo_root, capture_output=True, text=True, check=True)
                cmd.extend(res_commits.stdout.splitlines())
            except Exception:
                pass
        
        cmd.extend(["--", file_pattern])
        
        try:
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
            output_lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            
            if and_query:
                and_matches = []
                for file_path in output_lines:
                    res_and = subprocess.run(["git", "grep", "-n", and_query, "--", file_path], cwd=self.repo_root, capture_output=True, text=True)
                    if res_and.returncode == 0:
                        and_matches.extend(res_and.stdout.splitlines())
                return and_matches[:50]
                
            return output_lines[:50]
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")

    def run_pr_audit(self, base_branch: str = "main", compare_branch: str = "HEAD", file_pattern: str = "*") -> dict[str, Any]:
        """Run a full, machine-auditable PR pipeline reporting stats, API changes, churn, secrets, and complexity."""
        for name, label in [(base_branch, "base_branch"), (compare_branch, "compare_branch")]:
            if not all(c.isalnum() or c in "-_./@" for c in name):
                raise ValueError(f"Invalid characters in {label}: {name}")
                
        try:
            res_count = subprocess.run(["git", "rev-list", f"{base_branch}..{compare_branch}", "--count", "--no-merges"], cwd=self.repo_root, capture_output=True, text=True, check=True)
            commit_count = int(res_count.stdout.strip())
            
            res_diff = subprocess.run(["git", "diff", f"{base_branch}...{compare_branch}", "--", file_pattern], cwd=self.repo_root, capture_output=True, text=True, check=True)
            diff_text = res_diff.stdout
            
            import re
            secrets = []
            complexity_proxy = 0
            api_additions = []
            
            secret_pattern = re.compile(r"^\+\s*.*(password|secret|token|api_key|private_key)\s*[:=]\s*['\"][^'\"]{6,}", re.IGNORECASE)
            
            for line in diff_text.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    if secret_pattern.search(line):
                        secrets.append(line[1:].strip())
                    if re.search(r"\b(if|for|while|switch|select|except|case)\b", line):
                        complexity_proxy += 1
                    if "func " in line or "def " in line or "class " in line:
                        api_additions.append(line[1:].strip())

            res_churn = subprocess.run(["git", "log", "--name-only", "--format=", f"{base_branch}..{compare_branch}"], cwd=self.repo_root, capture_output=True, text=True, check=True)
            files = [line.strip() for line in res_churn.stdout.splitlines() if line.strip()]
            from collections import Counter
            top_churn = [{"file": k, "changes": v} for k, v in Counter(files).most_common(10)]
            
            return {
                "commit_count": commit_count,
                "api_additions": api_additions[:25],
                "complexity_additions": complexity_proxy,
                "potential_secrets_exposed": secrets[:10],
                "high_churn_files": top_churn
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PR Audit pipeline failed: {e.stderr.strip() or str(e)}")





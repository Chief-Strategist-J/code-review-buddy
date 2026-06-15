from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts on the FastMCP instance.
    
    Args:
        mcp: The FastMCP server instance.

    """

    @mcp.prompt()
    def review_file_prompt(file_path: str, content: str) -> str:
        """Prompt to review the contents of a specific file."""
        return (
            f"Please review the following file: {file_path}\n\n"
            f"Code content:\n"
            f"```\n{content}\n```\n\n"
            f"Provide a thorough code review. Look for bugs, optimization opportunities, "
            f"readability issues, and adherence to clean code standards."
        )

    @mcp.prompt()
    def commit_message_prompt(diff: str) -> str:
        """Prompt to generate a conventional commit message for a git diff."""
        return (
            f"Generate a clear, conventional commit message based on the following git diff:\n\n"
            f"```diff\n{diff}\n```\n\n"
            f"The commit message should have a type (e.g., feat, fix, chore, docs, refactor), "
            f"an optional scope in parentheses, a description, and an optional body if needed."
        )

    @mcp.prompt()
    def create_file_prompt(file_path: str, requirements: str) -> str:
        """Prompt to generate code for a new file with specified requirements."""
        return (
            f"Write the implementation for a new file at `{file_path}` based on these requirements:\n\n"
            f"{requirements}\n\n"
            f"Make sure to output the complete code content ready to be written to the file."
        )

    @mcp.prompt()
    def write_and_commit_prompt(file_path: str, content: str, commit_message: str) -> str:
        """Prompt instructing the agent to write a file and then commit and push it."""
        return (
            f"Please perform the following tasks:\n"
            f"1. Use the `write_file` tool to save this content to `{file_path}`:\n"
            f"```\n{content}\n```\n"
            f"2. Use the `commit_and_push_file` tool to commit `{file_path}` with message '{commit_message}' and push it."
        )

    @mcp.prompt()
    def update_and_commit_prompt(file_path: str, target_text: str, replacement_text: str, commit_message: str) -> str:
        """Prompt instructing the agent to update a file and then commit and push it."""
        return (
            f"Please perform the following tasks:\n"
            f"1. Use the `update_file` tool to replace the target text in `{file_path}`:\n"
            f"Target text:\n`{target_text}`\n"
            f"Replacement text:\n`{replacement_text}`\n"
            f"2. Use the `commit_and_push_file` tool to commit `{file_path}` with message '{commit_message}' and push it."
        )

    @mcp.prompt()
    def advanced_diff_prompt(base_branch: str, compare_branch: str) -> str:
        """Prompt instructing the agent to run and analyze an advanced diff between branches."""
        return (
            f"Please run the `get_advanced_diff` tool comparing `{base_branch}` and `{compare_branch}`.\n"
            f"Make sure to inspect: \n"
            f"1. Overall statistic summaries (e.g., set show_stat=True)\n"
            f"2. Word-level changes for tight code reviews (e.g., set word_diff=True)\n"
            f"Analyze the result for architectural adjustments, design patterns, and potential bugs."
        )

    @mcp.prompt()
    def branch_history_prompt() -> str:
        """Prompt to analyze the visual branch history graph of the repository."""
        return (
            "Please fetch the repository's branch and commit timeline using the `get_branch_history` tool.\n"
            "Examine the topology, recent merges, active development paths, and trace key branch milestones."
        )

    @mcp.prompt()
    def file_history_prompt(file_path: str) -> str:
        """Prompt to perform code archaeology on a specific file's commit history."""
        return (
            f"Please run the `get_file_history` tool for `{file_path}`.\n"
            "Track how this file evolved over time. Look at who modified it, search for target function histories, "
            "and examine previous versions to understand current behaviors."
        )

    @mcp.prompt()
    def file_blame_prompt(file_path: str) -> str:
        """Prompt to run blame on a file to analyze authorship and trace refactor histories."""
        return (
            f"Please run the `get_file_blame` tool for `{file_path}`.\n"
            "Use it to analyze authorship per line range, ignoring mass whitespace refactoring "
            "to trace the true originators of critical algorithms in the code."
        )

    @mcp.prompt()
    def inspect_commit_prompt(commit_sha: str) -> str:
        """Prompt to inspect details of a specific commit SHA."""
        return (
            f"Please run the `inspect_commit` tool for `{commit_sha}`.\n"
            "Review the commit metadata, affected files, line metrics, and exact diff patch to assess quality."
        )

    @mcp.prompt()
    def check_merge_safety_prompt(base_branch: str, feature_branch: str) -> str:
        """Prompt to simulate merge safety checks and conflict resolutions."""
        return (
            f"Please run the `check_merge_safety` tool comparing `{base_branch}` and `{feature_branch}`.\n"
            "Inspect if they are cleanly mergeable, review conflict locations, and estimate the sync gap."
        )

    @mcp.prompt()
    def analyze_churn_risk_prompt(base_branch: str, compare_branch: str) -> str:
        """Prompt to analyze code churn risk, ownership entropy, and logical couplings."""
        return (
            f"Please run the `analyze_churn_risk` tool comparing `{base_branch}` and `{compare_branch}`.\n"
            "Examine top-risk churn files, logical coupling pairs (files changing together), "
            "and identify files with diffuse authorship ownership (diffuse entropy)."
        )

    @mcp.prompt()
    def detect_code_similarity_prompt(base_branch: str, compare_branch: str) -> str:
        """Prompt to look for copy-pasted blocks and rename actions across branches."""
        return (
            f"Please run the `detect_code_similarity` tool comparing `{base_branch}` and `{compare_branch}`.\n"
            "Find code duplicates, copy-paste patterns, and renamed files to identify opportunities for DRY refactoring."
        )

    @mcp.prompt()
    def get_semantic_diff_prompt(base_branch: str, compare_branch: str) -> str:
        """Prompt to check semantic diffs: API signature updates and complexity metrics."""
        return (
            f"Please run the `get_semantic_diff` tool comparing `{base_branch}` and `{compare_branch}`.\n"
            "Identify breaking changes (removed exports), API signature additions, and evaluate cyclomatic complexity indices."
        )

    @mcp.prompt()
    def query_object_graph_prompt(action: str, param1: str) -> str:
        """Prompt to query the lower-level Git object graph or reflogs."""
        return (
            f"Please run the `query_object_graph` tool with action=`{action}` and param1=`{param1}`.\n"
            "Analyze the graph topology, reachability, dangling references, or reflog timelines."
        )

    @mcp.prompt()
    def get_diff_with_algorithm_prompt(base_branch: str, compare_branch: str, algorithm: str) -> str:
        """Prompt instructing the agent to run a diff with specific algorithms (histogram, patience, etc.)."""
        return (
            f"Please run the `get_diff_with_algorithm` tool comparing `{base_branch}` and `{compare_branch}` with the `{algorithm}` algorithm.\n"
            "Analyze the diff output for clean patches, readability, and structural modifications."
        )

    @mcp.prompt()
    def search_repository_prompt(query: str) -> str:
        """Prompt to search the repository for patterns or variables."""
        return (
            f"Please search the repository using the `search_repository` tool for query `{query}`.\n"
            "Examine matching files, search query contexts, and find references in code files."
        )

    @mcp.prompt()
    def run_pr_audit_prompt(base_branch: str, compare_branch: str) -> str:
        """Prompt instructing the agent to execute the full automated PR audit report."""
        return (
            f"Please run the `run_pr_audit` tool comparing `{base_branch}` and `{compare_branch}`.\n"
            "Examine the audit report detailing commit counts, added APIs, code churn hotspots, "
            "complexity additions, and check for potential secret leaks."
        )




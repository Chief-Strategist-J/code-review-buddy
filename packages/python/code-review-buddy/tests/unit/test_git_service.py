import pytest
from src.features.git.service import GitService

def test_git_service_branch_validation() -> None:
    service = GitService("/tmp")
    with pytest.raises(ValueError, match="Invalid characters in base_branch"):
        service.get_git_diff("main; rm -rf /", "HEAD")

def test_git_service_commits_validation() -> None:
    service = GitService("/tmp")
    with pytest.raises(ValueError, match="Count must be between 1 and 20"):
        service.get_recent_commits(0)
    with pytest.raises(ValueError, match="Count must be between 1 and 20"):
        service.get_recent_commits(21)

import pytest
from pathlib import Path
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

def test_commit_and_push_file_validation() -> None:
    service = GitService("/tmp")
    with pytest.raises(ValueError, match="Path is outside the repository root"):
        service.commit_and_push_file("../outside.txt", "message")
        
    with pytest.raises(ValueError, match="Commit message cannot be empty or contain newlines"):
        service.commit_and_push_file("some.txt", "message\nwith newline")

def test_commit_and_push_file_execution(tmp_path: Path) -> None:
    from unittest.mock import patch
    service = GitService(str(tmp_path))
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        res = service.commit_and_push_file("test_file.txt", "Commit message")
        assert "Successfully staged, committed, and pushed" in res
        assert mock_run.call_count == 3

def test_advanced_git_methods(tmp_path: Path) -> None:
    from unittest.mock import patch
    service = GitService(str(tmp_path))
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "dummy output"
        
        res_diff = service.get_advanced_diff(base_branch="main", compare_branch="HEAD", word_diff=True, unified=5, show_stat=True)
        assert res_diff == "dummy output"
        
        res_history = service.get_branch_history(limit=5)
        assert res_history == "dummy output"
        
        res_file_hist = service.get_file_history("test.txt", search_query="pattern")
        assert res_file_hist == "dummy output"
        
        res_blame = service.get_file_blame("test.txt", line_range="1,10")
        assert res_blame == "dummy output"
        
        res_inspect = service.inspect_commit("abc1234")
        assert isinstance(res_inspect, dict)
        assert "stat" in res_inspect
        assert "patch" in res_inspect

def test_git_analysis_engine_methods(tmp_path: Path) -> None:
    from unittest.mock import patch
    service = GitService(str(tmp_path))
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "dummy output"
        
        # Test detect_code_similarity
        res_sim = service.detect_code_similarity(similarity_threshold=60)
        assert res_sim == "dummy output"
        
        # Test get_semantic_diff
        res_sem = service.get_semantic_diff()
        assert isinstance(res_sem, dict)
        assert "added_definitions" in res_sem
        
        # Test query_object_graph
        res_graph = service.query_object_graph("reachability", "commit1", "commit2")
        assert isinstance(res_graph, dict)
        assert "is_ancestor" in res_graph




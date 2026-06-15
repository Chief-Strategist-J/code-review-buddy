import pytest
from pathlib import Path
from src.features.fs.service import FileSystemService

def test_list_files_invalid_dir(tmp_path: Path) -> None:
    service = FileSystemService(str(tmp_path))
    with pytest.raises(ValueError, match="Not a directory"):
        service.list_files("nonexistent_dir")

def test_list_files_filtering(tmp_path: Path) -> None:
    # Create temp files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.txt").write_text("some text")
    
    service = FileSystemService(str(tmp_path))
    files = service.list_files("src")
    assert "src/main.py" in files
    assert "src/utils.txt" in files
    
    python_files = service.list_files("src", extension=".py")
    assert "src/main.py" in python_files
    assert "src/utils.txt" not in python_files

def test_read_file_limit(tmp_path: Path) -> None:
    large_file = tmp_path / "large.txt"
    large_file.write_text("\n" * 501)
    
    service = FileSystemService(str(tmp_path))
    with pytest.raises(ValueError, match="File exceeds the limit of 500 lines"):
        service.read_file("large.txt")

def test_safe_resolve_traversal(tmp_path: Path) -> None:
    service = FileSystemService(str(tmp_path))
    with pytest.raises(ValueError, match="Path is outside the repository root"):
        service._safe_resolve("../outside.txt")

def test_write_and_update_file(tmp_path: Path) -> None:
    service = FileSystemService(str(tmp_path))
    res = service.write_file("new_dir/test.txt", "hello world")
    assert res == "Successfully wrote to new_dir/test.txt"
    assert (tmp_path / "new_dir" / "test.txt").read_text() == "hello world"

    res_up = service.update_file("new_dir/test.txt", "world", "buddy")
    assert res_up == "Successfully updated new_dir/test.txt"
    assert (tmp_path / "new_dir" / "test.txt").read_text() == "hello buddy"

    with pytest.raises(ValueError, match="Target text not found"):
        service.update_file("new_dir/test.txt", "missing", "new")


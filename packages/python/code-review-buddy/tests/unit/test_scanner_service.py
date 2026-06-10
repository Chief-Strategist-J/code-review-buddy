import pytest
from pathlib import Path
from src.features.scanner.service import ScannerService

def test_scan_todos(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    code = """
    # TODO: fix this bug
    # FIXME: critical issue here
    # HACK: temporary workaround
    # XXX: look at this
    print("hello")
    """
    (tmp_path / "src" / "app.py").write_text(code)
    
    service = ScannerService(str(tmp_path))
    todos = service.scan_todos("src")
    
    assert len(todos) == 4
    markers = [t["text"] for t in todos]
    assert any("TODO" in m for m in markers)
    assert any("FIXME" in m for m in markers)
    assert any("HACK" in m for m in markers)
    assert any("XXX" in m for m in markers)

def test_find_large_functions(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    # Create a 45 line python function
    func_lines = ["def large_func():"] + [f"    print({i})" for i in range(43)]
    (tmp_path / "src" / "large.py").write_text("\n".join(func_lines))
    
    service = ScannerService(str(tmp_path))
    large_funcs = service.find_large_functions("src/large.py")
    
    assert len(large_funcs) == 1
    assert large_funcs[0]["function"] == "large_func"
    assert large_funcs[0]["line_count"] == 44

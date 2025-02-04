from pathlib import Path
from typing import Optional


class SourceCodeFile:
    def __init__(self, path: Path, module: Optional[Path], dependency_depth: int):
        assert path.is_absolute()
        assert module is None or module.is_absolute()
        assert dependency_depth is None or dependency_depth >= 0

        self.path = path
        self.module = module
        self.dependency_depth = dependency_depth
        self.is_test_file = SourceCodeFile._is_test_file(path)

    @classmethod
    def _is_test_file(cls, path: Path) -> bool:
        is_in_tests_folder = any(part in ["test", "tests"] for part in path.parts)
        return path.suffix == ".rs" and is_in_tests_folder

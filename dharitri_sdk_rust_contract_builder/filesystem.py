import logging
from pathlib import Path
from typing import Callable, List, Union

from dharitri_sdk_rust_contract_builder.errors import ErrKnown


def get_all_files(folder: Path, should_include_file: Union[Callable[[Path], bool], None] = None):
    should_include_file = should_include_file or (lambda _: True)
    paths = list(folder.rglob("*"))
    paths = [path for path in paths if path.is_file() and should_include_file(path)]
    return paths


def find_files_in_folder(folder: Path, pattern: str) -> List[Path]:
    files = list(folder.rglob(pattern))

    if len(files) == 0:
        raise ErrKnown(f"No file matches pattern [{pattern}] in folder {folder}")

    return sorted([Path(file).resolve() for file in files])


def find_file_in_folder(folder: Path, pattern: str) -> Path:
    files = sorted(list(folder.rglob(pattern)))

    if len(files) == 0:
        raise ErrKnown(f"No file matches pattern [{pattern}] in folder {folder}")
    if len(files) > 1:
        logging.warning(f"More files match pattern [{pattern}] in folder {folder}. Will pick first:\n{files}")

    file = folder / files[0]
    return Path(file).resolve()

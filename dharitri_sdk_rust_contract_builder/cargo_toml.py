from pathlib import Path
from typing import List, Tuple

import toml

from dharitri_sdk_rust_contract_builder.errors import ErrKnown


class CargoLockFile:
    def __init__(self, path: Path, content: str):
        self.path = path
        self.content = content


def get_contract_name_and_version(contract_folder: Path) -> Tuple[str, str]:
    file = contract_folder / "Cargo.toml"
    data = toml.loads(file.read_text())

    name = data["package"]["name"]
    version = data["package"]["version"]
    return name, version


def gather_cargo_lock_files(folder: Path) -> List[CargoLockFile]:
    paths = sorted(list(folder.glob("**/Cargo.lock")))
    files: List[CargoLockFile] = []

    for path in paths:
        content = path.read_text()
        files.append(CargoLockFile(path, content))

    return files


def ensure_no_change_within_cargo_lock_files(files_before_build: List[CargoLockFile], files_after_build: List[CargoLockFile]):
    """
    Ensure there are no changes within Cargo.lock files during build.

    Even if "--locked" is passed to "cargo build", it's still possible that Cargo.lock files are created (think of the Cargo.lock at the workspace level).
    """

    paths_before_build = [file.path for file in files_before_build]
    paths_after_build = [file.path for file in files_after_build]
    new_paths = list(set(paths_after_build) - set(paths_before_build))
    new_paths_strings = [str(path) for path in new_paths]
    removed_paths = list(set(paths_before_build) - set(paths_after_build))
    removed_paths_strings = [str(path) for path in removed_paths]

    if new_paths:
        raise ErrKnown(f"Cargo.lock file(s) have been created during build: {new_paths_strings}")

    if removed_paths:
        raise ErrKnown(f"Cargo.lock file(s) have been removed during build: {removed_paths_strings}")

    changed_paths: List[Path] = []

    for before, after in zip(files_before_build, files_after_build):
        if before.content != after.content:
            changed_paths.append(before.path)

    changed_paths_strings = [str(path) for path in changed_paths]

    if changed_paths:
        raise ErrKnown(f"Cargo.lock file(s) have changed during build: {changed_paths_strings}")

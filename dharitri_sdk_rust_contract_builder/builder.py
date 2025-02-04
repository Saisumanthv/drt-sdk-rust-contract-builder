import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Set

from dharitri_sdk_rust_contract_builder import source_code
from dharitri_sdk_rust_contract_builder.build_metadata import BuildMetadata
from dharitri_sdk_rust_contract_builder.build_options import BuildOptions
from dharitri_sdk_rust_contract_builder.build_outcome import BuildOutcome
from dharitri_sdk_rust_contract_builder.cargo_toml import (
    ensure_no_change_within_cargo_lock_files, gather_cargo_lock_files,
    get_contract_name_and_version)
from dharitri_sdk_rust_contract_builder.codehash import \
    generate_code_hash_artifact
from dharitri_sdk_rust_contract_builder.constants import (
    CONTRACT_CONFIG_FILENAME, MAX_PACKAGED_SOURCE_CODE_SIZE)
from dharitri_sdk_rust_contract_builder.errors import ErrKnown
from dharitri_sdk_rust_contract_builder.filesystem import \
    find_files_in_folder
from dharitri_sdk_rust_contract_builder.packaged_source_code import (
    PackagedSourceCode, PackagedSourceMetadata)


def build_project(
    project_folder: Path,
    parent_output_folder: Path,
    metadata: BuildMetadata,
    options: BuildOptions
) -> BuildOutcome:
    project_folder = project_folder.expanduser().resolve()
    parent_output_folder = parent_output_folder.expanduser().resolve()
    cargo_target_dir = options.cargo_target_dir.expanduser().resolve()
    no_wasm_opt = options.no_wasm_opt
    specific_contract = options.specific_contract
    build_root_folder = options.build_root_folder.expanduser().resolve()

    ensure_output_folder_is_empty(parent_output_folder)

    outcome = BuildOutcome(metadata, options)
    contracts_folders = get_contracts_folders(project_folder)
    ensure_distinct_contract_names(contracts_folders)

    # We copy the whole project folder to the build path, to ensure that all local dependencies are available.
    project_within_build_folder = copy_project_folder_to_build_folder(project_folder, build_root_folder)

    cargo_lock_files_before_build = gather_cargo_lock_files(project_within_build_folder)

    for contract_folder in sorted(contracts_folders):
        contract_name, contract_version = get_contract_name_and_version(contract_folder)
        logging.info(f"Contract = {contract_name}, version = {contract_version}")

        if specific_contract and contract_name != specific_contract:
            logging.info(f"Skipping {contract_name}.")
            continue

        output_subfolder = parent_output_folder / f"{contract_name}"
        output_subfolder.mkdir(parents=True, exist_ok=True)

        relative_contract_folder = contract_folder.relative_to(project_folder)
        contract_build_subfolder = project_within_build_folder / relative_contract_folder

        # Clean folder - it may contain externally-generated build artifacts
        clean_contract(contract_build_subfolder)
        build_contract(contract_build_subfolder, output_subfolder, cargo_target_dir, no_wasm_opt)

        # We do not clean the "output" folder, since it will be included in one of the generated archives.
        clean_contract(contract_build_subfolder, clean_output=False)

        # We create the source code bundle (packaged source code) - could have been created before the build, as well.
        create_packaged_source_code(
            parent_project_folder=project_within_build_folder,
            contract_folder=contract_build_subfolder,
            output_folder=output_subfolder,
            build_metadata=metadata.to_dict(),
            build_options=options.to_dict(),
            package_filename=f"{contract_name}-{contract_version}.source.json"
        )

        outcome.gather_artifacts(contract_build_subfolder, output_subfolder)

    cargo_lock_files_after_build = gather_cargo_lock_files(project_within_build_folder)

    ensure_no_change_within_cargo_lock_files(
        files_before_build=cargo_lock_files_before_build,
        files_after_build=cargo_lock_files_after_build
    )

    return outcome


def ensure_output_folder_is_empty(parent_output_folder: Path):
    is_empty = len(os.listdir(parent_output_folder)) == 0
    if not is_empty:
        raise ErrKnown(f"Output folder must be empty: {parent_output_folder}")


def get_contracts_folders(project_path: Path) -> List[Path]:
    marker_files = list(project_path.glob(f"**/{CONTRACT_CONFIG_FILENAME}"))
    folders = [marker_file.parent for marker_file in marker_files]
    return sorted(set(folders))


def ensure_distinct_contract_names(contracts_folders: List[Path]):
    names: Set[str] = set()

    for folder in sorted(contracts_folders):
        name, _ = get_contract_name_and_version(folder)
        if name in names:
            raise Exception(f"""Name "{name}" already associated to another contract.""")

        names.add(name)


def copy_project_folder_to_build_folder(project_folder: Path, build_root_folder: Path):
    shutil.rmtree(build_root_folder, ignore_errors=True)
    build_root_folder.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        project_folder, build_root_folder,
        dirs_exist_ok=True, symlinks=True, ignore_dangling_symlinks=True
    )

    return build_root_folder


def clean_contract(folder: Path, clean_output: bool = True):
    logging.info(f"Cleaning: {folder}")

    # On a best-effort basis, remove folders that (usually) hold build artifacts
    shutil.rmtree(folder / "wasm" / "target", ignore_errors=True)
    shutil.rmtree(folder / "meta" / "target", ignore_errors=True)

    if clean_output:
        shutil.rmtree(folder / "output", ignore_errors=True)


def build_contract(build_folder: Path, output_folder: Path, cargo_target_dir: Path, no_wasm_opt: bool):
    cargo_output_folder = build_folder / "output"
    meta_folder = build_folder / "meta"

    args = ["cargo", "run", "build"]
    args.extend(["--target-dir", str(cargo_target_dir)])
    args.extend(["--no-wasm-opt"] if no_wasm_opt else [])

    # If the lock file is missing, or it needs to be updated, Cargo will exit with an error.
    # See: https://doc.rust-lang.org/cargo/commands/cargo-build.html
    args.append("--locked")

    custom_env = os.environ.copy()
    # Cargo will use the git executable to fetch registry indexes and git dependencies.
    #  - https://doc.rust-lang.org/cargo/reference/config.html
    # This is required to avoid high memory usage when fetching dependencies.
    # - https://github.com/rust-lang/cargo/issues/10583
    custom_env["CARGO_NET_GIT_FETCH_WITH_CLI"] = "true"

    logging.info(f"Building: {args}")
    return_code = subprocess.run(args, cwd=meta_folder, env=custom_env).returncode
    if return_code != 0:
        raise ErrKnown(f"Failed to build contract {build_folder}. Return code: {return_code}.")

    # One or more WASM files should have been generated.
    wasm_files = find_files_in_folder(cargo_output_folder, "*.wasm")
    for wasm_file in wasm_files:
        generate_code_hash_artifact(wasm_file)

    shutil.copytree(cargo_output_folder, output_folder, dirs_exist_ok=True)


def create_packaged_source_code(
        parent_project_folder: Path,
        contract_folder: Path,
        output_folder: Path,
        build_metadata: Dict[str, Any],
        build_options: Dict[str, Any],
        package_filename: str
):
    source_code_files = source_code.get_source_code_files(
        project_folder=parent_project_folder,
        contract_folder=contract_folder,
    )

    contract_name, contract_version = get_contract_name_and_version(contract_folder)
    metadata = PackagedSourceMetadata(
        contract_name=contract_name,
        contract_version=contract_version,
        build_metadata=build_metadata,
        build_options=build_options,
    )

    package = PackagedSourceCode.from_filesystem(metadata, parent_project_folder, source_code_files)
    package_path = output_folder / package_filename
    package.save_to_file(package_path)

    size_of_file = package_path.stat().st_size
    if size_of_file > MAX_PACKAGED_SOURCE_CODE_SIZE:
        warn_file_too_large(package_path, size_of_file, MAX_PACKAGED_SOURCE_CODE_SIZE)


def warn_file_too_large(path: Path, size: int, max_size: int):
    logging.warning(f"""File is too large (this might cause issues with using downstream applications, such as the contract build verification services):
file = {path}, size = {size}, maximum size = {max_size}""")

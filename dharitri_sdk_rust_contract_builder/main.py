import logging
import os
import shutil
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from dharitri_sdk_rust_contract_builder import builder
from dharitri_sdk_rust_contract_builder.build_metadata import BuildMetadata
from dharitri_sdk_rust_contract_builder.build_options import BuildOptions
from dharitri_sdk_rust_contract_builder.constants import (
    DEFAULT_BUILD_ROOT, HARDCODED_UNWRAP_FOLDER)
from dharitri_sdk_rust_contract_builder.errors import ErrKnown
from dharitri_sdk_rust_contract_builder.packaged_source_code import \
    PackagedSourceCode


def main(cli_args: List[str]):
    logging.basicConfig(level=logging.DEBUG)

    start_time = time.time()

    parser = ArgumentParser()
    parser.add_argument("--project", type=str, required=False, help="source code folder (project)")
    parser.add_argument("--package-whole-project-src", action="store_true", default=False, help="deprecated parameter, not used anymore")
    parser.add_argument("--packaged-src", type=str, required=False, help="source code packaged in a JSON file")
    parser.add_argument("--contract", type=str, required=False, help="contract to build (contract name, as found in Cargo.toml)")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--no-wasm-opt", action="store_true", default=False, help="do not optimize wasm files after the build (default: %(default)s)")
    parser.add_argument("--cargo-target-dir", type=str, required=True, help="Cargo's target-dir")
    parser.add_argument("--build-root", type=str, default=DEFAULT_BUILD_ROOT, required=False, help="root path (within container) for the build (default: %(default)s)")

    parsed_args = parser.parse_args(cli_args)
    project_path = Path(parsed_args.project).expanduser().resolve() if parsed_args.project else None
    packaged_src_path = Path(parsed_args.packaged_src).expanduser().resolve() if parsed_args.packaged_src else None
    parent_output_folder = Path(parsed_args.output)
    specific_contract = parsed_args.contract
    cargo_target_dir = Path(parsed_args.cargo_target_dir)
    no_wasm_opt = parsed_args.no_wasm_opt
    build_root = Path(parsed_args.build_root)

    if not project_path:
        if not packaged_src_path:
            raise ErrKnown("One of the following must be provided: --project, --packaged-src")

        # We have to unwrap the packaged source code (JSON)
        project_path = HARDCODED_UNWRAP_FOLDER
        shutil.rmtree(HARDCODED_UNWRAP_FOLDER, ignore_errors=True)
        packaged = PackagedSourceCode.from_file(packaged_src_path)
        packaged.unwrap_to_filesystem(HARDCODED_UNWRAP_FOLDER)
        build_root = Path(packaged.metadata.build_options.get("buildRootFolder", build_root))

    metadata = BuildMetadata.from_env()

    options = BuildOptions(
        specific_contract=specific_contract,
        cargo_target_dir=cargo_target_dir,
        no_wasm_opt=no_wasm_opt,
        build_root_folder=build_root,
    )

    outcome = builder.build_project(
        project_path,
        parent_output_folder,
        metadata,
        options,
    )

    outcome.save_to_file(parent_output_folder / "artifacts.json")

    end_time = time.time()
    time_elapsed = end_time - start_time
    logging.info(f"Built in {time_elapsed} seconds, as user = {os.getuid()}, group = {os.getgid()}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ErrKnown as err:
        print("An error occurred.")
        print(err)
        exit(1)

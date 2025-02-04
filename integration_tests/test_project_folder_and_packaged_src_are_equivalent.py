import shutil
import sys
from pathlib import Path
from typing import List

from integration_tests.config import PARENT_OUTPUT_FOLDER
from integration_tests.shared import download_project_repository, run_docker


def main(cli_args: List[str]):
    repository_url = "https://github.com/TerraDharitri/drt-sc-sovereign"
    commit = "80599388b9358842b50ea216a622d514e15df374"
    archve_subfolder = f"drt-sc-sovereign-{commit}"
    project_path = download_project_repository(f"{repository_url}/archive/{commit}.zip", archve_subfolder)
    project_path = project_path / archve_subfolder

    check_project_folder_and_packaged_src_are_equivalent(
        project_path=project_path,
        parent_output_folder=PARENT_OUTPUT_FOLDER,
        contracts=["dcdt-safe", "fee-market"],
    )


def check_project_folder_and_packaged_src_are_equivalent(
        project_path: Path,
        parent_output_folder: Path,
        contracts: List[str]):
    for contract in contracts:
        output_using_project = parent_output_folder / "using-project" / contract
        output_using_packaged_src = parent_output_folder / "using-packaged-src" / contract

        shutil.rmtree(output_using_project, ignore_errors=True)
        shutil.rmtree(output_using_packaged_src, ignore_errors=True)

        output_using_project.mkdir(parents=True, exist_ok=True)
        output_using_packaged_src.mkdir(parents=True, exist_ok=True)

        (code, _, _) = run_docker(
            project_path=project_path,
            packaged_src_path=None,
            contract_name=contract,
            image="sdk-rust-contract-builder:next",
            output_folder=output_using_project
        )

        assert code == 0

        packaged_src_path = next((output_using_project / contract).glob("*.source.json"))

        (code, _, _) = run_docker(
            project_path=None,
            packaged_src_path=packaged_src_path,
            contract_name=contract,
            image="sdk-rust-contract-builder:next",
            output_folder=output_using_packaged_src
        )

        assert code == 0

        # Check that output folders are identical
        using_project_output_files = sorted((output_using_project / contract).rglob("*"))
        using_packaged_src_output_files = sorted((output_using_packaged_src / contract).rglob("*"))

        assert len(using_project_output_files) == len(using_packaged_src_output_files)

        for index, file_using_project in enumerate(using_project_output_files):
            file_using_packaged_src = using_packaged_src_output_files[index]

            if not file_using_project.is_file() or file_using_project.suffix == ".zip":
                continue
            file_content_using_project = file_using_project.read_bytes()
            file_content_using_packaged_src = file_using_packaged_src.read_bytes()

            if file_content_using_project == file_content_using_packaged_src:
                print(f"Files are identical ({contract}): {file_using_project.name}")
            else:
                print(f"Files differ ({contract}):")
                print(f"  {file_using_project}")
                print(f"  {file_using_packaged_src}")
                raise Exception(f"Files differ ({contract}): {file_using_project.name}")


if __name__ == "__main__":
    main(sys.argv[1:])

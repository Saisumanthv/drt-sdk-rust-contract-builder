import os
import shutil

from integration_tests.config import PARENT_OUTPUT_FOLDER
from integration_tests.shared import download_project_repository, run_docker
from dharitri_sdk_rust_contract_builder.packaged_source_code import \
    PackagedSourceCode

DEFAULT_PROJECT_ARCHIVE_URL = "https://github.com/TerraDharitri/drt-sc-sovereign/archive/80599388b9358842b50ea216a622d514e15df374.zip"
DEFAULT_PROJECT_ARCHIVE_PAYLOAD = "drt-sc-sovereign-80599388b9358842b50ea216a622d514e15df374"
DEFAULT_CONTRACT_NAME = "dcdt-safe"


def test_with_symlinks():
    workspace_parent = download_project_repository(DEFAULT_PROJECT_ARCHIVE_URL, "test_with_symlinks")
    workspace = workspace_parent / DEFAULT_PROJECT_ARCHIVE_PAYLOAD

    output_folder = PARENT_OUTPUT_FOLDER / "test_with_symlinks"
    shutil.rmtree(output_folder, ignore_errors=True)
    output_folder.mkdir(parents=True, exist_ok=True)

    # In the workspace, create a symlink towards something outside it:
    dummy_file = workspace_parent / "dummy"
    dummy_file.write_text("dummy")
    os.symlink(dummy_file, workspace / "dummy")

    # But also a symlink towards something inside the workspace:
    os.symlink(workspace / ".github", workspace / "github_symlink", target_is_directory=True)

    # Symlinks should be ignored, and the build should succeed.
    (code, _, _) = run_docker(
        project_path=workspace,
        packaged_src_path=None,
        contract_name=DEFAULT_CONTRACT_NAME,
        image="sdk-rust-contract-builder:next",
        output_folder=output_folder
    )

    assert code == 0
    assert (output_folder / "artifacts.json").exists()


def test_has_correct_packaged_source():
    workspace_parent = download_project_repository(DEFAULT_PROJECT_ARCHIVE_URL, "test_has_correct_packaged_source")
    workspace = workspace_parent / DEFAULT_PROJECT_ARCHIVE_PAYLOAD

    output_folder = PARENT_OUTPUT_FOLDER / "test_has_correct_packaged_source"
    shutil.rmtree(output_folder, ignore_errors=True)
    output_folder.mkdir(parents=True, exist_ok=True)

    (code, _, _) = run_docker(
        project_path=workspace,
        packaged_src_path=None,
        contract_name=DEFAULT_CONTRACT_NAME,
        image="sdk-rust-contract-builder:next",
        output_folder=output_folder
    )

    assert code == 0

    packaged_source_code = PackagedSourceCode.from_file(output_folder / DEFAULT_CONTRACT_NAME / f"{DEFAULT_CONTRACT_NAME}-0.0.0.source.json")

    for entry in packaged_source_code.entries:
        assert not str(entry.path).startswith("target"), f"Unexpected file: {entry.path}"
        assert entry.is_test_file == ("test" in str(entry.path)), f"Unexpected is_test_file marker for: {entry.path}"


def test_fail_if_contract_cargo_lock_is_missing():
    workspace_parent = download_project_repository(DEFAULT_PROJECT_ARCHIVE_URL, "test_fail_if_contract_cargo_lock_is_missing")
    workspace = workspace_parent / DEFAULT_PROJECT_ARCHIVE_PAYLOAD

    output_folder = PARENT_OUTPUT_FOLDER / "test_fail_if_contract_cargo_lock_is_missing"
    shutil.rmtree(output_folder, ignore_errors=True)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Remove a (required) Cargo.lock file
    (workspace / DEFAULT_CONTRACT_NAME / "wasm" / "Cargo.lock").unlink()

    (code, _, stderr) = run_docker(
        project_path=workspace,
        packaged_src_path=None,
        contract_name=DEFAULT_CONTRACT_NAME,
        image="sdk-rust-contract-builder:next",
        output_folder=output_folder
    )

    assert code != 0
    assert "Cargo.lock needs to be updated but --locked was passed to prevent this" in stderr


def test_fail_if_workspace_cargo_lock_is_missing():
    workspace_parent = download_project_repository(DEFAULT_PROJECT_ARCHIVE_URL, "test_fail_if_workspace_cargo_lock_is_missing")
    workspace = workspace_parent / DEFAULT_PROJECT_ARCHIVE_PAYLOAD

    output_folder = PARENT_OUTPUT_FOLDER / "test_fail_if_workspace_cargo_lock_is_missing"
    shutil.rmtree(output_folder, ignore_errors=True)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Remove a (required) Cargo.lock file
    (workspace / "Cargo.lock").unlink()

    (code, stdout, _) = run_docker(
        project_path=workspace,
        packaged_src_path=None,
        contract_name=DEFAULT_CONTRACT_NAME,
        image="sdk-rust-contract-builder:next",
        output_folder=output_folder
    )

    assert code != 0
    assert "Cargo.lock file(s) have been created during build: ['/tmp/project/Cargo.lock']" in stdout

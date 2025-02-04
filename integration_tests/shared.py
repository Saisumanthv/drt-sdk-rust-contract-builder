import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

from integration_tests.config import (CARGO_TARGET_DIR, DOWNLOADS_FOLDER,
                                      EXTRACTED_FOLDER, RUST_GIT,
                                      RUST_REGISTRY, RUST_TMP)


def download_project_repository(zip_archive_url: str, name: str) -> Path:
    DOWNLOADS_FOLDER.mkdir(parents=True, exist_ok=True)
    EXTRACTED_FOLDER.mkdir(parents=True, exist_ok=True)

    download_to_path = DOWNLOADS_FOLDER / f"{name}.zip"
    extract_to_path = EXTRACTED_FOLDER / name

    urllib.request.urlretrieve(zip_archive_url, download_to_path)
    shutil.rmtree(extract_to_path, ignore_errors=True)
    shutil.unpack_archive(download_to_path, extract_to_path)
    return extract_to_path


def download_packaged_src(json_url: str, name: str) -> Path:
    downloaded_packaged_src = DOWNLOADS_FOLDER / f"{name}.source.json"
    urllib.request.urlretrieve(json_url, downloaded_packaged_src)
    return downloaded_packaged_src


def run_docker(
    project_path: Optional[Path],
    packaged_src_path: Optional[Path],
    contract_name: Optional[str],
    image: str,
    output_folder: Path,
) -> Tuple[int, str, str]:
    print(f"""Running docker...
    project_path: {project_path},
    packaged_src_path: {packaged_src_path},
    contract_name: {contract_name},
    image: {image},
    output_folder: {output_folder}
""")

    CARGO_TARGET_DIR.mkdir(parents=True, exist_ok=True)
    RUST_REGISTRY.mkdir(parents=True, exist_ok=True)
    RUST_GIT.mkdir(parents=True, exist_ok=True)
    RUST_TMP.mkdir(parents=True, exist_ok=True)

    docker_mount_args: List[str] = ["--volume", f"{output_folder}:/output"]

    if project_path:
        docker_mount_args.extend(["--volume", f"{project_path}:/project"])

    if packaged_src_path:
        docker_mount_args.extend(["--volume", f"{packaged_src_path}:/packaged-src.json"])

    docker_mount_args += ["--volume", f"{CARGO_TARGET_DIR}:/rust/cargo-target-dir"]
    docker_mount_args += ["--volume", f"{RUST_REGISTRY}:/rust/registry"]
    docker_mount_args += ["--volume", f"{RUST_GIT}:/rust/git"]
    docker_mount_args += ["--volume", f"{RUST_TMP}:/rust/tmp"]
    docker_mount_args += ["--network", "host"]

    docker_args = ["docker", "run"]
    docker_args += docker_mount_args
    docker_args += ["--user", f"{str(os.getuid())}:{str(os.getgid())}"]
    docker_args += ["--rm", image]

    entrypoint_args: List[str] = []

    if project_path:
        entrypoint_args.extend(["--project", "project"])

    if packaged_src_path:
        entrypoint_args.extend(["--packaged-src", "packaged-src.json"])

    if contract_name:
        entrypoint_args.extend(["--contract", contract_name])

    args = docker_args + entrypoint_args

    result = subprocess.run(
        args,
        capture_output=True,
        text=True
    )

    print("# command:")
    print(" ".join(args))
    print("# returncode:", result.returncode)
    print("# stdout:")
    print(result.stdout)
    print("# stderr:")
    print(result.stderr)

    return result.returncode, result.stdout, result.stderr

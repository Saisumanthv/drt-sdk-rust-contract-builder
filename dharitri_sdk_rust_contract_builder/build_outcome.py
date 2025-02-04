
import json
from pathlib import Path
from typing import Any, Dict, Protocol

from dharitri_sdk_rust_contract_builder.cargo_toml import \
    get_contract_name_and_version
from dharitri_sdk_rust_contract_builder.filesystem import (
    find_file_in_folder, find_files_in_folder)


class IWithToDict(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...


class BuildOutcome:
    def __init__(self, build_metadata: IWithToDict, build_options: IWithToDict):
        self.contracts: Dict[str, BuildOutcomeEntry] = dict()
        self.build_metadata = build_metadata
        self.build_options = build_options

    def gather_artifacts(self, build_folder: Path, output_subfolder: Path):
        entries = BuildOutcomeEntry.many_from_folders(build_folder, output_subfolder)
        self.contracts.update(entries)

    def get_entry(self, contract_name: str) -> 'BuildOutcomeEntry':
        return self.contracts[contract_name]

    def save_to_file(self, file: Path):
        data = self.to_dict()

        with open(file, "w") as f:
            json.dump(data, f, indent=4)

    def to_dict(self) -> Dict[str, Any]:
        contracts: Dict[str, Any] = {}

        for key, value in self.contracts.items():
            contracts[key] = value.to_dict()

        return {
            "buildMetadata": self.build_metadata.to_dict(),
            "buildOptions": self.build_options.to_dict(),
            "contracts": contracts
        }


class BuildOutcomeEntry:
    def __init__(self) -> None:
        self.version = ""
        self.codehash = ""
        self.bytecode_path = BuildArtifact(Path(""))
        self.abi_path = BuildArtifact(Path(""))
        self.src_package_path = BuildArtifact(Path(""))

    @classmethod
    def many_from_folders(cls, build_folder: Path, output_folder: Path) -> Dict[str, 'BuildOutcomeEntry']:
        # Note: sub-contracts of multi-contracts share the same version.
        _, version = get_contract_name_and_version(build_folder)

        # We consider all *.wasm files in the output folder to be standalone contracts or sub-contracts of multi-contracts.
        wasm_files = find_files_in_folder(output_folder, "*.wasm")

        result: Dict[str, BuildOutcomeEntry] = {}

        for wasm_file in wasm_files:
            contract_name = wasm_file.stem
            entry = BuildOutcomeEntry()
            entry.version = version
            entry.codehash = find_file_in_folder(output_folder, f"{contract_name}.codehash.txt").read_text()
            entry.bytecode_path = BuildArtifact.find_in_output(f"{contract_name}.wasm", output_folder)
            entry.abi_path = BuildArtifact.find_in_output(f"{contract_name}.abi.json", output_folder)
            entry.src_package_path = BuildArtifact.find_in_output("*.source.json", output_folder)

            result[contract_name] = entry

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "codehash": self.codehash,
            "artifacts": {
                "bytecode": self.bytecode_path.path.name,
                "abi": self.abi_path.path.name,
                "srcPackage": self.src_package_path.path.name,
            }
        }


class BuildArtifact:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def find_in_output(cls, name_pattern: str, output_folder: Path) -> 'BuildArtifact':
        path = find_file_in_folder(output_folder, name_pattern)
        return BuildArtifact(path)

    def read(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()

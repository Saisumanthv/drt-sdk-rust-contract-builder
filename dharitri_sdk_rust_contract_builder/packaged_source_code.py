
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence

from dharitri_sdk_rust_contract_builder.errors import ErrKnown

SCHEMA_VERSION_V1 = "1.0.0"
SCHEMA_VERSION_V2 = "2.0.0"


class ISourceCodeFile(Protocol):
    path: Path
    module: Optional[Path]
    dependency_depth: int
    is_test_file: bool


class PackagedSourceMetadata:
    def __init__(
        self,
        contract_name: str,
        contract_version: str,
        build_metadata: Dict[str, Any],
        build_options: Dict[str, Any]
    ):
        self.contract_name = contract_name
        self.contract_version = contract_version
        self.build_metadata = build_metadata
        self.build_options = build_options

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contractName": self.contract_name,
            "contractVersion": self.contract_version,
            "buildMetadata": self.build_metadata,
            "buildOptions": self.build_options,
        }

    @classmethod
    def from_dict_v1(cls, data: Dict[str, Any]) -> 'PackagedSourceMetadata':
        return PackagedSourceMetadata(
            contract_name=data.get("name", "untitled"),
            contract_version=data.get("version", "0.0.0"),
            build_metadata={},
            build_options={}
        )

    @classmethod
    def from_dict_v2(cls, data: Dict[str, Any]) -> 'PackagedSourceMetadata':
        return PackagedSourceMetadata(
            contract_name=data.get("contractName", "untitled"),
            contract_version=data.get("contractVersion", "0.0.0"),
            build_metadata=data.get("buildMetadata", {}),
            build_options=data.get("buildOptions", {}),
        )


class PackagedSourceCode:
    def __init__(
            self,
            version: str,
            metadata: PackagedSourceMetadata,
            entries: Sequence['PackagedSourceCodeEntry'],
    ) -> None:
        self.version = version
        self.metadata = metadata
        self.entries = entries

    @classmethod
    def from_file(cls, path: Path) -> 'PackagedSourceCode':
        with open(path, "r") as f:
            data: Dict[str, Any] = json.load(f)

        return PackagedSourceCode.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackagedSourceCode':
        schema_version = data.get("schemaVersion", SCHEMA_VERSION_V1)
        if schema_version == SCHEMA_VERSION_V1:
            metadata_raw = data
            metadata = PackagedSourceMetadata.from_dict_v1(metadata_raw)
        elif schema_version == SCHEMA_VERSION_V2:
            metadata_raw = data.get("metadata", {})
            metadata = PackagedSourceMetadata.from_dict_v2(metadata_raw)
        else:
            raise ErrKnown(f"Unknown schema version: {schema_version}")

        entries_raw: List[Dict[str, Any]] = data.get("entries", [])
        entries = [PackagedSourceCodeEntry.from_dict(entry) for entry in entries_raw]
        _sort_entries(entries)

        return PackagedSourceCode(schema_version, metadata, entries)

    @classmethod
    def from_filesystem(
        cls,
        metadata: PackagedSourceMetadata,
        project_folder: Path,
        source_code_files: Sequence[ISourceCodeFile]
    ) -> 'PackagedSourceCode':
        entries: List[PackagedSourceCodeEntry] = []

        for file in source_code_files:
            entry = PackagedSourceCodeEntry.from_source_code_file(project_folder, file)
            entries.append(entry)

        _sort_entries(entries)
        return PackagedSourceCode(SCHEMA_VERSION_V2, metadata, entries)

    def unwrap_to_filesystem(self, project_folder: Path):
        for entry in self.entries:
            full_path = project_folder / entry.path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(entry.content)

    def save_to_file(self, path: Path):
        data = self.to_dict()

        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def to_dict(self) -> Dict[str, Any]:
        entries = [entry.to_dict() for entry in self.entries]

        return {
            "schemaVersion": self.version,
            "metadata": self.metadata.to_dict(),
            "entries": entries
        }


class PackagedSourceCodeEntry:
    def __init__(self,
                 path: Path,
                 content: bytes,
                 module: Optional[Path],
                 dependency_depth: int,
                 is_test_file: bool
                 ) -> None:
        self.path = path
        self.content = content
        self.module = module
        self.dependency_depth = dependency_depth
        self.is_test_file = is_test_file

    @classmethod
    def from_dict(cls, dict: Dict[str, Any]) -> 'PackagedSourceCodeEntry':
        path = Path(dict.get("path", ""))
        content = base64.b64decode(dict.get("content", ""))
        module = Path(dict.get("module", ""))
        dependency_depth = dict.get("dependencyDepth", sys.maxsize)
        is_test_file = dict.get("isTestFile", False)

        return PackagedSourceCodeEntry(path, content, module, dependency_depth, is_test_file)

    @classmethod
    def from_source_code_file(cls, project_folder: Path, source_code_file: ISourceCodeFile) -> 'PackagedSourceCodeEntry':
        path = source_code_file.path.relative_to(project_folder)
        content = Path(source_code_file.path).read_bytes()
        module = source_code_file.module.relative_to(project_folder) if source_code_file.module else None
        dependency_depth = source_code_file.dependency_depth
        is_test_file = source_code_file.is_test_file

        return PackagedSourceCodeEntry(path, content, module, dependency_depth, is_test_file)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "path": str(self.path),
            "content": base64.b64encode(self.content).decode(),
            "module": str(self.module),
            "dependencyDepth": self.dependency_depth,
            "isTestFile": self.is_test_file
        }

        return data


def _sort_entries(entries: List[PackagedSourceCodeEntry]):
    entries.sort(key=lambda entry: (entry.dependency_depth, entry.path))

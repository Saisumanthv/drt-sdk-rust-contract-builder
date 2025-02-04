import os
from typing import Dict


class BuildMetadata:
    def __init__(
        self,
        builder_name: str,
        version_rust: str,
        version_binaryen: str,
        version_sc_meta: str,
        target_platform: str,
    ):
        self.builder_name = builder_name
        self.version_rust = version_rust
        self.version_binaryen = version_binaryen
        self.version_sc_meta = version_sc_meta
        self.target_platform = target_platform

    @classmethod
    def from_env(cls) -> 'BuildMetadata':
        return BuildMetadata(
            builder_name=os.environ["BUILD_METADATA_BUILDER_NAME"],
            version_rust=os.environ["BUILD_METADATA_VERSION_RUST"],
            version_binaryen=os.environ["BUILD_METADATA_VERSION_BINARYEN"],
            version_sc_meta=os.environ["BUILD_METADATA_VERSION_SC_META"],
            target_platform=os.environ["BUILD_METADATA_TARGETPLATFORM"],
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "builderName": self.builder_name,
            "versionRust": self.version_rust,
            "versionBinaryen": self.version_binaryen,
            "versionScTool": self.version_sc_meta,
            "targetPlatform": self.target_platform,
        }

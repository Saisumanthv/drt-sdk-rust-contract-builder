
from pathlib import Path
from typing import Any, Dict


class BuildOptions:
    def __init__(
        self,
        specific_contract: str,
        cargo_target_dir: Path,
        no_wasm_opt: bool,
        build_root_folder: Path,
    ) -> None:
        self.specific_contract = specific_contract
        self.cargo_target_dir = cargo_target_dir
        self.no_wasm_opt = no_wasm_opt
        self.build_root_folder = build_root_folder

    def to_dict(self) -> Dict[str, Any]:
        return {
            # "packageWholeProjectSrc" is kept due to compatibility reasons.
            "packageWholeProjectSrc": True,
            "specificContract": self.specific_contract,
            "cargoTargetDir": str(self.cargo_target_dir),
            "noWasmOpt": self.no_wasm_opt,
            "buildRootFolder": str(self.build_root_folder),
        }

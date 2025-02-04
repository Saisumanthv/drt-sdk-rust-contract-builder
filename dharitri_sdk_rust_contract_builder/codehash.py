
import logging
from hashlib import blake2b
from pathlib import Path


def generate_code_hash_artifact(wasm_file: Path):
    code_hash = compute_code_hash(wasm_file)
    with open(wasm_file.with_suffix(".codehash.txt"), "w") as f:
        f.write(code_hash)
    logging.info(f"Code hash of {wasm_file}: {code_hash}")


def compute_code_hash(wasm_file: Path):
    with open(wasm_file, "rb") as bytecode_file:
        code = bytecode_file.read()

    h = blake2b(digest_size=32)
    h.update(code)
    return h.hexdigest()

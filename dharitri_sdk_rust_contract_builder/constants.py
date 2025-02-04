from pathlib import Path

# The default value is the legacy one, to avoid breaking reproducibility of previous builds.
DEFAULT_BUILD_ROOT = "/tmp/project"
HARDCODED_UNWRAP_FOLDER = Path("/tmp/unwrapped")
ONE_KB_IN_BYTES: int = 1024
MAX_PACKAGED_SOURCE_CODE_SIZE: int = 2 * ONE_KB_IN_BYTES * 1024

CONTRACT_CONFIG_FILENAME = "dharitri.json"
SC_META_LOCAL_DEPS_FILENAME = "local_deps.txt"

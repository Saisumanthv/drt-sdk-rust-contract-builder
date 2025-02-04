FROM ubuntu:22.04

# Constants
ARG BUILDER_NAME="dharitri/sdk-rust-contract-builder:v0.0.1"
ARG VERSION_RUST="1.78.0"
ARG VERSION_BINARYEN="version_112"
ARG DOWNLOAD_URL_BINARYEN="https://github.com/WebAssembly/binaryen/releases/download/${VERSION_BINARYEN}/binaryen-${VERSION_BINARYEN}-x86_64-linux.tar.gz"
ARG VERSION_SC_META="1.0.3"
ARG TARGETPLATFORM

# Install system dependencies
RUN apt-get update --fix-missing && apt-get install -y \
    wget \
    build-essential \
    git \
    python3.11 python-is-python3 python3-pip \
    pkg-config \
    libssl-dev

# Install binaryen
RUN wget -O binaryen.tar.gz ${DOWNLOAD_URL_BINARYEN} && \
    tar -xf binaryen.tar.gz && \
    mkdir -p /binaryen && \
    cp binaryen-${VERSION_BINARYEN}/bin/wasm-opt /binaryen && \
    rm -rf binaryen.tar.gz binaryen-${VERSION_BINARYEN} && \
    chmod -R 777 /binaryen

# Install Python dependencies
RUN pip3 install toml==0.10.2 semver==3.0.0-dev.4

# Install rust
RUN wget -O rustup.sh https://sh.rustup.rs && \
    chmod +x rustup.sh && \
    CARGO_HOME=/rust RUSTUP_HOME=/rust ./rustup.sh --verbose --default-toolchain ${VERSION_RUST} --profile minimal --target wasm32-unknown-unknown -y && \
    rm rustup.sh && \
    chmod -R 777 /rust && \
    rm -rf /rust/registry

# Install sc-tool
RUN PATH="/rust/bin:${PATH}" CARGO_HOME=/rust RUSTUP_HOME=/rust cargo install dharitri-sc-meta --version ${VERSION_SC_META} --locked && \
    rm -rf /rust/registry

COPY "dharitri_sdk_rust_contract_builder" "/dharitri_sdk_rust_contract_builder"

ENV PATH="/rust/bin:/binaryen:${PATH}"
ENV CARGO_HOME="/rust"
ENV RUSTUP_HOME="/rust"
ENV PYTHONPATH=/
ENV BUILD_METADATA_BUILDER_NAME=${BUILDER_NAME}
ENV BUILD_METADATA_VERSION_RUST=${VERSION_RUST}
ENV BUILD_METADATA_VERSION_BINARYEN=${VERSION_BINARYEN}
ENV BUILD_METADATA_VERSION_SC_META=${VERSION_SC_META}
ENV BUILD_METADATA_TARGETPLATFORM=${TARGETPLATFORM}

# Additional arguments (must be provided at "docker run"):
# --project or --packaged-src
# --no-wasm-opt (optional)
# --build-root (optional)
ENTRYPOINT ["python", "/dharitri_sdk_rust_contract_builder/main.py", \
    "--output", "/output", \
    "--cargo-target-dir", "/rust/cargo-target-dir"]

LABEL frozen="yes"
LABEL rust=${VERSION_RUST}
LABEL wasm-opt-binaryen=${VERSION_BINARYEN}
LABEL sc_meta=${VERSION_SC_META}

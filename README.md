# drt-sdk-rust-contract-builder

Docker image (and wrappers) for reproducible contract builds (Rust). See [docs.dharitri.com](https://docs.dharitri.com/developers/reproducible-contract-builds/).

## Build the Docker image

```
docker build --network host . -t sdk-rust-contract-builder:next -f ./Dockerfile
```

Maintainers can publish the image as follows:

```
docker build --network host . -t dharitri/sdk-rust-contract-builder:next -f ./Dockerfile
docker push dharitri/sdk-rust-contract-builder:next
```

## Build contract using the wrapper

If you are using a Mac with ARM64, we _recommend_ setting the following variable beforehand (contract builds will be slower, but this eliminates the risk of not being able to reproduce the build on Linux):

```
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

Building from a project folder:

```
python3 ./build_with_docker.py --image=sdk-rust-contract-builder:next \
    --project=~/contracts/example \
    --output=~/contracts/output-from-docker
```

Building from a packaged source code:

```
python3 ./build_with_docker.py --image=sdk-rust-contract-builder:next \
    --packaged-src=~/contracts/example-0.0.0.source.json \
    --output=~/contracts/output-from-docker
```

## Run unit tests

```
pytest .
```

## Run integration tests (with Docker)

```
python3 ./integration_tests/test_previous_builds_are_reproducible.py --selected-builds "a.1" [...]
python3 ./integration_tests/test_project_folder_and_packaged_src_are_equivalent.py
```

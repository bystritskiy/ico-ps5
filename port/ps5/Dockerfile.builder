FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends clang-18 lld-18 llvm-18 cmake ninja-build build-essential python3 zlib1g-dev pkg-config git ca-certificates && apt-get clean

# scmd-bench grader: Lean v4.31.0, mathlib fabf563a (sources + prebuilt oleans), REPL 0cc6026.
#
#   docker build -t scmd-bench:1.0 -f docker/Dockerfile .
#   docker run --rm --network none -v $PWD:/work scmd-bench:1.0 \
#       grade --items /work/data/v1/dev.jsonl --submission /work/sub.jsonl --track anon --k 64 \
#             --out /work/graded.jsonl
#
# The image needs the network to BUILD (elan, mathlib's olean cache, the REPL) and not to RUN:
# grading is meant to happen under `--network none`.
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git python3 python3-pip && rm -rf /var/lib/apt/lists/*

ENV ELAN_HOME=/opt/elan PATH=/opt/elan/bin:$PATH
RUN curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
        | sh -s -- -y --no-modify-path --default-toolchain leanprover/lean4:v4.31.0

# mathlib at the pin, with its prebuilt oleans from mathlib's own cache (no local build).
COPY docker/library /opt/lean/library
WORKDIR /opt/lean/library
RUN lake update && lake exe cache get \
 && test "$(git -C .lake/packages/mathlib rev-parse HEAD)" = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"

# The REPL at the pinned commit.
RUN git clone https://github.com/leanprover-community/repl /opt/lean/repl \
 && git -C /opt/lean/repl checkout 0cc60263319308000bbaa5354427f775fe3dc7d0 \
 && cd /opt/lean/repl && lake build

COPY pyproject.toml README.md /opt/scmd-bench/
COPY scmd_bench /opt/scmd-bench/scmd_bench
RUN pip install --break-system-packages --no-deps /opt/scmd-bench

ENV SCMD_BENCH_LIBRARY=/opt/lean/library SCMD_BENCH_REPL_DIR=/opt/lean/repl \
    SCMD_BENCH_TOOLCHAIN_BIN=/opt/elan/bin
WORKDIR /work
ENTRYPOINT ["scmd-bench"]

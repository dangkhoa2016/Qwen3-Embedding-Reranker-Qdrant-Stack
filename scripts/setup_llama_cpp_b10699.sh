#!/usr/bin/env bash
set -Eeuo pipefail
set +x
umask 077

TAG="${LLAMA_CPP_TAG:-b10699}"
if [[ "$TAG" != "b10699" ]]; then
  echo "This evidence script is pinned to b10699; got LLAMA_CPP_TAG=$TAG" >&2
  exit 2
fi

ASSET="llama-b10699-bin-ubuntu-x64.tar.gz"
EXPECTED_SHA="a18d4ac6e1f81788e53726060fd892e16dec5744973ca4bad40532fce4ea30dd"
URL="https://github.com/ggml-org/llama.cpp/releases/download/${TAG}/${ASSET}"
DEST_ROOT="${LLAMA_CPP_DEST_ROOT:-/kaggle/working/llama.cpp-b10699}"
CACHE="${LLAMA_CPP_DOWNLOAD_CACHE:-/kaggle/working/${ASSET}}"
EVIDENCE_DIR="${LLAMA_CPP_EVIDENCE_DIR:-/kaggle/working/llama-cpp-b10699-evidence}"
mkdir -p "$DEST_ROOT" "$EVIDENCE_DIR"

if [[ -n "${LLAMA_SERVER_BIN:-}" ]]; then
  test -x "$LLAMA_SERVER_BIN"
  printf '%s\n' "$LLAMA_SERVER_BIN" > "$EVIDENCE_DIR/llama-server.path.txt"
  "$LLAMA_SERVER_BIN" --version 2>&1 | tee "$EVIDENCE_DIR/llama-server.version.txt"
  "$LLAMA_SERVER_BIN" --help 2>&1 | tee "$EVIDENCE_DIR/llama-server.help.txt" >/dev/null
  grep -Eq -- '--rerank|--reranking' "$EVIDENCE_DIR/llama-server.help.txt"
  grep -Fq -- '--cache-ram' "$EVIDENCE_DIR/llama-server.help.txt"
  echo "LLAMA_CPP_SETUP=PASS_EXISTING_BINARY"
  exit 0
fi

if [[ ! -f "$CACHE" ]] || [[ "$(sha256sum "$CACHE" | awk '{print $1}')" != "$EXPECTED_SHA" ]]; then
  rm -f "$CACHE"
  curl -fL --retry 3 --connect-timeout 20 --max-time 900 -o "$CACHE" "$URL"
fi

echo "$EXPECTED_SHA  $CACHE" | sha256sum -c - | tee "$EVIDENCE_DIR/asset.sha256.verify.txt"
rm -rf "$DEST_ROOT"/*
tar -xzf "$CACHE" -C "$DEST_ROOT"

LLAMA_SERVER_BIN_FOUND="$(find "$DEST_ROOT" -type f -name 'llama-server' -perm -u+x -print | head -n1)"
test -n "$LLAMA_SERVER_BIN_FOUND"
test -x "$LLAMA_SERVER_BIN_FOUND"

set +e
"$LLAMA_SERVER_BIN_FOUND" --version > "$EVIDENCE_DIR/llama-server.version.txt" 2>&1
VERSION_RC=$?
set -e

if [[ "$VERSION_RC" -ne 0 ]]; then
  echo "Prebuilt llama-server failed to execute; building pinned b10699 from source." | tee "$EVIDENCE_DIR/prebuilt-fallback.txt"
  SRC="${LLAMA_CPP_SOURCE_ROOT:-/kaggle/working/llama.cpp-src-b10699}"
  rm -rf "$SRC"
  git clone --depth 1 --branch b10699 https://github.com/ggml-org/llama.cpp.git "$SRC"
  cmake -S "$SRC" -B "$SRC/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_NATIVE=OFF \
    -DGGML_CUDA=OFF \
    -DGGML_VULKAN=OFF
  cmake --build "$SRC/build" --config Release -j2 --target llama-server
  LLAMA_SERVER_BIN_FOUND="$SRC/build/bin/llama-server"
  test -x "$LLAMA_SERVER_BIN_FOUND"
  "$LLAMA_SERVER_BIN_FOUND" --version > "$EVIDENCE_DIR/llama-server.version.txt" 2>&1
fi

"$LLAMA_SERVER_BIN_FOUND" --help > "$EVIDENCE_DIR/llama-server.help.txt" 2>&1
grep -Eq -- '--rerank|--reranking' "$EVIDENCE_DIR/llama-server.help.txt"
grep -Fq -- '--pooling' "$EVIDENCE_DIR/llama-server.help.txt"
grep -Fq -- '--cache-ram' "$EVIDENCE_DIR/llama-server.help.txt"

printf '%s\n' "$LLAMA_SERVER_BIN_FOUND" | tee "$EVIDENCE_DIR/llama-server.path.txt"
sha256sum "$LLAMA_SERVER_BIN_FOUND" | tee "$EVIDENCE_DIR/llama-server.sha256.txt"

echo "LLAMA_CPP_TAG=$TAG"
echo "LLAMA_SERVER_BIN=$LLAMA_SERVER_BIN_FOUND"
echo "LLAMA_CPP_SETUP=PASS"

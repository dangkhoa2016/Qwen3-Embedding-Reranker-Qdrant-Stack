#!/usr/bin/env bash
set -Eeuo pipefail
set +x
umask 077

QDRANT_VERSION=1.18.3
QDRANT_ARCHIVE='qdrant-x86_64-unknown-linux-musl.tar.gz'
QDRANT_ARCHIVE_SHA256='b4faedcdf8c9577bf1c8f2ab9b454636b87e056c116c99d49bd4f9fb2e634285'
QDRANT_URL="https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/${QDRANT_ARCHIVE}"
DEST_ROOT="${QDRANT_DEMO_ROOT:-/kaggle/working/qdrant-${QDRANT_VERSION}}"
BIN_DIR="$DEST_ROOT/bin"
CACHE="${QDRANT_DOWNLOAD_CACHE:-/kaggle/working/${QDRANT_ARCHIVE}}"
QDRANT_BIN="${QDRANT_BIN:-$BIN_DIR/qdrant}"
mkdir -p "$BIN_DIR"

verify_qdrant_bin() {
  local candidate="$1" output version
  [[ -f "$candidate" && -x "$candidate" ]] || return 1
  output="$(timeout 10 "$candidate" --version 2>&1)" || return 1
  version="$(printf '%s\n' "$output" | sed -nE 's/.*[Qq]drant[[:space:]]+v?([0-9]+\.[0-9]+\.[0-9]+).*/\1/p' | head -n1)"
  [[ "$version" == "$QDRANT_VERSION" ]] || return 1
  printf 'QDRANT_BIN_VERIFIED=%s version=%s\n' "$candidate" "$version"
}

if [[ -n "${QDRANT_BIN_EXPLICIT:-}" ]]; then
  QDRANT_BIN="$QDRANT_BIN_EXPLICIT"
  verify_qdrant_bin "$QDRANT_BIN" || { echo "ERROR: explicit QDRANT_BIN is not Qdrant ${QDRANT_VERSION}" >&2; exit 2; }
elif verify_qdrant_bin "$QDRANT_BIN" >/dev/null 2>&1; then
  :
elif command -v qdrant >/dev/null 2>&1 && verify_qdrant_bin "$(command -v qdrant)" >/dev/null 2>&1; then
  install -m 0755 "$(command -v qdrant)" "$QDRANT_BIN"
else
  if [[ ! -f "$CACHE" ]] || [[ "$(sha256sum "$CACHE" | awk '{print $1}')" != "$QDRANT_ARCHIVE_SHA256" ]]; then
    rm -f "$CACHE"
    curl -fL --retry 3 --connect-timeout 15 --max-time 900 -o "$CACHE" "$QDRANT_URL"
  fi
  printf '%s  %s\n' "$QDRANT_ARCHIVE_SHA256" "$CACHE" | sha256sum -c -
  TMP_DIR="$(mktemp -d "$DEST_ROOT/.extract.XXXXXX")"
  trap 'rm -rf "$TMP_DIR"' EXIT
  tar -xzf "$CACHE" -C "$TMP_DIR" qdrant
  install -m 0755 "$TMP_DIR/qdrant" "$QDRANT_BIN"
fi

verify_qdrant_bin "$QDRANT_BIN"
printf 'QDRANT_BIN=%s\n' "$QDRANT_BIN"

#!/bin/sh
# Decrypt the beta-raven-bench answer key into a directory outside this repository.
#
# Usage: ./scripts/decrypt_answers.sh <output-dir>
#
# The passphrase is never stored in this repository and is never echoed, written
# to disk, or passed as a command-line argument. Do not run this on a machine that
# is also running the benchmark: cleartext ground truth must not be reachable from
# any agent-visible path.

set -eu

CIPHER_ALGO="aes-256-cbc"
KDF_DIGEST="sha256"
KDF_ITERATIONS=600000

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(dirname -- "$script_dir")
bundle="$repo_root/answers/polymarket-march-2026-labels.tar.gz.enc"
checksums="$repo_root/answers/SHA256SUMS"

fail() {
    echo "error: $1" >&2
    exit 1
}

[ $# -eq 1 ] || fail "usage: $0 <output-dir>"
[ -f "$bundle" ] || fail "encrypted bundle not found: $bundle"
command -v openssl >/dev/null 2>&1 || fail "openssl is required"
command -v tar >/dev/null 2>&1 || fail "tar is required"

mkdir -p -- "$1"
out_dir=$(CDPATH= cd -- "$1" && pwd)
case "$out_dir/" in
    "$repo_root"/*) fail "refusing to decrypt into the repository; choose a path outside $repo_root" ;;
esac

if command -v shasum >/dev/null 2>&1; then
    (cd "$repo_root/answers" && shasum -a 256 -c SHA256SUMS) >/dev/null \
        || fail "ciphertext does not match $checksums"
elif command -v sha256sum >/dev/null 2>&1; then
    (cd "$repo_root/answers" && sha256sum -c SHA256SUMS) >/dev/null \
        || fail "ciphertext does not match $checksums"
else
    echo "warning: no sha256 tool found; skipping ciphertext integrity check" >&2
fi

printf 'Passphrase (not echoed): ' >&2
stty_state=$(stty -g 2>/dev/null || true)
if [ -n "$stty_state" ]; then stty -echo; fi
read -r RAVEN_ANSWER_KEY || true
if [ -n "$stty_state" ]; then stty "$stty_state"; fi
printf '\n' >&2
export RAVEN_ANSWER_KEY
[ -n "${RAVEN_ANSWER_KEY:-}" ] || fail "empty passphrase"

if ! openssl enc -d -"$CIPHER_ALGO" -md "$KDF_DIGEST" -pbkdf2 -iter "$KDF_ITERATIONS" \
        -in "$bundle" -pass env:RAVEN_ANSWER_KEY 2>/dev/null | tar -xzf - -C "$out_dir"; then
    unset RAVEN_ANSWER_KEY
    fail "decryption failed; wrong passphrase or corrupted bundle"
fi
unset RAVEN_ANSWER_KEY

extracted="$out_dir/polymarket-march-2026-labels"
if command -v shasum >/dev/null 2>&1; then
    (cd "$extracted" && shasum -a 256 -c SHA256SUMS) >/dev/null || fail "cleartext checksum mismatch"
elif command -v sha256sum >/dev/null 2>&1; then
    (cd "$extracted" && sha256sum -c SHA256SUMS) >/dev/null || fail "cleartext checksum mismatch"
fi

echo "Answer key written to $extracted"
echo "This is ground truth. Keep it off every agent-visible path and delete it when scoring is done."

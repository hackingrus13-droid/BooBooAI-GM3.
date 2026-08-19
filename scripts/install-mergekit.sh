#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MERGEKIT_DIR="$ROOT/vendor/mergekit"
MERGEKIT_REPO="https://github.com/arcee-ai/mergekit.git"
MERGEKIT_REV="a6e402884ba9bc30da7f23e8304a35f19485de95"
ENV_DIR="$ROOT/state/mergekit-venv"

fail(){ printf '[FAIL] %s\n' "$*" >&2; exit 1; }
pass(){ printf '[PASS] %s\n' "$*"; }
info(){ printf '[INFO] %s\n' "$*"; }

cd "$ROOT"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' \
  || fail 'MergeKit requires Python >= 3.10.'
command -v git >/dev/null 2>&1 || fail 'git is required.'
command -v python3 >/dev/null 2>&1 || fail 'python3 is required.'

if [ -e "$MERGEKIT_DIR/.git" ]; then
    info 'Existing MergeKit checkout detected.'
else
    [ ! -e "$MERGEKIT_DIR" ] || fail "Refusing to overwrite existing path: $MERGEKIT_DIR"
    mkdir -p "$(dirname "$MERGEKIT_DIR")"
    git clone "$MERGEKIT_REPO" "$MERGEKIT_DIR"
fi

cd "$MERGEKIT_DIR"
git fetch --tags --prune origin
git cat-file -e "$MERGEKIT_REV^{commit}" \
  || fail "Pinned MergeKit revision is unavailable: $MERGEKIT_REV"
git checkout --detach "$MERGEKIT_REV"

printf '%s\n' "$(git rev-parse HEAD)" > "$ROOT/state/mergekit-revision.txt"
pass "MergeKit source pinned: $(git rev-parse HEAD)"

cd "$ROOT"
if [ "$(uname -s)" = "Linux" ] && [ -n "${TERMUX_VERSION:-}" ]; then
    info 'Termux detected. Source integration is verified, but MergeKit dependencies include PyTorch and are not installed automatically on Android.'
    info 'Use a supported Linux/desktop Python environment for actual model merging.'
    exit 0
fi

python3 -m venv "$ENV_DIR"
"$ENV_DIR/bin/python" -m pip install --upgrade pip
"$ENV_DIR/bin/python" -m pip install -e "$MERGEKIT_DIR"
"$ENV_DIR/bin/python" -m mergekit.scripts.run_yaml --help >/dev/null
pass 'MergeKit Python environment installed and CLI import verified.'
printf '%s\n' "To run MergeKit: $ENV_DIR/bin/mergekit-yaml --help"

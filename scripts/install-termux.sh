#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

REPO='https://github.com/hackingrus13-droid/BooBooAI-GM3..git'
BRANCH='main'
TARGET="${BOOBOOAI_ROOT:-$HOME/BooBooAI-GM3.}"

fail(){ printf '[FAIL] %s\n' "$*" >&2; exit 1; }
pass(){ printf '[PASS] %s\n' "$*"; }
info(){ printf '[INFO] %s\n' "$*"; }

command -v pkg >/dev/null 2>&1 || fail 'Termux pkg command not found.'
printf '%s\n' '============================================================'
printf '%s\n' ' BOOBOOAI-GM3 — TERMUX INSTALL / VERIFY'
printf '%s\n' ' FACTS ONLY / SAFE RECOVERY / NO DESTRUCTIVE RESET'
printf '%s\n' '============================================================'

info 'Updating Termux package indexes.'
pkg update -y
info 'Upgrading installed Termux packages before dependency installation.'
pkg upgrade -y
info 'Installing required packages.'
pkg install -y git python curl openssl openssh termux-services

for c in git python3 curl ssh sshd; do
    command -v "$c" >/dev/null 2>&1 || fail "Required command missing after installation: $c"
done
pass 'required Termux commands detected'

if [ -d "$TARGET/.git" ]; then
    cd "$TARGET"
    pass "existing Git checkout detected: $TARGET"
else
    [ ! -e "$TARGET" ] || fail "Target exists but is not a Git checkout: $TARGET"
    info "Cloning verified GitHub repository into $TARGET"
    git clone --branch "$BRANCH" --single-branch "$REPO" "$TARGET"
    cd "$TARGET"
    pass 'repository cloned from GitHub main'
fi

ORIGIN="$(git remote get-url origin 2>/dev/null || true)"
[ "$ORIGIN" = "$REPO" ] || fail "origin mismatch: $ORIGIN"
CURRENT_BRANCH="$(git branch --show-current)"
[ "$CURRENT_BRANCH" = "$BRANCH" ] || fail "checkout is on '$CURRENT_BRANCH', not '$BRANCH'"

if [ -n "$(git status --porcelain)" ]; then
    printf '\n%s\n' '=== SAFE DIRTY-WORKTREE RECOVERY ==='
    RECOVERY="$HOME/.boobooai-recovery/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$RECOVERY/untracked-top" "$RECOVERY/untracked-paths"
    git status --porcelain=v1 >"$RECOVERY/status.txt"
    git diff --binary >"$RECOVERY/tracked.patch"
    git diff --stat >"$RECOVERY/tracked.stat"
    pass "dirty state recorded: $RECOVERY"

    while IFS= read -r -d '' path; do
        top="${path%%/*}"
        [ -e "$path" ] || continue
        [ "$top" = '.git' ] && continue
        if [ -z "$(git ls-files -- "$top")" ]; then
            if [ ! -e "$RECOVERY/untracked-top/$top" ]; then
                mv -- "$top" "$RECOVERY/untracked-top/"
                info "preserved untracked tree: $top"
            fi
        else
            dest="$RECOVERY/untracked-paths/$path"
            mkdir -p "$(dirname "$dest")"
            if [ ! -e "$dest" ]; then
                mv -- "$path" "$dest"
                info "preserved untracked path: $path"
            fi
        fi
    done < <(git ls-files --others --exclude-standard -z)

    git fetch --prune origin "$BRANCH"
    LOCAL="$(git rev-parse HEAD)"
    REMOTE="$(git rev-parse "origin/$BRANCH")"
    if [ "$LOCAL" != "$REMOTE" ]; then
        git merge --ff-only "origin/$BRANCH" || fail "local checkout cannot fast-forward safely after preservation; backup remains at $RECOVERY"
    fi

    if [ -s "$RECOVERY/tracked.patch" ]; then
        git apply --check "$RECOVERY/tracked.patch" || fail "preserved tracked change cannot be safely reapplied; backup remains at $RECOVERY"
        git apply "$RECOVERY/tracked.patch" || fail "preserved tracked change could not be safely reapplied; backup remains at $RECOVERY"
    fi

    while IFS= read -r -d '' src; do
        name="${src##*/}"
        if [ -e "$TARGET/$name" ]; then
            git ls-files --error-unmatch -- "$name" >/dev/null 2>&1 && fail "upstream now tracks preserved tree: $name; backup remains at $RECOVERY"
            fail "destination already exists for preserved tree: $name; backup remains at $RECOVERY"
        fi
        mv -- "$src" "$TARGET/"
        info "restored preserved untracked tree: $name"
    done < <(find "$RECOVERY/untracked-top" -mindepth 1 -maxdepth 1 -print0)

    if [ -d "$RECOVERY/untracked-paths" ]; then
        while IFS= read -r -d '' src; do
            rel="${src#"$RECOVERY/untracked-paths/"}"
            dest="$TARGET/$rel"
            if [ -e "$dest" ]; then
                git ls-files --error-unmatch -- "$rel" >/dev/null 2>&1 && fail "upstream now tracks preserved path: $rel; backup remains at $RECOVERY"
                fail "destination already exists for preserved path: $rel; backup remains at $RECOVERY"
            fi
            mkdir -p "$(dirname "$dest")"
            mv -- "$src" "$dest"
            info "restored preserved untracked path: $rel"
        done < <(find "$RECOVERY/untracked-paths" -type f -print0)
    fi

    pass 'local state preserved and source synchronized without destructive reset'
fi

git fetch --prune origin "$BRANCH"
LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse "origin/$BRANCH")"
[ "$LOCAL" = "$REMOTE" ] || git merge --ff-only "origin/$BRANCH" || fail 'local checkout cannot fast-forward safely to origin/main.'
pass "source synchronized with origin/$BRANCH"

for f in server.py index.html config/config.example.json config/governed_rules.json scripts/wake_up.py scripts/launch-final-termux.sh; do
    [ -f "$f" ] || fail "required project file missing: $f"
done

bash -n scripts/install-termux.sh || fail 'Termux installer syntax validation failed.'
bash -n scripts/launch-final-termux.sh || fail 'Termux launcher syntax validation failed.'
pass 'Termux shell scripts syntax verified without changing tracked file modes'

python3 -m compileall -q server.py booboo scripts tests
pass 'Python compilation'
python3 -m unittest discover -s tests -v
pass 'complete test suite'

DIAG_DIR="$TARGET/state"
mkdir -p "$DIAG_DIR"
python3 -m booboo.diagnostics >"$DIAG_DIR/termux-diagnostics.json"
pass "safe diagnostics: $DIAG_DIR/termux-diagnostics.json"

if [ -f scripts/final_verify.py ]; then
    python3 scripts/final_verify.py
    pass 'project final verifier'
fi

printf '\n%s\n' '=== OPENSSH VERIFICATION ==='
ssh -V 2>&1 | head -n 1
sshd -t || fail 'sshd configuration validation failed.'
pass 'OpenSSH/sshd configuration verified'

printf '\n%s\n' '=== OPTIONAL SSH SERVICE ==='
printf '%s\n' 'OpenSSH is installed. This script does not expose the phone to the network automatically.'
printf '%s\n' 'To start the Termux sshd service after verification, run: sshd'
printf '%s\n' 'To inspect listening sockets, run: ss -ltn'

printf '\n%s\n' '============================================================'
printf '%s\n' ' BOOBOOAI-GM3 — TERMUX SOURCE INSTALL VERIFIED'
printf '%s\n' '============================================================'
printf 'ROOT:   %s\n' "$TARGET"
printf 'BRANCH: %s\n' "$(git branch --show-current)"
printf 'COMMIT: %s\n' "$(git rev-parse HEAD)"
printf '%s\n' 'SOURCE: VERIFIED'
printf '%s\n' 'PYTHON: VERIFIED'
printf '%s\n' 'TESTS:  VERIFIED'
printf '%s\n' 'DIAGNOSTICS: VERIFIED'
printf '%s\n' 'OPENSSH: VERIFIED'
printf '%s\n' '============================================================\n'

if [ "${1:-}" = '--start' ]; then
    exec ./scripts/launch-final-termux.sh
fi
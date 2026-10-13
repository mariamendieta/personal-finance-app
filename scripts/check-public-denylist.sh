#!/usr/bin/env bash
# Public-repo check: this repo is PUBLIC, so block commits that add household
# terms (names, employers, merchants, card numbers) listed in a PRIVATE denylist.
#
# The denylist is NOT stored here (that would publish it). It is a plain text
# file, one term per line (# comments allowed), read from the first of:
#   $PUBLIC_DENYLIST, $PRODUCTION_DATA_DIR/public-repo-denylist.txt,
#   ../woffieta-data/, ~/build/woffieta-data/, ~/woffieta-data/
# Terms match case-insensitively as whole words.
#
# Usage:
#   check-public-denylist.sh            staged added lines (pre-commit hook)
#   check-public-denylist.sh --msg F    a commit message file (commit-msg hook)
#   check-public-denylist.sh --range R  added lines + messages in a commit range (CI)
#   check-public-denylist.sh --history  every commit's added lines + messages
#   check-public-denylist.sh --tree     the current files
# Add --quiet to report only where a hit is (never the matched text), for CI
# logs, which are public.
set -u

mode="staged"; arg=""; quiet=0
while [ $# -gt 0 ]; do
  case "$1" in
    --msg|--range) mode="${1#--}"; arg="${2:-}"; shift ;;
    --history|--tree) mode="${1#--}" ;;
    --quiet) quiet=1 ;;
  esac
  shift
done

# Find the private denylist; if it isn't on this machine, warn and allow the
# commit so contributors without the data repo aren't blocked.
repo_root="$(git rev-parse --show-toplevel)"
list=""
for c in "${PUBLIC_DENYLIST:-}" "${PRODUCTION_DATA_DIR:-}/public-repo-denylist.txt" \
         "$repo_root/../woffieta-data/public-repo-denylist.txt" \
         "$HOME/build/woffieta-data/public-repo-denylist.txt" \
         "$HOME/woffieta-data/public-repo-denylist.txt"; do
  if [ -n "$c" ] && [ -f "$c" ]; then list="$c"; break; fi
done
if [ -z "$list" ]; then
  echo "public-repo check: denylist not found; skipping (see CLAUDE.md)." >&2
  exit 0
fi

# Strip comments and blank lines into a temporary pattern file.
patterns="$(mktemp)"; trap 'rm -f "$patterns"' EXIT
grep -v -E '^\s*(#|$)' "$list" > "$patterns"
[ -s "$patterns" ] || exit 0

# Produce the text to scan for the chosen mode.
scan() {
  case "$mode" in
    staged)  git diff --cached -U0 --no-color | grep -E '^\+' | grep -v -E '^\+\+\+ ' ;;
    msg)     grep -v -E '^#' "$arg" ;;
    # Messages are indented 4 spaces so their "- " bullets aren't mistaken for
    # removed lines; then keep added lines and message lines only.
    range)   git log -p -U0 --no-color --format='commit %h%n%w(0,4,4)%B' "$arg" | grep -v -E '^(-|\+\+\+ |@@|diff |index )' ;;
    history) git log --all -p -U0 --no-color --format='commit %h%n%w(0,4,4)%B' | grep -v -E '^(-|\+\+\+ |@@|diff |index )' ;;
  esac
}

if [ "$mode" = tree ]; then
  # Match file contents only (not the file:line prefix), report file:line.
  hits="$(git grep -I -n -i -w -F -f "$patterns" -- . )"
else
  hits="$(scan | grep -n -i -w -F -f "$patterns")"
fi
if [ -z "$hits" ]; then exit 0; fi

count="$(printf '%s\n' "$hits" | wc -l | tr -d ' ')"
echo "public-repo check: $count line(s) contain a private household term. This repo is PUBLIC." >&2
if [ "$quiet" = 1 ]; then
  # Only the line numbers within the scanned text: no matched content.
  printf '%s\n' "$hits" | cut -d: -f1 | head -50 | sed 's/^/  scanned line /' >&2
else
  printf '%s\n' "$hits" | cut -c1-200 | head -50 | sed 's/^/  /' >&2
  echo "Move household-specific rules to the private woffieta-data repo." >&2
fi
exit 1

#!/usr/bin/env bash
# Preflight — run before every commit. Installed as a git pre-commit hook by
# `make hooks`, and runnable by hand with `make check`.
#
# This exists because of a real incident: a sibling project baked a live
# OpenAI key into a Dockerfile, and it sat in that repository's history for
# fourteen months. A .gitignore would not have caught it — the file was meant
# to be committed, the key just should not have been in it. So this scans
# CONTENT, not filenames, and it scans what is actually staged.
set -uo pipefail
fail=0
say() { printf '  %s\n' "$*"; }

staged=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$staged" ] && { echo "preflight: nothing staged"; exit 0; }

echo "preflight: $(echo "$staged" | wc -l) staged file(s)"

# 1. Count. A sudden flood usually means a venv or a data directory slipped in.
n=$(echo "$staged" | wc -l)
if [ "$n" -gt 200 ]; then
  say "REFUSED: $n staged files — that is a lot. Check .gitignore before continuing."
  fail=1
fi

# 2. Secret shapes, in staged content.
patterns='sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----'
if hits=$(git diff --cached -U0 | grep -nE "^\+.*($patterns)" 2>/dev/null); then
  say "REFUSED: possible credential in staged content:"
  echo "$hits" | sed -E "s/($patterns)/<REDACTED>/g" | sed 's/^/    /' | head -10
  fail=1
fi

# 3. Assigned-looking secrets that are not obvious placeholders.
if hits=$(git diff --cached -U0 \
          | grep -nE '^\+.*(API_KEY|_TOKEN|_SECRET|PASSWORD)[[:space:]]*=[[:space:]]*[^[:space:]]' \
          | grep -viE 'REPLACE_ME|YOUR_|<.*>|xxx+|example|placeholder|\$\{|os\.getenv|getenv\(|process\.env|=[[:space:]]*(""|'"''"'|$)' 2>/dev/null); then
  say "REFUSED: assigned secret that is not a placeholder:"
  # Redact the VALUE, not just an unquoted token — a scanner that prints the
  # secret it found defeats its own purpose the moment you paste the output.
  echo "$hits" | sed -E 's/(=[[:space:]]*)("[^"]*"|'"'"'[^'"'"']*'"'"'|[^[:space:]]+)/\1<REDACTED>/' \
               | sed 's/^/    /' | head -10
  fail=1
fi

# 4. Files that should never be staged, whatever .gitignore says.
if bad=$(echo "$staged" | grep -E '(^|/)\.env$|\.sqlite3|/chroma/|node_modules/|\.pem$|\.key$'); then
  say "REFUSED: these should not be committed:"
  echo "$bad" | sed 's/^/    /'
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "preflight: clean"
else
  echo
  echo "  Nothing was committed. Fix the above, or override with --no-verify"
  echo "  if you are certain (you usually are not)."
fi
exit "$fail"

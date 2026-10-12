#!/usr/bin/env bash
# Create a new lab attempt under attempts/.
#
# Every run creates the next numbered folder (attempt-01, attempt-02, ...).
# Existing attempts are never changed or deleted, so running this again is
# the way to start over while keeping earlier work for review.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/lab/evidence"
attempts_dir="$repo_root/attempts"

mkdir -p "$attempts_dir"

n=1
while [ -e "$attempts_dir/$(printf 'attempt-%02d' "$n")" ]; do
    n=$((n + 1))
done
name="$(printf 'attempt-%02d' "$n")"
attempt="$attempts_dir/$name"

mkdir "$attempt" "$attempt/evidence" "$attempt/work"

# Original evidence: read-only copies. Students read these but never edit them.
cp "$source_dir"/*.txt "$source_dir"/*.log "$source_dir"/*.conf "$attempt/evidence/"
chmod 444 "$attempt"/evidence/*
chmod 555 "$attempt/evidence"

# Working copies: the only files students are expected to change.
cp "$source_dir/handover-draft.txt" "$attempt/work/handover.txt"
cp "$source_dir/web-02-live.conf" "$attempt/work/web-02.conf"
chmod 644 "$attempt"/work/*

printf 'created=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" > "$attempt/.attempt"

echo "Created $name"
echo
echo "  evidence/   original files (read-only)"
echo "  work/       your working copies and results"
echo
if [ "$n" -gt 1 ]; then
    echo "Earlier attempts are unchanged in $attempts_dir."
    echo
fi
echo "Move into your lab root with:"
echo
echo "  cd $attempt"

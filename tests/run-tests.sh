#!/usr/bin/env bash
# Automated tests for lab/start.sh and lab/check.py.
#
# Works on a temporary copy of the repository, so it never touches real
# attempts. Usage, from the repository root:
#
#     bash tests/run-tests.sh
set -uo pipefail

PYTHON="${PYTHON:-python3}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'chmod -R u+w "$tmp" 2>/dev/null; rm -rf "$tmp"' EXIT

cp -R "$repo_root/lab" "$repo_root/reviewer" "$tmp/"
export LC_COLLATE=C

passes=0
failures=0
ok()   { passes=$((passes + 1)); echo "ok    $1"; }
fail() { failures=$((failures + 1)); echo "FAIL  $1"; }

tree_hash() {
    (cd "$1" && find . -type f | sort | while read -r f; do
        printf '%s %s\n' "$f" "$(sha256sum "$f" | cut -d " " -f 1)"
    done) | sha256sum | cut -d " " -f 1
}

check() {   # check ATTEMPT [PART...]  -> sets $out and $status
    out="$(cd "$1" && "$PYTHON" "$tmp/lab/check.py" "${@:2}" 2>&1)"
    status=$?
}

# 1. start.sh creates an attempt with read-only evidence and working copies
bash "$tmp/lab/start.sh" > /dev/null
a1="$tmp/attempts/attempt-01"
[ -f "$a1/work/handover.txt" ] && [ -f "$a1/work/web-02.conf" ] \
    && ok "start.sh creates working copies" || fail "start.sh creates working copies"
if [ "$(id -u)" -ne 0 ] && ( echo x >> "$a1/evidence/runbook.txt" ) 2>/dev/null; then
    fail "evidence is read-only"
else
    ok "evidence is read-only"
fi
diff -q "$a1/evidence/web-02-live.conf" "$a1/work/web-02.conf" > /dev/null \
    && ok "work/web-02.conf starts identical to the live file" \
    || fail "work/web-02.conf starts identical to the live file"

# 2. A fresh attempt fails, but its evidence passes
check "$a1"
[ "$status" -eq 1 ] && ok "fresh attempt fails the checker" || fail "fresh attempt fails the checker"
grep -q "^PASS  Evidence" <<< "$out" && ok "fresh evidence passes" || fail "fresh evidence passes"

# 3. The reference solution passes every check
bash "$tmp/reviewer/solution.sh" "$a1"
check "$a1"
if [ "$status" -eq 0 ] && ! grep -q "^FAIL" <<< "$out"; then
    ok "reference solution passes ($(grep -o '[0-9]* of [0-9]* checks passed' <<< "$out"))"
else
    fail "reference solution passes"; echo "$out"
fi

# 4. The checker does not change any file
before="$(tree_hash "$a1")"
check "$a1"; check "$a1" 3; check "$a1" final
[ "$before" = "$(tree_hash "$a1")" ] && ok "checker leaves files unchanged" \
    || fail "checker leaves files unchanged"

# 5. A second start.sh creates attempt-02 and leaves attempt-01 alone
bash "$tmp/lab/start.sh" > /dev/null
[ -d "$tmp/attempts/attempt-02" ] && [ "$before" = "$(tree_hash "$a1")" ] \
    && ok "new attempt preserves earlier work" || fail "new attempt preserves earlier work"

# 6. The checker finds the attempt from a subfolder, and refuses elsewhere
out="$(cd "$a1/work" && "$PYTHON" "$tmp/lab/check.py" 3 2>&1)"; status=$?
[ "$status" -eq 0 ] && ok "checker runs from work/" || fail "checker runs from work/"
out="$(cd "$tmp" && "$PYTHON" "$tmp/lab/check.py" 2>&1)"; status=$?
[ "$status" -eq 2 ] && ok "checker refuses outside an attempt" || fail "checker refuses outside an attempt"
check "$a1" 3
if grep -q "Exp 3" <<< "$out" && ! grep -q "Exp 5" <<< "$out"; then
    ok "single-part mode"
else
    fail "single-part mode"
fi

# 7. Hints: every experiment has two levels, bad input is refused, and no hint
#    gives away a value the student must find.
hint_ok=yes
for part in 1 2 3 4 5 6 7 final; do
    for level in 1 2; do
        text="$("$PYTHON" "$tmp/lab/hint.py" "$part" "$level" 2>&1)" || hint_ok=no
        for answer in "Tomas Reyes" "01:14:07" "10093" "37" "31" "S24" "pool_size" "40 to 4"; do
            grep -qF "$answer" <<< "$text" && { hint_ok=no; echo "  hint $part $level reveals $answer"; }
        done
    done
done
[ "$hint_ok" = yes ] && ok "hints exist for every part and reveal no answers" \
    || fail "hints exist for every part and reveal no answers"
"$PYTHON" "$tmp/lab/hint.py" 9 > /dev/null 2>&1; s1=$?
"$PYTHON" "$tmp/lab/hint.py" 3 5 > /dev/null 2>&1; s2=$?
[ "$s1" -eq 2 ] && [ "$s2" -eq 2 ] && ok "hint refuses an unknown part or level" \
    || fail "hint refuses an unknown part or level"
check "$tmp/attempts/attempt-02"
grep -qF "python3 ../../lab/hint.py 2" <<< "$out" && ok "checker points to the hint for the first failing part" \
    || fail "checker points to the hint for the first failing part"

# 8. Each common mistake is detected with a specific message.
#    mutate NAME PART EXPECTED_TEXT COMMANDS
mutate() {
    local name="$1" part="$2" expected="$3" commands="$4"
    local m="$tmp/attempts/mutant"
    chmod -R u+w "$m" 2>/dev/null; rm -rf "$m"
    cp -R "$a1" "$m"
    chmod 555 "$m/evidence"
    (cd "$m" && eval "$commands") 2>/dev/null
    check "$m" "$part"
    if [ "$status" -eq 1 ] && grep "^FAIL" <<< "$out" | grep -qF "$expected"; then
        ok "detects: $name"
    else
        fail "detects: $name"; echo "$out" | grep -E "^(PASS|FAIL)"
    fi
}

mutate "missing file" 3 "is missing" \
    'rm work/statuses.txt'
mutate "sorted cut output" 3 "different order" \
    'cut -d "|" -f 3 evidence/requests.log | sort > work/statuses.txt'
mutate "wrong cut field" 3 "does not contain field" \
    'cut -d "|" -f 2 evidence/requests.log > work/statuses.txt'
mutate "text sort instead of numeric" 4 "Add -n" \
    'cut -d "|" -f 4,5 evidence/requests.log | sort -r > work/latency-ranked.txt'
mutate "missing -r" 4 "Add -r" \
    'cut -d "|" -f 4,5 evidence/requests.log | sort -n > work/latency-ranked.txt'
mutate "output redirected onto its own input" 4 "is empty" \
    'sort -n -r work/latency-ranked.txt > work/latency-ranked.txt'
mutate "uniq without sort" 5 "still has repeated lines" \
    'cut -d "|" -f 2,3 evidence/alerts.log | uniq > work/alert-types.txt'
mutate "uniq -c without sort" 5 "more than once" \
    'cut -d "|" -f 2,3 evidence/alerts.log | uniq -c > work/alert-counts.txt'
mutate "counts not ranked" 6 "highest count is not first" \
    'grep -F "|503" work/time-server-status.txt | cut -d "|" -f 2 | sort | uniq -c > work/errors-by-server.txt'
mutate "504 counted with 503" 6 "wrong counts" \
    'grep -F "|50" work/time-server-status.txt | cut -d "|" -f 2 | sort | uniq -c | sort -n -r > work/errors-by-server.txt'
mutate "diff inputs reversed" 7 "wrong order" \
    'diff evidence/web-02-approved.conf evidence/web-02-live.conf > work/config-changes.diff'
mutate "diff of identical files saved" 7 "is empty" \
    'diff evidence/web-02-live.conf evidence/web-02-live.conf > work/config-changes.diff'
mutate "config not repaired" 7 "has not been changed yet" \
    'cp evidence/web-02-live.conf work/web-02.conf'
mutate "config partly repaired" 7 "still differs" \
    'grep -v debug.sql_trace evidence/web-02-live.conf > work/web-02.conf'
mutate "students not deduplicated" final "more than once" \
    'grep -F "|503|" evidence/requests.log | grep -F "|/api/enrol|" | cut -d "|" -f 6 | sort > work/students-to-contact.txt'
mutate "students from other endpoints" final "had no 503 response on /api/enrol" \
    'grep -F "|503|" evidence/requests.log | cut -d "|" -f 6 | sort | uniq > work/students-to-contact.txt'
mutate "students with 504 only" final "had no 503 response on /api/enrol" \
    'grep -F "|/api/enrol|" evidence/requests.log | grep -F "|50" | cut -d "|" -f 6 | sort | uniq > work/students-to-contact.txt'
mutate "archived escalation contact" final "archived 2025 rota" \
    'sed -i "s/^Escalation: .*/Escalation: Ravi Menon/" work/handover.txt'
mutate "cause values reversed" final "approved value comes first" \
    'sed -i "s/^Cause: .*/Cause: db.pool_size changed from 4 to 40/" work/handover.txt'
mutate "wrong first 503 time" final "earliest 503" \
    'sed -i "s/^First 503: .*/First 503: 01:40:00/" work/handover.txt'
mutate "rev 3 lines left in handover" final "exactly 10 lines" \
    'echo "Notes: none" >> work/handover.txt'
mutate "config reconciled claimed but not done" final "still differs" \
    'cp evidence/web-02-live.conf work/web-02.conf'
mutate "evidence edited" 3 "has been changed" \
    'chmod u+w evidence evidence/alerts.log && echo extra >> evidence/alerts.log'

echo
echo "$passes passed, $failures failed"
[ "$failures" -eq 0 ]

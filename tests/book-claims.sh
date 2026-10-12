#!/usr/bin/env bash
# Run the lab book's commands in order and check every output the book quotes
# (error messages, first lines, counts, diff markers, checker messages).
#
# Works on a temporary copy of the repository with a temporary HOME, so it
# never touches real attempts or your ~/.bashrc. From the repository root:
#
#     bash tests/book-claims.sh
set -u
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
R="$(mktemp -d)"
trap 'chmod -R u+w "$R" 2>/dev/null; rm -rf "$R"' EXIT
cp -R "$repo_root/lab" "$repo_root/tests" "$repo_root/reviewer" "$R/"
export HOME="$R/home"
mkdir "$HOME"
cd "$R"
pass=0; fail=0
ok()  { if eval "$2"; then pass=$((pass+1)); echo "ok    $1"; else fail=$((fail+1)); echo "FAIL  $1"; fi; }

setup_out="$(bash lab/setup/postcreate.sh 2>&1)"
ok "setup prints self-test and 'Setup complete'" '[[ "$setup_out" == *"Lab self-test: 34 passed, 0 failed."* && "$setup_out" == *"Setup complete"* ]]'
start1="$(bash lab/start.sh)"
ok "start.sh last line is the cd command (attempt-01)" '[[ "$(tail -n 1 <<< "$start1")" == "  cd $R/attempts/attempt-01" ]]'
start2="$(bash lab/start.sh)"
ok "second start.sh prints a cd to attempt-02 as last line" '[[ "$(tail -n 1 <<< "$start2")" == "  cd $R/attempts/attempt-02" ]]'
cd "$R/attempts/attempt-01"
export LC_COLLATE=C

ok "runbook is 285 lines" '[[ $(grep -c "" evidence/runbook.txt) -eq 285 ]]'
ok "runbook last line END OF RUNBOOK" '[[ "$(tail -n 1 evidence/runbook.txt)" == "END OF RUNBOOK" ]]'
ok "two headings contain NOTE FORMAT; first is Section 9" '[[ $(grep -c "NOTE FORMAT" evidence/runbook.txt) -eq 2 && "$(grep -m1 "NOTE FORMAT" evidence/runbook.txt)" == "SECTION 9:"* ]]'
ok "no 'Rota' match (case-sensitive example)" '! grep -q "Rota" evidence/runbook.txt'
ok "draft line 2 Owner: Sam Okafor, line 3 Ravi Menon" '[[ "$(sed -n 2p work/handover.txt)" == "Owner: Sam Okafor" && "$(sed -n 3p work/handover.txt)" == "Escalation: Ravi Menon" ]]'
ok "example log line 01:02:27|web-02|200|29|/health|- exists" 'grep -qxF "01:02:27|web-02|200|29|/health|-" evidence/requests.log'

err="$(bash -c 'cut -d | -f 3 evidence/requests.log' 2>&1)"
ok "3A unquoted: -f: command not found + cut option error" '[[ "$err" == *"-f: command not found"* && "$err" == *"option requires an argument"* ]]'
cut -d "|" -f 3 evidence/requests.log > work/statuses.txt
cut -d "|" -f 1,2,3 evidence/requests.log > work/time-server-status.txt
ok "3B first two lines as quoted" '[[ "$(head -2 work/time-server-status.txt | tr "\n" " ")" == "01:00:00|web-03|200 01:01:04|web-01|200 " ]]'
ok "first 503 is 01:14:07" '[[ "$(grep -F "|503" work/time-server-status.txt | head -1)" == "01:14:07|web-02|503" ]]'
ok "-f 5,4 prints field 4 first" '[[ "$(cut -d "|" -f 5,4 evidence/requests.log | head -1)" == "423|/api/enrol" ]]'
ok "cut -f 3 without -d prints whole lines" '[[ "$(cut -f 3 evidence/requests.log | head -1)" == "$(head -1 evidence/requests.log)" ]]'
ok "cut without -f error text" '[[ "$(cut -d "|" evidence/requests.log 2>&1 | head -1)" == "cut: you must specify a list of bytes, characters, or fields" ]]'

ok "text sort: first line is not the smallest; 10093 near top" '[[ "$(cut -d "|" -f 4 evidence/requests.log | sort | head -1)" == "10012" && $(cut -d "|" -f 4 evidence/requests.log | sort | grep -n "^10093$" | cut -d: -f1) -le 5 ]]'
ok "numeric sort: 10093 last" '[[ "$(cut -d "|" -f 4 evidence/requests.log | sort -n | tail -1)" == "10093" ]]'
ok "sort -r text puts 953 first, above 10093" '[[ "$(cut -d "|" -f 4 evidence/requests.log | sort -r | head -1)" == "953" ]]'
cut -d "|" -f 4,5 evidence/requests.log | sort -n -r > work/latency-ranked.txt
ok "slowest 10093|/api/enrol" '[[ "$(head -1 work/latency-ranked.txt)" == "10093|/api/enrol" ]]'
cp work/statuses.txt work/scratch.txt; sort work/scratch.txt > work/scratch.txt
ok "4C scratch is empty" '[[ ! -s work/scratch.txt ]]'
rm work/scratch.txt
perr="$(bash -c 'sort evidence/alerts.log > evidence/alerts.log' 2>&1)"
ok "4C evidence redirect: Permission denied" '[[ "$perr" == *"Permission denied"* ]]'

ok "alerts: 14 lines" '[[ $(cut -d "|" -f 2,3 evidence/alerts.log | grep -c "") -eq 14 ]]'
ok "uniq leaves 10 lines" '[[ $(cut -d "|" -f 2,3 evidence/alerts.log | uniq | grep -c "") -eq 10 ]]'
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq > work/alert-types.txt
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq -c > work/alert-counts.txt
ok "uniq -c line '      6 HighErrorRate|web-02'" 'grep -qxF "      6 HighErrorRate|web-02" work/alert-counts.txt'
ok "without sort HighErrorRate|web-02 split in 3 groups" '[[ $(cut -d "|" -f 2,3 evidence/alerts.log | uniq -c | grep -c "HighErrorRate|web-02") -eq 3 ]]'
sort work/statuses.txt | uniq -c > work/status-counts.txt
ok "503 count is 37" 'grep -qx " *37 503" work/status-counts.txt'

grep -F "|503" work/time-server-status.txt | cut -d "|" -f 2 | sort | uniq -c | sort -n -r > work/errors-by-server.txt
ok "faulty server web-02 first" '[[ "$(head -1 work/errors-by-server.txt | tr -s " ")" == " 31 web-02" ]]'

ok "7A identical: no output" '[[ -z "$(diff evidence/web-02-live.conf work/web-02.conf)" ]]'
d="$(diff evidence/web-02-live.conf evidence/web-02-approved.conf)"
ok "7B markers 7c7 9d8 10a10" '[[ "$(grep -E "^[0-9]" <<< "$d" | tr "\n" " ")" == "7c7 9d8 10a10 " ]]'
ok "7B swapped: 7c7 8a9 10d10" '[[ "$(diff evidence/web-02-approved.conf evidence/web-02-live.conf | grep -E "^[0-9]" | tr "\n" " ")" == "7c7 8a9 10d10 " ]]'
ok "live line 10 is cache.enabled = true" '[[ "$(sed -n 10p evidence/web-02-live.conf)" == "cache.enabled = true" ]]'
ok "diff typo message" '[[ "$(diff work/web02.conf evidence/web-02-approved.conf 2>&1)" == "diff: work/web02.conf: No such file or directory" ]]'
diff evidence/web-02-live.conf evidence/web-02-approved.conf > work/config-changes.diff

ok "runbook rev 4 has 10 template lines" '[[ $(sed -n "/NOTE FORMAT (REV 4/,/^SECTION 15/p" evidence/runbook.txt | grep -cE "^  [A-Z0-9][^ ]*.*: ") -eq 10 ]]'
fail_msg="$(cut -d "|" -f 2,3 evidence/alerts.log | uniq > work/alert-types.txt; python3 ../../lab/check.py 5)"
ok "validation: deliberate mistake FAIL text" '[[ "$fail_msg" == *"still has repeated lines. uniq removes only adjacent repeats; sort first, then uniq."* ]]'
cut -d "|" -f 2,3 evidence/alerts.log | sort | uniq > work/alert-types.txt
out="$(cd .. && python3 ../lab/check.py 2>&1)"
ok "checker outside attempt: message as in error table" '[[ "$out" == "Run this checker from inside your lab attempt"* ]]'

bash "$R/reviewer/solution.sh" . >/dev/null
final="$(python3 ../../lab/check.py)"
ok "reference solution: 14 of 14 checks passed" '[[ "$final" == *"14 of 14 checks passed."* ]]'
echo; echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
